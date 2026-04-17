from __future__ import annotations

import hashlib
import math

from agentic_knowledge_platform.text import tokenize


class HashEmbeddingService:
    def __init__(self, dimensions: int = 96) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        tokens = tokenize(text)
        vector = [0.0] * self.dimensions
        if not tokens:
            return vector
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            first_index = int.from_bytes(digest[:2], "big") % self.dimensions
            second_index = int.from_bytes(digest[2:4], "big") % self.dimensions
            magnitude = 1.0 + digest[4] / 255.0
            vector[first_index] += magnitude
            vector[second_index] -= magnitude * 0.5
        return self._normalize(vector)

    def batch_embed(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(value * value for value in vector))
        if not norm:
            return vector
        return [value / norm for value in vector]
