from __future__ import annotations

from collections import defaultdict
import re

from agentic_knowledge_platform.text import normalize_text, short_snippet, tokenize
from agentic_knowledge_platform.services.query_policy import QuestionPolicyService
from agentic_knowledge_platform.types import (
    AnswerSection,
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
        embedding_batch_size: int = 32,
        question_policy: QuestionPolicyService | None = None,
    ) -> None:
        self.parser = parser
        self.chunker = chunker
        self.embeddings = embeddings
        self.vector_store = vector_store
        self.reranker = reranker
        self.model_router = model_router
        self.grounded_threshold = grounded_threshold
        self.default_top_k = default_top_k
        self.embedding_batch_size = max(1, embedding_batch_size)
        self.question_policy = question_policy or QuestionPolicyService()
        self.documents: dict[str, ParsedDocument] = {}
        self.chunks_by_document: dict[str, list[ChunkRecord]] = defaultdict(list)

    def ingest(self, request: DocumentIngestRequest) -> IngestionResult:
        request.metadata = request.metadata.copy()
        request.metadata.setdefault("tenant_id", request.tenant_id)
        document = self.parser.parse(request)
        chunks = self.chunker.chunk(document)
        for start in range(0, len(chunks), self.embedding_batch_size):
            batch = chunks[start : start + self.embedding_batch_size]
            vectors = self.embeddings.batch_embed([chunk.content for chunk in batch])
            self.vector_store.upsert(batch, vectors)
        self.documents[document.document_id] = document
        self.chunks_by_document[document.document_id] = chunks
        return IngestionResult(document=document, chunks=chunks)

    def list_documents(self, tenant_id: str | None = None) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for document_id, document in self.documents.items():
            document_tenant = document.metadata.get("tenant_id", "default")
            if tenant_id and document_tenant != tenant_id:
                continue
            items.append(
                {
                    "document_id": document_id,
                    "title": document.title,
                    "source": document.source,
                    "modality": document.modality,
                    "outline": document.outline,
                    "keywords": document.keywords,
                    "chunk_count": len(self.chunks_by_document[document_id]),
                    "tenant_id": document_tenant,
                }
            )
        return items

    def retrieve(
        self,
        question: str,
        top_k: int | None = None,
        tenant_id: str | None = None,
    ) -> list[RetrievalHit]:
        effective_top_k = top_k or self.default_top_k
        query_vector = self.embeddings.embed(question)
        candidates = self.vector_store.search(
            query_vector,
            top_k=max(effective_top_k * 3, effective_top_k),
            tenant_id=tenant_id,
        )
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

    def answer(
        self,
        question: str,
        top_k: int | None = None,
        tenant_id: str | None = None,
    ) -> AnswerResult:
        plan = self.prepare_answer_plan(question, top_k=top_k, tenant_id=tenant_id)
        if plan["status"] != "grounded":
            return self.finalize_answer(plan)

        model_response = self.model_router.generate(plan["model_request"])
        return self.finalize_answer(plan, model_output=model_response.output, route=model_response.route)

    def prepare_answer_plan(
        self,
        question: str,
        top_k: int | None = None,
        tenant_id: str | None = None,
    ) -> dict[str, object]:
        question_type = self.question_policy.classify(question)
        effective_top_k = top_k or self.question_policy.top_k_for(question_type)
        hits = self.retrieve(question, effective_top_k, tenant_id=tenant_id)
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
        reasoning = [f"hits={len(hits)}", f"question_type={question_type}"]
        if hits:
            reasoning.append(f"top_score={hits[0].final_score}")
        if tenant_id:
            reasoning.append(f"tenant_id={tenant_id}")

        if question_type == "should_refuse":
            return {
                "status": "refusal",
                "question": question,
                "question_type": question_type,
                "citations": citations,
                "reasoning": reasoning + ["guard=policy_refusal"],
                "grounded": bool(citations),
                "confidence": "low",
                "refusal_triggered": True,
                "hint": "",
            }

        if not grounded or self.question_policy.is_low_confidence(question, hits, question_type):
            return {
                "status": "low_confidence",
                "question": question,
                "question_type": question_type,
                "citations": citations,
                "reasoning": reasoning + ["guard=insufficient_evidence"],
                "grounded": False,
                "confidence": "low",
                "refusal_triggered": True,
                "hint": "",
            }

        labeled_context_blocks = [
            f"{self._reference_label(citation)}：{normalize_text(hit.chunk.content)}"
            for hit, citation in zip(hits, citations, strict=False)
        ]
        return {
            "status": "grounded",
            "question": question,
            "question_type": question_type,
            "citations": citations,
            "reasoning": reasoning,
            "grounded": True,
            "confidence": self._confidence_for(question_type, hits),
            "refusal_triggered": False,
            "hint": self._build_usage_hint(question, question_type, citations),
            "model_request": ModelRequest(
                task="qa",
                prompt=question,
                context_blocks=labeled_context_blocks,
                metadata={
                    "citation_count": str(len(citations)),
                    "tenant_id": tenant_id or "default",
                    "question_type": question_type,
                },
            ),
        }

    def finalize_answer(
        self,
        plan: dict[str, object],
        model_output: str | None = None,
        route: str | None = None,
    ) -> AnswerResult:
        status = str(plan["status"])
        citations = list(plan["citations"])
        reasoning = list(plan["reasoning"])
        question_type = str(plan["question_type"])
        confidence = str(plan["confidence"])
        refusal_triggered = bool(plan["refusal_triggered"])
        grounded = bool(plan["grounded"])
        question = str(plan["question"])

        if status == "refusal":
            sections = self._build_refusal_sections(question)
            return AnswerResult(
                answer=self._render_sections(sections),
                grounded=grounded,
                citations=citations,
                answer_sections=sections,
                reasoning=reasoning,
                question_type=question_type,
                confidence=confidence,
                refusal_triggered=refusal_triggered,
            )

        if status == "low_confidence":
            sections = self._build_low_confidence_sections(question, citations)
            return AnswerResult(
                answer=self._render_sections(sections),
                grounded=grounded,
                citations=citations,
                answer_sections=sections,
                reasoning=reasoning,
                question_type=question_type,
                confidence=confidence,
                refusal_triggered=refusal_triggered,
            )

        if route:
            reasoning.append(f"route={route}")
        cleaned_answer = self._clean_model_answer(model_output or "")
        sections = self._build_grounded_sections(question, cleaned_answer, citations, question_type)
        return AnswerResult(
            answer=self._render_sections(sections),
            grounded=grounded,
            citations=citations,
            answer_sections=sections,
            reasoning=reasoning,
            question_type=question_type,
            confidence=confidence,
            refusal_triggered=refusal_triggered,
        )

    def _build_refusal_sections(self, question: str) -> list[AnswerSection]:
        return [
            AnswerSection(
                title="结论",
                body="当前问题需要结合更具体的案件事实、证据材料或裁判语境，系统不适合直接下确定性结论。",
            ),
            AnswerSection(
                title="原因",
                body=(
                    "这类问题通常涉及定性、量刑或责任判断。仅凭一句自然语言提问，无法可靠判断行为方式、主观故意、后果程度和证据完整性。"
                ),
            ),
            AnswerSection(
                title="建议",
                body=(
                    "如果你愿意，可以继续补充案情细节、法条编号或争议点，我再基于可检索到的材料给出更保守、可引用的分析。"
                    f" 原问题：{normalize_text(question)}"
                ),
            ),
        ]

    def _build_low_confidence_sections(
        self,
        question: str,
        citations: list[Citation],
    ) -> list[AnswerSection]:
        sections = [
            AnswerSection(
                title="结论",
                body="当前检索到的法条和材料不足以支撑高置信度回答，系统先给出保守结论，不直接扩展推断。",
            ),
            AnswerSection(
                title="原因",
                body="已命中的材料与问题存在一定相关性，但证据覆盖还不够完整，暂时不足以支持更明确的法律判断。",
            ),
        ]
        if citations:
            sections.append(
                AnswerSection(
                    title="已命中的相关条文",
                    body="\n".join(
                        f"- {self._reference_label(citation)}：{citation.snippet}" for citation in citations[:2]
                    ),
                )
            )
        sections.append(
            AnswerSection(
                title="建议",
                body=(
                    "建议把问题缩小到具体法条、罪名边界，或补充案件事实后再问。"
                    f" 原问题：{normalize_text(question)}"
                ),
            )
        )
        return sections

    def _build_grounded_sections(
        self,
        question: str,
        cleaned_answer: str,
        citations: list[Citation],
        question_type: str,
    ) -> list[AnswerSection]:
        conclusion = cleaned_answer or "已根据当前命中的法条和材料整理出结论。"
        basis_lines = [
            f"- {self._reference_label(citation)}：{citation.snippet}" for citation in citations[:3]
        ]
        hint = self._build_usage_hint(question, question_type, citations)
        return [
            AnswerSection(title="结论", body=conclusion),
            AnswerSection(
                title="法条依据",
                body="\n".join(basis_lines) if basis_lines else "当前未返回可展示的法条依据。",
            ),
            AnswerSection(title="提示", body=hint),
        ]

    def _build_usage_hint(
        self,
        question: str,
        question_type: str,
        citations: list[Citation],
    ) -> str:
        if question_type == "confusing":
            return "这是一个概念边界或罪名比较问题。阅读时优先关注行为方式、是否使用暴力胁迫、保护法益和法条适用边界。"
        if question_type == "definition":
            return "这是一个定义类问题，当前回答优先解释法条含义，不直接延伸到具体案件定性。"
        if question_type == "complex_reasoning":
            return "这是一个需要更多事实背景的推理类问题。当前回答只基于已命中的条文整理，不替代正式法律意见。"
        if not citations:
            return "当前没有足够引用材料支撑进一步展开，请补充更具体的问题。"
        return (
            "当前回答基于已检索到的条文内容整理，适合作为法条定位与初步分析，"
            f"不替代正式法律意见。原问题：{normalize_text(question)}"
        )

    def _confidence_for(self, question_type: str, hits: list[RetrievalHit]) -> str:
        if not hits:
            return "low"
        top_score = hits[0].final_score
        if question_type == "complex_reasoning":
            return "low" if top_score < 0.65 else "medium"
        if top_score >= 0.55:
            return "high"
        if top_score >= 0.32:
            return "medium"
        return "low"

    def _clean_model_answer(self, answer: str) -> str:
        cleaned = normalize_text(answer)
        cleaned = re.sub(r"^(Primary Model|Fallback Model|[A-Za-z][A-Za-z0-9 _-]{0,30})基于检索证据的回答[:：]?\s*", "", cleaned)
        cleaned = re.sub(r"^结论[:：]\s*", "", cleaned)
        cleaned = re.sub(r"\s*Citations:.*$", "", cleaned)
        return cleaned.strip()

    def _reference_label(self, citation: Citation) -> str:
        title = citation.title.strip()
        section = citation.section.strip()
        if title.lower() in {"law", "criminal law"}:
            return section
        if title == section:
            return title
        return f"{title} / {section}"

    def _render_sections(self, sections: list[AnswerSection]) -> str:
        return "\n\n".join(f"{section.title}\n{section.body}" for section in sections)
