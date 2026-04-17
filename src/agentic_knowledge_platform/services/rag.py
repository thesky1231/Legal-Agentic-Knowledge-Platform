from __future__ import annotations

from collections import defaultdict

from agentic_knowledge_platform.text import normalize_text, short_snippet, tokenize
from agentic_knowledge_platform.types import (
    AnswerResult,
    Citation,
    ChunkRecord,
    DocumentIngestRequest,
    IngestionResult,
    ModelRequest,
    ParsedDocument,
    RetrievalHit,
)


class LexicalReranker:
    def rerank(
        self,
        question: str,
        candidates: list[tuple[float, object]],
        top_k: int,
    ) -> list[RetrievalHit]:
        query_tokens = set(tokenize(question))
        rescored: list[RetrievalHit] = []
        for vector_score, record in candidates:
            chunk = record.chunk
            chunk_tokens = set(tokenize(chunk.content))
            overlap = len(query_tokens & chunk_tokens) / max(1, len(query_tokens))
            section_tokens = set(tokenize(chunk.section))
            section_boost = 0.15 if query_tokens & section_tokens else 0.0
            final_score = round((vector_score * 0.65) + (overlap * 0.35) + section_boost, 4)
            rescored.append(
                RetrievalHit(
                    chunk=chunk,
                    vector_score=round(vector_score, 4),
                    rerank_score=round(overlap + section_boost, 4),
                    final_score=final_score,
                )
            )
        rescored.sort(key=lambda item: item.final_score, reverse=True)
        return rescored[:top_k]


class KnowledgeBaseService:
    def __init__(
        self,
        parser,
        chunker,
        embeddings,
        vector_store,
        reranker: LexicalReranker,
        model_router,
        grounded_threshold: float = 0.22,
        default_top_k: int = 4,
    ) -> None:
        self.parser = parser
        self.chunker = chunker
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.reranker = reranker
        self.model_router = model_router
        self.grounded_threshold = grounded_threshold
        self.default_top_k = default_top_k
        self.documents: dict[str, ParsedDocument] = {}
        self.chunks_by_document: dict[str, list[ChunkRecord]] = defaultdict(list)

    def ingest(self, request: DocumentIngestRequest) -> IngestionResult:
        document = self.parser.parse(request)
        chunks = self.chunker.chunk(document)
        vectors = self.embeddings.batch_embed([chunk.content for chunk in chunks])
        self.vector_store.upsert(chunks, vectors)
        self.documents[document.document_id] = document
        self.chunks_by_document[document.document_id] = chunks
        return IngestionResult(document=document, chunks=chunks)

    def list_documents(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for document_id, document in self.documents.items():
            items.append(
                {
                    "document_id": document_id,
                    "title": document.title,
                    "source": document.source,
                    "modality": document.modality,
                    "outline": document.outline,
                    "keywords": document.keywords,
                    "chunk_count": len(self.chunks_by_document[document_id]),
                }
            )
        return items

    def retrieve(self, question: str, top_k: int | None = None) -> list[RetrievalHit]:
        effective_top_k = top_k or self.default_top_k
        query_vector = self.embeddings.embed(question)
        candidates = self.vector_store.search(query_vector, top_k=max(effective_top_k * 3, effective_top_k))
        return self.reranker.rerank(question, candidates, effective_top_k)

    def summarize_document(self, document_id: str) -> str:
        document = self.documents[document_id]
        chunks = self.chunks_by_document[document_id][:4]
        context_blocks = [chunk.content for chunk in chunks]
        response = self.model_router.generate(
            ModelRequest(
                task="summary",
                prompt=document.title,
                context_blocks=context_blocks,
                metadata={"document_id": document_id},
            )
        )
        return response.output

    def answer(self, question: str, top_k: int | None = None) -> AnswerResult:
        hits = self.retrieve(question, top_k)
        citations = [
            Citation(
                document_id=hit.chunk.document_id,
                chunk_id=hit.chunk.chunk_id,
                title=hit.chunk.title,
                section=hit.chunk.section,
                snippet=short_snippet(hit.chunk.content),
                score=hit.final_score,
            )
            for hit in hits
        ]
        grounded = bool(hits) and hits[0].final_score >= self.grounded_threshold
        reasoning = [f"hits={len(hits)}"]
        if hits:
            reasoning.append(f"top_score={hits[0].final_score}")
        if not grounded:
            answer = "当前知识库没有足够高置信度的证据来回答这个问题，请先补充文档或放宽检索范围。"
            reasoning.append("guard=insufficient_evidence")
            return AnswerResult(answer=answer, grounded=False, citations=citations, reasoning=reasoning)

        context_blocks = [
            f"{hit.chunk.title} / {hit.chunk.section}: {normalize_text(hit.chunk.content)}" for hit in hits
        ]
        model_response = self.model_router.generate(
            ModelRequest(
                task="qa",
                prompt=question,
                context_blocks=context_blocks,
                metadata={"citation_count": str(len(citations))},
            )
        )
        reasoning.append(f"route={model_response.route}")
        return AnswerResult(
            answer=self._attach_citations(model_response.output, citations),
            grounded=True,
            citations=citations,
            reasoning=reasoning,
        )

    def _attach_citations(self, answer: str, citations: list[Citation]) -> str:
        if not citations:
            return answer
        citation_lines = [
            f"[{index}] {citation.title} / {citation.section} / score={citation.score:.2f}"
            for index, citation in enumerate(citations[:3], start=1)
        ]
        return f"{answer}\n引用：{'；'.join(citation_lines)}"
