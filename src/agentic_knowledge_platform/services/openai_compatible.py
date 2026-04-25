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
        context = "\n\n".join(normalize_text(block) for block in request.context_blocks if normalize_text(block))
        question_type = request.metadata.get("question_type", "direct_answer")
        prompt = (
            f"Task: {request.task}\n"
            f"Question type: {question_type}\n"
            f"User question: {normalize_text(request.prompt)}\n"
            "Available evidence blocks are listed below. Use only this evidence.\n"
            f"Evidence:\n{context or '[no context]'}\n\n"
            "Output requirements:\n"
            "1. Answer in Simplified Chinese.\n"
            "2. Give the conclusion first.\n"
            "3. If this is a comparison question, summarize the key differences instead of copying statutes.\n"
            "4. Keep the answer concise and grounded; do not paste long raw article text.\n"
            "5. If the evidence is insufficient, say so explicitly instead of guessing."
        )
        if self.endpoint_mode == "chat_completions":
            response = self.http.post(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
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
        context = "\n\n".join(normalize_text(block) for block in request.context_blocks if normalize_text(block))
        question_type = request.metadata.get("question_type", "direct_answer")
        prompt = (
            f"Task: {request.task}\n"
            f"Question type: {question_type}\n"
            f"User question: {normalize_text(request.prompt)}\n"
            "Available evidence blocks are listed below. Use only this evidence.\n"
            f"Evidence:\n{context or '[no context]'}\n\n"
            "Output requirements:\n"
            "1. Answer in Simplified Chinese.\n"
            "2. Give the conclusion first.\n"
            "3. If this is a comparison question, summarize the key differences instead of copying statutes.\n"
            "4. Keep the answer concise and grounded; do not paste long raw article text.\n"
            "5. If the evidence is insufficient, say so explicitly instead of guessing."
        )
        if self.endpoint_mode == "chat_completions":
            stream = self.http.stream(
                "/v1/chat/completions",
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": instructions},
                        {"role": "user", "content": prompt},
                    ],
                    "temperature": 0.2,
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

    def _instructions_for_task(self, request: ModelRequest) -> str:
        if request.task == "summary":
            return "You summarize legal or enterprise documents into concise implementation notes in Chinese."
        if request.task == "qa":
            question_type = request.metadata.get("question_type", "direct_answer")
            if question_type == "confusing":
                return (
                    "You are a careful legal knowledge assistant. "
                    "The user is asking for a legal distinction or boundary. "
                    "Explain the difference in your own words based only on the supplied evidence. "
                    "Do not copy full statutes. Focus on action pattern, violence or coercion, protected legal interest, and applicable article boundary."
                )
            if question_type == "definition":
                return (
                    "You are a careful legal knowledge assistant. "
                    "Define the legal concept directly from the provided evidence and keep the answer short and clear."
                )
            if question_type == "complex_reasoning":
                return (
                    "You are a careful legal knowledge assistant. "
                    "Provide a conservative analysis from the supplied evidence only, and remind the user when more facts are needed."
                )
            return (
                "You are a careful legal knowledge assistant. "
                "Answer only from the provided evidence, keep the wording direct, and avoid quoting long statute passages verbatim."
            )
        if request.task == "speech_script":
            return "You turn technical answers into a spoken teaching script of about one minute."
        return "You are a careful backend AI platform assistant."

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
