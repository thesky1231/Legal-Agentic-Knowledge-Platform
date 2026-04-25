from __future__ import annotations

from collections.abc import Iterator
from typing import Protocol

from agentic_knowledge_platform.services.http_json import JsonHttpClient
from agentic_knowledge_platform.text import normalize_text
from agentic_knowledge_platform.types import ModelRequest


class EmbeddingService(Protocol):
    dimensions: int

    def embed(self, text: str) -> list[float]:
        ...

    def batch_embed(self, texts: list[str]) -> list[list[float]]:
        ...


class ModelClient(Protocol):
    name: str
    supported_tasks: set[str]

    def generate(self, request: ModelRequest) -> str:
        ...

    def stream_generate(self, request: ModelRequest) -> Iterator[str]:
        ...


class OpenAICompatibleEmbeddingService:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: int = 1536,
        max_batch_size: int = 10,
        timeout_seconds: int = 20,
    ) -> None:
        self.dimensions = dimensions
        self.model = model
        self.max_batch_size = max(1, max_batch_size)
        self.http = JsonHttpClient(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            default_headers={"Authorization": f"Bearer {api_key}"},
        )

    def embed(self, text: str) -> list[float]:
        payload = {"model": self.model, "input": text}
        response = self.http.post("/v1/embeddings", payload)
        return self._extract_single_embedding(response)

    def batch_embed(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []

        embeddings: list[list[float]] = []
        for start in range(0, len(texts), self.max_batch_size):
            batch = texts[start : start + self.max_batch_size]
            payload = {"model": self.model, "input": batch}
            response = self.http.post("/v1/embeddings", payload)
            embeddings.extend(self._extract_embedding_list(response))
        return embeddings

    def _extract_single_embedding(self, response: dict[str, object]) -> list[float]:
        data = response.get("data", [])
        if not isinstance(data, list) or not data:
            raise RuntimeError("embedding response missing data")
        first = data[0]
        if not isinstance(first, dict) or not isinstance(first.get("embedding"), list):
            raise RuntimeError("embedding response missing vector")
        return [float(value) for value in first["embedding"]]

    def _extract_embedding_list(self, response: dict[str, object]) -> list[list[float]]:
        data = response.get("data", [])
        if not isinstance(data, list):
            raise RuntimeError("embedding response missing data list")

        embeddings: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise RuntimeError("embedding item missing vector")
            embeddings.append([float(value) for value in item["embedding"]])
        return embeddings


class OpenAICompatibleModelClient:
    def __init__(
        self,
        name: str,
        model: str,
        base_url: str,
        api_key: str,
        endpoint_mode: str,
        supported_tasks: set[str],
        timeout_seconds: int = 20,
    ) -> None:
        self.name = name
        self.model = model
        self.endpoint_mode = endpoint_mode
        self.supported_tasks = supported_tasks
        self.http = JsonHttpClient(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            default_headers={"Authorization": f"Bearer {api_key}"},
        )

    def generate(self, request: ModelRequest) -> str:
        instructions = self._instructions_for_task(request)
        prompt = self._build_prompt(request)
        if self.endpoint_mode == "chat_completions":
            response = self.http.post(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                },
            )
            return self._extract_chat_completion_text(response)

        response = self.http.post(
            "/v1/responses",
            {
                "model": self.model,
                "instructions": instructions,
                "input": prompt,
            },
        )
        return self._extract_responses_text(response)

    def stream_generate(self, request: ModelRequest) -> Iterator[str]:
        instructions = self._instructions_for_task(request)
        prompt = self._build_prompt(request)
        if self.endpoint_mode == "chat_completions":
            stream = self.http.stream(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.0,
                    "stream": True,
                },
            )
            return self._chat_stream_iterator(stream)

        stream = self.http.stream(
            "/v1/responses",
            {
                "model": self.model,
                "instructions": instructions,
                "input": prompt,
                "stream": True,
            },
        )
        return self._responses_stream_iterator(stream)

    def _build_prompt(self, request: ModelRequest) -> str:
        context_blocks = [normalize_text(block) for block in request.context_blocks if normalize_text(block)]
        context = "\n\n".join(
            f"[证据 {index}]\n{block}" for index, block in enumerate(context_blocks, start=1)
        )
        question_type = request.metadata.get("question_type", "direct_answer")
        citation_count = request.metadata.get("citation_count", str(len(request.context_blocks)))
        output_contract = self._output_contract_for_question_type(question_type)
        return (
            "Answer Composer v2\n"
            "答案撰写任务：把检索证据加工成可读、可解释、可追溯的法律知识回答。\n"
            f"Task: {request.task}\n"
            f"Question type: {question_type}\n"
            f"Citation count: {citation_count}\n"
            f"User question: {normalize_text(request.prompt)}\n\n"
            "证据来源：下面的证据块是唯一允许使用的依据。\n"
            f"Evidence:\n{context or '[no context]'}\n\n"
            "内部证据审查规则，只在内部执行，不要输出推理过程：\n"
            "1. 系统已经在调用模型前完成证据门控；当前任务默认是“证据可用，负责组织答案”。\n"
            "2. 仍需检查证据是否覆盖用户问题的核心法律概念、罪名边界、构成要件、法条或事实模式。\n"
            "3. 如果证据完全无关，只能输出一个机器标记：EVIDENCE_INSUFFICIENT。除此之外不要输出任何文字。\n"
            "4. 如果证据部分覆盖问题，应给出保守答案并说明适用边界，不要扩展到证据之外。\n"
            "5. 证据充分时，必须先给用户能直接理解的答案，再用证据支持，不能只复述或拼接法条原文。\n\n"
            "强制禁令：\n"
            "- do_not_dump_statutes: 禁止直接堆法条，必须解释法条与问题之间的关系。\n"
            "- do_not_mix_unrelated_crimes: 禁止把召回到的无关罪名、无关条文混进答案。\n"
            "- do_not_answer_from_weak_evidence: 禁止基于弱相关材料强行回答。\n"
            "- do_not_use_general_legal_knowledge: 禁止使用证据之外的通用法律知识补全结论。\n"
            "- do_not_expose_chain_of_thought: 禁止输出内部思考过程。\n\n"
            "输出要求：\n"
            "- 使用简体中文，只输出答案正文，不要输出 Markdown 标题，不要重复 Citations 列表。\n"
            "- 外层系统会展示“法条依据”和“提示”，你这里重点负责把结论说清楚。\n"
            "- 如果证据足够，第一句话必须直接回答用户问题，后面再解释理由和边界。\n"
            "- 不要输出“当前知识库没有检索到...”这类拒答句；证据完全无关时只输出 EVIDENCE_INSUFFICIENT。\n"
            "- 一般控制在 300 到 600 个中文字符；复杂问题可以稍长，但要避免长篇复制法条。\n\n"
            f"本题输出策略：\n{output_contract}"
        )

    def _instructions_for_task(self, request: ModelRequest) -> str:
        if request.task == "summary":
            return "你负责把法律或企业文档总结成简洁、可执行的中文说明。"
        if request.task == "qa":
            question_type = request.metadata.get("question_type", "direct_answer")
            if question_type == "confusing":
                return (
                    "你是保守的法律 RAG 答案撰写器。用户正在问概念边界或罪名区别。"
                    "必须先用自己的话讲清核心区别，再说明适用边界和引用依据。"
                    "不得直接堆法条，不得复制长篇条文，不得使用证据之外的通用法律知识。"
                    "证据完全无关时只输出 EVIDENCE_INSUFFICIENT。"
                )
            if question_type == "definition":
                return (
                    "你是保守的法律 RAG 答案撰写器。用户正在问法律概念定义。"
                    "只有证据直接定义或解释该概念时才能回答。"
                    "回答时先给定义，再列关键条件和边界。证据完全无关时只输出 EVIDENCE_INSUFFICIENT。"
                )
            if question_type == "complex_reasoning":
                return (
                    "你是保守的法律 RAG 答案撰写器。用户正在问复杂事实判断或法律推理。"
                    "不得越过证据作确定性结论。必须说明分析路径、关键事实缺口和适用边界。"
                    "如果缺少事实或直接法条，只能给保守结论；证据完全无关时只输出 EVIDENCE_INSUFFICIENT。"
                )
            if question_type == "should_refuse":
                return (
                    "你是保守的法律 RAG 答案撰写器。用户问题存在高风险、事实不足或不适合直接定性。"
                    "必须输出保守拒答，不得给确定性法律结论。"
                    "可以提示需要补充事实、证据或咨询专业人士。"
                )
            return (
                "你是保守的法律 RAG 答案撰写器。只有检索证据直接覆盖用户问题时才能回答。"
                "证据部分覆盖时给出保守边界，不得猜测；证据完全无关时只输出 EVIDENCE_INSUFFICIENT。"
                "回答要先给结论，再解释依据，避免长篇照搬法条。"
            )
        if request.task == "speech_script":
            return "你把技术回答改写成约一分钟的口播讲解稿。"
        return "你是严谨的后端 AI 平台助手。"

    def _output_contract_for_question_type(self, question_type: str) -> str:
        if question_type == "confusing":
            return (
                "- 第一句话必须回答“核心区别”，不得先罗列条文。\n"
                "- 后续按“行为方式、是否暴力或胁迫、保护法益、适用边界”解释。\n"
                "- 可以使用 2 到 4 个短点对比，但每一点都必须来自证据。\n"
                "- 对抢劫与抢夺这类问题，优先说明抢劫通常强调暴力、胁迫或其他压制反抗的方法，抢夺通常强调公然夺取财物；如果证据提到携带凶器、暴力胁迫升级等边界，也要点出。\n"
                "- 结尾说明边界：具体定性仍要结合行为方式、是否造成反抗被压制、财物取得过程和证据。"
            )
        if question_type == "definition":
            return (
                "- 第一句话给出概念定义。\n"
                "- 后续说明 2 到 4 个关键构成或适用条件。\n"
                "- 如果证据只出现概念名称但没有解释含义，只输出 EVIDENCE_INSUFFICIENT。"
            )
        if question_type == "complex_reasoning":
            return (
                "- 第一句话给保守结论，不要直接下确定性罪名或责任结论。\n"
                "- 后续说明分析路径：需要看哪些事实、哪些法条边界、证据中已经覆盖了什么。\n"
                "- 明确列出缺失事实或证据缺口，避免过度推断。"
            )
        if question_type == "should_refuse":
            return (
                "- 第一句话必须保守拒答，不给确定性法律结论。\n"
                "- 说明原因：事实不足、证据不足、问题风险较高或需要专业判断。\n"
                "- 可以建议补充事实、争议点、已有证据和适用法条后再问。"
            )
        return (
            "- 第一句话直接回答用户问题。\n"
            "- 后续用 2 到 4 个短点说明构成要件、适用条件或结论来源。\n"
            "- 不得改答相似但不同的问题；证据完全无关时只输出 EVIDENCE_INSUFFICIENT。"
        )

    def _extract_chat_completion_text(self, response: dict[str, object]) -> str:
        choices = response.get("choices", [])
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("chat completion response missing choices")
        first = choices[0]
        if not isinstance(first, dict):
            raise RuntimeError("chat completion choice malformed")
        message = first.get("message", {})
        if not isinstance(message, dict):
            raise RuntimeError("chat completion message missing")
        content = message.get("content", "")
        if not isinstance(content, str):
            raise RuntimeError("chat completion content missing")
        return normalize_text(content)

    def _extract_responses_text(self, response: dict[str, object]) -> str:
        output_text = response.get("output_text")
        if isinstance(output_text, str) and output_text.strip():
            return normalize_text(output_text)

        output = response.get("output", [])
        if not isinstance(output, list):
            raise RuntimeError("responses output missing")
        pieces: list[str] = []
        for item in output:
            if not isinstance(item, dict):
                continue
            content = item.get("content", [])
            if not isinstance(content, list):
                continue
            for part in content:
                if not isinstance(part, dict):
                    continue
                if part.get("type") in {"output_text", "text"}:
                    text = part.get("text", "")
                    if isinstance(text, str) and text.strip():
                        pieces.append(text)
                    elif isinstance(text, dict):
                        value = text.get("value", "")
                        if isinstance(value, str) and value.strip():
                            pieces.append(value)
        if not pieces:
            raise RuntimeError("responses output missing text")
        return normalize_text(" ".join(pieces))

    def _chat_stream_iterator(self, stream: Iterator[dict[str, object]]) -> Iterator[str]:
        for event in stream:
            choices = event.get("choices", [])
            if not isinstance(choices, list) or not choices:
                continue
            first = choices[0]
            if not isinstance(first, dict):
                continue
            delta = first.get("delta", {})
            if not isinstance(delta, dict):
                continue
            content = delta.get("content")
            if isinstance(content, str) and content:
                yield content

    def _responses_stream_iterator(self, stream: Iterator[dict[str, object]]) -> Iterator[str]:
        for event in stream:
            if event.get("type") == "response.output_text.delta":
                delta = event.get("delta", "")
                if isinstance(delta, str) and delta:
                    yield delta
