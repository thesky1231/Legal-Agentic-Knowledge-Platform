from __future__ import annotations

import re
import time
from collections.abc import Iterable
from collections.abc import Iterator

from agentic_knowledge_platform.core.resilience import CircuitBreaker, RetryPolicy, SlidingWindowRateLimiter
from agentic_knowledge_platform.services.openai_compatible import ModelClient
from agentic_knowledge_platform.text import normalize_text, sentence_split, tokenize
from agentic_knowledge_platform.types import ModelRequest, ModelResponse


class TemplateModelClient:
    def __init__(
        self,
        name: str,
        supported_tasks: Iterable[str],
        persona: str,
        fail_tasks: set[str] | None = None,
    ) -> None:
        self.name = name
        self.supported_tasks = set(supported_tasks)
        self.persona = persona
        self.fail_tasks = fail_tasks or set()

    def generate(self, request: ModelRequest) -> str:
        if request.task in self.fail_tasks:
            raise RuntimeError(f"{self.name} simulated failure on task {request.task}")
        if request.task == "summary":
            return self._summarize(request.context_blocks)
        if request.task == "qa":
            return self._answer(request.prompt, request.context_blocks)
        if request.task == "speech_script":
            return self._speech_script(request.context_blocks or [request.prompt])
        raise ValueError(f"unsupported task: {request.task}")

    def _summarize(self, context_blocks: list[str]) -> str:
        sentences = self._pick_relevant_sentences("", context_blocks, limit=3)
        body = "；".join(sentences) if sentences else "暂无可总结内容。"
        return f"{self.persona}总结：{body}"

    def _answer(self, prompt: str, context_blocks: list[str]) -> str:
        sentences = self._pick_relevant_sentences(prompt, context_blocks, limit=3)
        if not sentences:
            return "当前没有足够依据回答这个问题。"
        body = "；".join(sentences)
        return f"{self.persona}基于检索证据的回答：{body}"

    def _speech_script(self, context_blocks: list[str]) -> str:
        base = "；".join(self._pick_relevant_sentences("", context_blocks, limit=3))
        if not base:
            base = normalize_text(context_blocks[0]) if context_blocks else "暂无讲解内容。"
        return f"大家好，今天重点讲三件事：{base}。最后要记住，回答必须可追溯、可审计、可扩展。"

    def _pick_relevant_sentences(self, prompt: str, context_blocks: list[str], limit: int) -> list[str]:
        query_tokens = set(tokenize(prompt))
        scored: list[tuple[int, str]] = []
        for block in context_blocks:
            for sentence in sentence_split(block):
                if not sentence:
                    continue
                cleaned = self._clean_sentence(sentence)
                if len(cleaned) < 8:
                    continue
                sentence_tokens = set(tokenize(cleaned))
                overlap = len(query_tokens & sentence_tokens) if query_tokens else 1
                if overlap or not query_tokens:
                    scored.append((overlap, cleaned))
        scored.sort(key=lambda item: (item[0], len(item[1])), reverse=True)
        selected: list[str] = []
        seen: set[str] = set()
        for _, sentence in scored:
            compact = normalize_text(sentence)
            if compact in seen:
                continue
            selected.append(compact)
            seen.add(compact)
            if len(selected) >= limit:
                break
        return selected

    def _clean_sentence(self, sentence: str) -> str:
        without_labels = re.sub(r"\[[^\]]+\]\s*", "", sentence)
        without_code = without_labels.replace("`", "")
        without_formula_markers = without_code.replace("$$", " ")
        without_table_pipes = without_formula_markers.replace("|", " ")
        return normalize_text(without_table_pipes)


class ModelRouter:
    def __init__(
        self,
        clients: list[ModelClient],
        task_routes: dict[str, list[str]],
        rate_limiter: SlidingWindowRateLimiter,
        failure_threshold: int = 2,
        recovery_timeout: int = 15,
        retry_policy: RetryPolicy | None = None,
    ) -> None:
        self.clients = {client.name: client for client in clients}
        self.task_routes = task_routes
        self.rate_limiter = rate_limiter
        self.retry_policy = retry_policy or RetryPolicy()
        self.breakers = {
            client.name: CircuitBreaker(
                failure_threshold=failure_threshold,
                recovery_timeout=float(recovery_timeout),
            )
            for client in clients
        }

    def generate(self, request: ModelRequest) -> ModelResponse:
        errors: list[str] = []
        routes = self.task_routes.get(request.task, list(self.clients))
        for client_name in routes:
            client = self.clients[client_name]
            if request.task not in client.supported_tasks:
                errors.append(f"{client_name} does not support {request.task}")
                continue
            breaker = self.breakers[client_name]
            if not breaker.allow_request():
                errors.append(f"{client_name} breaker open")
                continue
            if not self.rate_limiter.allow(f"{client_name}:{request.task}:{request.session_id}"):
                errors.append(f"{client_name} rate limited")
                continue
            started = time.perf_counter()
            try:
                output = self.retry_policy.call(lambda: client.generate(request), exceptions=(RuntimeError, ValueError))
            except Exception as exc:
                breaker.record_failure()
                errors.append(f"{client_name} failed: {exc}")
                continue
            latency_ms = int((time.perf_counter() - started) * 1000)
            breaker.record_success()
            return ModelResponse(
                model=client.name,
                route=client_name,
                output=output,
                latency_ms=latency_ms,
            )
        raise RuntimeError(f"no available model route for task {request.task}: {'; '.join(errors)}")

    def stream_generate(self, request: ModelRequest) -> tuple[str, str, Iterator[str]]:
        errors: list[str] = []
        routes = self.task_routes.get(request.task, list(self.clients))
        for client_name in routes:
            client = self.clients[client_name]
            if request.task not in client.supported_tasks:
                errors.append(f"{client_name} does not support {request.task}")
                continue
            breaker = self.breakers[client_name]
            if not breaker.allow_request():
                errors.append(f"{client_name} breaker open")
                continue
            if not self.rate_limiter.allow(f"{client_name}:{request.task}:{request.session_id}"):
                errors.append(f"{client_name} rate limited")
                continue

            def iterator() -> Iterator[str]:
                try:
                    stream_method = getattr(client, "stream_generate", None)
                    if callable(stream_method):
                        for chunk in stream_method(request):
                            yield chunk
                    else:
                        output = self.retry_policy.call(lambda: client.generate(request), exceptions=(RuntimeError, ValueError))
                        for chunk in self._chunk_output(output):
                            yield chunk
                except Exception:
                    breaker.record_failure()
                    raise
                else:
                    breaker.record_success()

            return client.name, client_name, iterator()
        raise RuntimeError(f"no available model route for task {request.task}: {'; '.join(errors)}")

    def breaker_state(self, client_name: str) -> dict[str, float | int | str]:
        return self.breakers[client_name].snapshot()

    def _chunk_output(self, output: str) -> Iterator[str]:
        normalized = normalize_text(output)
        if not normalized:
            return
        sentences = sentence_split(normalized)
        if sentences:
            for sentence in sentences:
                cleaned = normalize_text(sentence)
                if cleaned:
                    yield cleaned
            return
        chunk_size = 28
        for start in range(0, len(normalized), chunk_size):
            yield normalized[start : start + chunk_size]
