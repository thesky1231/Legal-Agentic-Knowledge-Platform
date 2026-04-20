from __future__ import annotations

from agentic_knowledge_platform.services.http_json import JsonHttpClient
from agentic_knowledge_platform.text import normalize_text
from agentic_knowledge_platform.types import ModelRequest


class OllamaModelClient:
    def __init__(
        self,
        name: str,
        model: str,
        base_url: str,
        supported_tasks: set[str],
        timeout_seconds: int = 20,
        temperature: float = 0.0,
        keep_alive: str = "5m",
    ) -> None:
        self.name = name
        self.model = model
        self.supported_tasks = supported_tasks
        self.temperature = temperature
        self.keep_alive = keep_alive
        self.http = JsonHttpClient(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
        )

    def generate(self, request: ModelRequest) -> str:
        system_prompt = self._instructions_for_task(request.task)
        context = "\n\n".join(normalize_text(block) for block in request.context_blocks if normalize_text(block))
        user_prompt = (
            f"Task: {request.task}\n"
            f"User prompt: {normalize_text(request.prompt)}\n"
            f"Context:\n{context or '[no context]'}\n"
            "Return a concise, grounded answer."
        )
        response = self.http.post(
            "/api/generate",
            {
                "model": self.model,
                "system": system_prompt,
                "prompt": user_prompt,
                "stream": False,
                "keep_alive": self.keep_alive,
                "options": {
                    "temperature": self.temperature,
                },
            },
        )
        return self._extract_text(response)

    def _instructions_for_task(self, task: str) -> str:
        if task == "summary":
            return "You summarize legal and enterprise documents into concise implementation notes."
        if task == "qa":
            return "You answer only from the provided evidence, keep the wording direct, and avoid unsupported claims."
        if task == "speech_script":
            return "You turn technical answers into a spoken teaching script of about one minute."
        return "You are a careful backend AI platform assistant."

    def _extract_text(self, response: dict[str, object]) -> str:
        text = response.get("response", "")
        if not isinstance(text, str) or not text.strip():
            raise RuntimeError("ollama response missing text")
        return normalize_text(text)

