from __future__ import annotations

import gzip
import json
from pathlib import Path
from typing import Any

from agentic_knowledge_platform.services.local_corpus import collect_document_paths, detect_modality, read_content
from agentic_knowledge_platform.types import ChunkRecord, DocumentIngestRequest, ParsedDocument


def build_snapshot(
    parser,
    chunker,
    embeddings,
    path_spec: str,
    tenant_id: str = "demo",
    embedding_batch_size: int = 32,
) -> dict[str, Any]:
    documents: list[dict[str, Any]] = []
    chunk_entries: list[dict[str, Any]] = []

    for path in collect_document_paths(path_spec):
        request = DocumentIngestRequest(
            title=path.stem,
            content=read_content(path),
            source=str(path),
            modality=detect_modality(path),
            tenant_id=tenant_id,
            metadata={"bootstrap": "snapshot", "tenant_id": tenant_id},
        )
        document = parser.parse(request)
        chunks = chunker.chunk(document)
        documents.append(_serialize_document(document))

        batch_size = max(1, embedding_batch_size)
        for start in range(0, len(chunks), batch_size):
            batch = chunks[start : start + batch_size]
            vectors = embeddings.batch_embed([chunk.content for chunk in batch])
            for chunk, vector in zip(batch, vectors, strict=True):
                chunk_entries.append(
                    {
                        "chunk": _serialize_chunk(chunk),
                        "vector": vector,
                    }
                )

    return {
        "version": 1,
        "documents": documents,
        "chunks": chunk_entries,
    }


def save_snapshot(snapshot: dict[str, Any], path: str | Path) -> Path:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(snapshot, ensure_ascii=False, separators=(",", ":"))
    if target.suffix == ".gz":
        with gzip.open(target, "wt", encoding="utf-8") as handle:
            handle.write(payload)
    else:
        target.write_text(payload, encoding="utf-8")
    return target


def load_snapshot(path: str | Path) -> dict[str, Any]:
    source = Path(path)
    if not source.exists():
        raise FileNotFoundError(f"bootstrap snapshot not found: {source}")
    if source.suffix == ".gz":
        with gzip.open(source, "rt", encoding="utf-8") as handle:
            return json.load(handle)
    return json.loads(source.read_text(encoding="utf-8"))


def load_snapshot_into_knowledge_base(
    knowledge_base,
    vector_store,
    path: str | Path,
    embedding_batch_size: int = 32,
) -> dict[str, Any]:
    snapshot = load_snapshot(path)
    documents = snapshot.get("documents", [])
    chunks = snapshot.get("chunks", [])

    for document_payload in documents:
        document = ParsedDocument(
            document_id=str(document_payload["document_id"]),
            title=str(document_payload["title"]),
            source=str(document_payload["source"]),
            modality=str(document_payload["modality"]),
            language=str(document_payload.get("language", "zh")),
            outline=[str(item) for item in document_payload.get("outline", [])],
            elements=[],
            keywords=[str(item) for item in document_payload.get("keywords", [])],
            metadata={str(key): str(value) for key, value in document_payload.get("metadata", {}).items()},
        )
        knowledge_base.documents[document.document_id] = document
        knowledge_base.chunks_by_document.setdefault(document.document_id, [])

    batch_size = max(1, embedding_batch_size)
    for start in range(0, len(chunks), batch_size):
        batch_entries = chunks[start : start + batch_size]
        batch_chunks: list[ChunkRecord] = []
        batch_vectors: list[list[float]] = []
        for entry in batch_entries:
            chunk_payload = entry.get("chunk", {})
            chunk = ChunkRecord(
                chunk_id=str(chunk_payload["chunk_id"]),
                document_id=str(chunk_payload["document_id"]),
                title=str(chunk_payload["title"]),
                section=str(chunk_payload["section"]),
                content=str(chunk_payload["content"]),
                source=str(chunk_payload["source"]),
                metadata={str(key): str(value) for key, value in chunk_payload.get("metadata", {}).items()},
                token_count=int(chunk_payload.get("token_count", 0)),
            )
            batch_chunks.append(chunk)
            batch_vectors.append([float(value) for value in entry.get("vector", [])])
            knowledge_base.chunks_by_document.setdefault(chunk.document_id, []).append(chunk)
        vector_store.upsert(batch_chunks, batch_vectors)

    return {
        "document_count": len(documents),
        "chunk_count": len(chunks),
    }


def _serialize_document(document: ParsedDocument) -> dict[str, Any]:
    return {
        "document_id": document.document_id,
        "title": document.title,
        "source": document.source,
        "modality": document.modality,
        "language": document.language,
        "outline": document.outline,
        "keywords": document.keywords,
        "metadata": document.metadata,
    }


def _serialize_chunk(chunk: ChunkRecord) -> dict[str, Any]:
    return {
        "chunk_id": chunk.chunk_id,
        "document_id": chunk.document_id,
        "title": chunk.title,
        "section": chunk.section,
        "content": chunk.content,
        "source": chunk.source,
        "metadata": chunk.metadata,
        "token_count": chunk.token_count,
    }
