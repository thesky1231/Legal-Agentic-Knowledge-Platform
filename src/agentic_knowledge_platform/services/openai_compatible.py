from __future__ import annotations

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


class OpenAICompatibleEmbeddingService:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        dimensions: int = 1536,
        timeout_seconds: int = 20,
    ) -> None:
        self.dimensions = dimensions
        self.model = model
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
        payload = {"model": self.model, "input": texts}
        response = self.http.post("/v1/embeddings", payload)
        data = response.get("data", [])
        if not isinstance(data, list):
            raise RuntimeError("embedding response missing data list")
        embeddings: list[list[float]] = []
        for item in data:
            if not isinstance(item, dict) or not isinstance(item.get("embedding"), list):
                raise RuntimeError("embedding item missing vector")
            embeddings.append([float(value) for value in item["embedding"]])
        return embeddings

    def _extract_single_embedding(self, response: dict[str, object]) -> list[float]:
        data = response.get("data", [])
        if not isinstance(data, list) or not data:
            raise RuntimeError("embedding response missing data")
        first = data[0]
        if not isinstance(first, dict) or not isinstance(first.get("embedding"), list):
            raise RuntimeError("embedding response missing vector")
        return [float(value) for value in first["embedding"]]


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
        instructions = self._instructions_for_task(request.task)
        context = "\n\n".join(normalize_text(block) for block in request.context_blocks if normalize_text(block))
        prompt = (
            f"Task: {request.task}\n"
            f"User prompt: {normalize_text(request.prompt)}\n"
            f"Context:\n{context or '[no context]'}\n"
            "Return a concise, grounded answer."
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

    def _instructions_for_task(self, task: str) -> str:
        if task == "summary":
            return "You summarize enterprise documents into concise implementation notes."
        if task == "qa":
            return "You answer only from the provided evidence and keep the wording direct."
        if task == "speech_script":
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
