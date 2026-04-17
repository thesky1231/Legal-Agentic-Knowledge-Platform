from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from agentic_knowledge_platform.services.http_json import JsonHttpClient
from agentic_knowledge_platform.types import ChunkRecord


@dataclass(slots=True)
class StoredVectorRecord:
    chunk: ChunkRecord
    vector: list[float]


class VectorStore(Protocol):
    def upsert(self, chunks: list[ChunkRecord], vectors: list[list[float]]) -> None:
        ...

    def search(
        self,
        query_vector: list[float],
        top_k: int = 4,
        tenant_id: str | None = None,
    ) -> list[tuple[float, StoredVectorRecord]]:
        ...

    def size(self) -> int:
        ...


class InMemoryVectorStore:
    def __init__(self) -> None:
        self.records: dict[str, StoredVectorRecord] = {}

    def upsert(self, chunks: list[ChunkRecord], vectors: list[list[float]]) -> None:
        for chunk, vector in zip(chunks, vectors, strict=True):
            self.records[chunk.chunk_id] = StoredVectorRecord(chunk=chunk, vector=vector)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 4,
        tenant_id: str | None = None,
    ) -> list[tuple[float, StoredVectorRecord]]:
        scored: list[tuple[float, StoredVectorRecord]] = []
        for record in self.records.values():
            if tenant_id and record.chunk.metadata.get("tenant_id") != tenant_id:
                continue
            score = sum(left * right for left, right in zip(query_vector, record.vector, strict=True))
            scored.append((score, record))
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[:top_k]

    def size(self) -> int:
        return len(self.records)


class QdrantRestVectorStore:
    def __init__(
        self,
        base_url: str,
        collection_name: str,
        vector_size: int,
        api_key: str = "",
        timeout_seconds: int = 20,
    ) -> None:
        headers = {"api-key": api_key} if api_key else None
        self.collection_name = collection_name
        self.vector_size = vector_size
        self.cached_size = 0
        self.http = JsonHttpClient(
            base_url=base_url,
            timeout_seconds=timeout_seconds,
            default_headers=headers,
        )
        self._ensure_collection()

    def upsert(self, chunks: list[ChunkRecord], vectors: list[list[float]]) -> None:
        points = []
        for chunk, vector in zip(chunks, vectors, strict=True):
            payload = {
                "chunk_id": chunk.chunk_id,
                "document_id": chunk.document_id,
                "title": chunk.title,
                "section": chunk.section,
                "content": chunk.content,
                "source": chunk.source,
                "metadata": chunk.metadata,
                "token_count": chunk.token_count,
            }
            points.append({"id": chunk.chunk_id, "vector": vector, "payload": payload})
        self.http.put(f"/collections/{self.collection_name}/points", {"points": points})
        self.cached_size += len(points)

    def search(
        self,
        query_vector: list[float],
        top_k: int = 4,
        tenant_id: str | None = None,
    ) -> list[tuple[float, StoredVectorRecord]]:
        payload: dict[str, object] = {
            "query": query_vector,
            "limit": top_k,
            "with_payload": True,
        }
        if tenant_id:
            payload["filter"] = {
                "must": [
                    {
                        "key": "metadata.tenant_id",
                        "match": {"value": tenant_id},
                    }
                ]
            }
        response = self.http.post(
            f"/collections/{self.collection_name}/points/query",
            payload,
        )
        result = response.get("result", {})
        points = result.get("points", []) if isinstance(result, dict) else result
        if not isinstance(points, list):
            return []
        hits: list[tuple[float, StoredVectorRecord]] = []
        for point in points:
            if not isinstance(point, dict):
                continue
            payload = point.get("payload", {})
            if not isinstance(payload, dict):
                continue
            chunk = ChunkRecord(
                chunk_id=str(payload.get("chunk_id", point.get("id", ""))),
                document_id=str(payload.get("document_id", "")),
                title=str(payload.get("title", "")),
                section=str(payload.get("section", "")),
                content=str(payload.get("content", "")),
                source=str(payload.get("source", "")),
                metadata=self._normalize_metadata(payload.get("metadata", {})),
                token_count=int(payload.get("token_count", 0)),
            )
            hits.append(
                (
                    float(point.get("score", 0.0)),
                    StoredVectorRecord(chunk=chunk, vector=[]),
                )
            )
        return hits

    def size(self) -> int:
        return self.cached_size

    def _ensure_collection(self) -> None:
        try:
            self.http.put(
                f"/collections/{self.collection_name}",
                {
                    "vectors": {
                        "size": self.vector_size,
                        "distance": "Cosine",
                    }
                },
            )
        except RuntimeError as exc:
            if "already exists" not in str(exc).lower():
                raise

    def _normalize_metadata(self, metadata: object) -> dict[str, str]:
        if not isinstance(metadata, dict):
            return {}
        return {str(key): str(value) for key, value in metadata.items()}
