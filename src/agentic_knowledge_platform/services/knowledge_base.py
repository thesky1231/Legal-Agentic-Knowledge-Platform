from __future__ import annotations

from collections import Counter
from collections import defaultdict
from dataclasses import dataclass
import math
import re

from agentic_knowledge_platform.text import normalize_text, short_snippet, tokenize
from agentic_knowledge_platform.services.query_policy import QuestionPolicyService
from agentic_knowledge_platform.services.vector_store import StoredVectorRecord
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


QUERY_FILLER_CHARS = frozenset("的了是有吗呢么什多几天与和及或请问")
SPECIAL_OBJECT_TERMS = frozenset(
    {
        "枪支",
        "弹药",
        "爆炸物",
        "危险物质",
        "毒害性",
        "放射性",
        "传染病",
        "武器装备",
        "军用物资",
        "邮件",
        "电报",
        "发票",
        "税款",
    }
)
BOUNDARY_CONTEXT_TERMS = frozenset(
    {
        "窝藏赃物",
        "抗拒抓捕",
        "毁灭罪证",
        "当场使用暴力",
    }
)
GENERIC_QUERY_TERMS = frozenset(
    {
        "什么",
        "怎么",
        "如何",
        "多少",
        "几天",
        "有多",
        "少天",
        "是否",
        "可以",
        "哪些",
        "有关",
        "规定",
        "公司",
        "企业",
        "单位",
        "人员",
        "工作",
        "职工",
        "员工",
        "区别",
        "不同",
        "比较",
        "说明",
        "请问",
        "请用",
        "应当",
        "判断",
        "处理",
        "如果",
        "为何",
        "为什么",
    }
)


def meaningful_query_terms(question: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    for token in tokenize(question):
        if len(token) < 2:
            continue
        if token in GENERIC_QUERY_TERMS:
            continue
        if any(char in QUERY_FILLER_CHARS for char in token):
            continue
        if not any("\u4e00" <= char <= "\u9fff" for char in token):
            continue
        if token in seen:
            continue
        terms.append(token)
        seen.add(token)
    return terms


@dataclass(slots=True)
class RetrievalCandidate:
    record: StoredVectorRecord
    vector_score: float = 0.0
    keyword_score: float = 0.0


class LexicalReranker:
    def rerank(
        self,
        question: str,
        candidates: list[RetrievalCandidate] | list[tuple[float, object]],
        top_k: int,
    ) -> list[RetrievalHit]:
        query_tokens = set(meaningful_query_terms(question)) or set(tokenize(question))
        rescored: list[RetrievalHit] = []
        for candidate in candidates:
            if isinstance(candidate, RetrievalCandidate):
                record = candidate.record
                vector_score = candidate.vector_score
                keyword_score = candidate.keyword_score
            else:
                vector_score, record = candidate
                keyword_score = 0.0
            chunk = record.chunk
            chunk_tokens = set(tokenize(f"{chunk.section} {chunk.content}"))
            overlap = len(query_tokens & chunk_tokens) / max(1, len(query_tokens))
            section_tokens = set(tokenize(chunk.section))
            section_boost = 0.15 if query_tokens & section_tokens else 0.0
            focus_adjustment = self._section_focus_adjustment(query_tokens, chunk)
            final_score = round(
                (vector_score * 0.45)
                + (keyword_score * 0.25)
                + (overlap * 0.30)
                + section_boost
                + focus_adjustment,
                4,
            )
            rescored.append(
                RetrievalHit(
                    chunk=chunk,
                    vector_score=round(vector_score, 4),
                    rerank_score=round(keyword_score + overlap + section_boost, 4),
                    final_score=final_score,
                )
            )
        rescored.sort(key=lambda item: item.final_score, reverse=True)
        return rescored[:top_k]

    def _section_focus_adjustment(self, query_tokens: set[str], chunk: ChunkRecord) -> float:
        if not query_tokens:
            return 0.0

        section = normalize_text(chunk.section)
        content_preview = normalize_text(chunk.content[:180])
        section_matches = [term for term in query_tokens if term in section]
        evidence_matches = [term for term in query_tokens if term in section or term in content_preview]

        adjustment = 0.0
        if section_matches:
            adjustment += min(0.28, 0.14 * len(section_matches))
        if len(evidence_matches) >= max(1, min(2, len(query_tokens))):
            adjustment += 0.06
        if self._looks_like_primary_article(section, query_tokens):
            adjustment += 0.18

        if any(term in section or term in content_preview for term in SPECIAL_OBJECT_TERMS):
            adjustment -= 0.34
        if any(term in content_preview for term in BOUNDARY_CONTEXT_TERMS):
            adjustment -= 0.26
        if self._has_extra_crime_focus(section, query_tokens):
            adjustment -= 0.12

        return adjustment

    def _looks_like_primary_article(self, section: str, query_tokens: set[str]) -> bool:
        if any(term in section for term in SPECIAL_OBJECT_TERMS):
            return False
        if not any(term in section for term in query_tokens):
            return False
        if len(section) <= 16:
            return True
        if len(query_tokens) >= 2 and all(term in section for term in query_tokens) and len(section) <= 22:
            return True
        return False

    def _has_extra_crime_focus(self, section: str, query_tokens: set[str]) -> bool:
        crime_terms = re.findall(r"[\u4e00-\u9fff]{1,10}罪", section)
        if len(crime_terms) <= 1:
            return False
        matched_crimes = [crime for crime in crime_terms if any(term in crime for term in query_tokens)]
        return len(matched_crimes) < len(crime_terms)


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
        vector_results = self.vector_store.search(
            query_vector,
            top_k=max(effective_top_k * 3, effective_top_k),
            tenant_id=tenant_id,
        )
        keyword_results = self._keyword_search(
            question=question,
            top_k=max(effective_top_k * 2, effective_top_k),
            tenant_id=tenant_id,
        )
        candidates = self._merge_retrieval_candidates(vector_results, keyword_results)
        return self.reranker.rerank(question, candidates, effective_top_k)

    def _merge_retrieval_candidates(
        self,
        vector_results: list[tuple[float, StoredVectorRecord]],
        keyword_results: list[tuple[float, ChunkRecord]],
    ) -> list[RetrievalCandidate]:
        candidates: dict[str, RetrievalCandidate] = {}
        for score, record in vector_results:
            candidates[record.chunk.chunk_id] = RetrievalCandidate(
                record=record,
                vector_score=float(score),
                keyword_score=0.0,
            )

        max_keyword_score = max((score for score, _ in keyword_results), default=0.0)
        for score, chunk in keyword_results:
            normalized_keyword_score = float(score) / max_keyword_score if max_keyword_score > 0 else 0.0
            existing = candidates.get(chunk.chunk_id)
            if existing:
                existing.keyword_score = max(existing.keyword_score, normalized_keyword_score)
                continue
            candidates[chunk.chunk_id] = RetrievalCandidate(
                record=StoredVectorRecord(chunk=chunk, vector=[]),
                vector_score=0.0,
                keyword_score=normalized_keyword_score,
            )
        return list(candidates.values())

    def _keyword_search(
        self,
        question: str,
        top_k: int,
        tenant_id: str | None = None,
    ) -> list[tuple[float, ChunkRecord]]:
        query_terms = meaningful_query_terms(question)
        if not query_terms:
            return []

        chunks = self._tenant_chunks(tenant_id)
        if not chunks:
            return []

        chunk_tokens = [self._bm25_tokens(f"{chunk.section} {chunk.content}") for chunk in chunks]
        doc_count = len(chunks)
        avg_doc_length = sum(len(tokens) for tokens in chunk_tokens) / max(1, doc_count)
        doc_frequency: Counter[str] = Counter()
        for tokens in chunk_tokens:
            doc_frequency.update(set(tokens))

        scores: list[tuple[float, ChunkRecord]] = []
        for chunk, tokens in zip(chunks, chunk_tokens, strict=True):
            if not tokens:
                continue
            token_counts = Counter(tokens)
            doc_length = len(tokens)
            score = 0.0
            for term in query_terms:
                term_frequency = token_counts.get(term, 0)
                if term_frequency <= 0:
                    continue
                frequency = doc_frequency.get(term, 0)
                inverse_document_frequency = math.log(
                    1 + (doc_count - frequency + 0.5) / (frequency + 0.5)
                )
                k1 = 1.5
                b = 0.75
                denominator = term_frequency + k1 * (1 - b + b * doc_length / max(1.0, avg_doc_length))
                score += inverse_document_frequency * ((term_frequency * (k1 + 1)) / denominator)
            if score > 0:
                scores.append((round(score, 4), chunk))

        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[:top_k]

    def _tenant_chunks(self, tenant_id: str | None) -> list[ChunkRecord]:
        chunks: list[ChunkRecord] = []
        for document_chunks in self.chunks_by_document.values():
            for chunk in document_chunks:
                if tenant_id and chunk.metadata.get("tenant_id") != tenant_id:
                    continue
                chunks.append(chunk)
        return chunks

    def _bm25_tokens(self, text: str) -> list[str]:
        return [
            token
            for token in tokenize(text)
            if len(token) >= 2 and not any(char in QUERY_FILLER_CHARS for char in token)
        ]

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
        return self.finalize_answer(
            plan,
            model_output=model_response.output,
            route=model_response.route,
            model_diagnostics=model_response.diagnostics,
        )

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

        evidence_supported = self._evidence_covers_question(question, hits, question_type)
        if (
            not grounded
            or self.question_policy.is_low_confidence(question, hits, question_type)
            or not evidence_supported
        ):
            guard_reason = "guard=insufficient_evidence" if evidence_supported else "guard=lexical_mismatch"
            return {
                "status": "low_confidence",
                "question": question,
                "question_type": question_type,
                "citations": citations,
                "reasoning": reasoning + [guard_reason],
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
        model_diagnostics: list[str] | None = None,
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
        for diagnostic in model_diagnostics or []:
            reasoning.append(f"model_error={normalize_text(diagnostic)[:500]}")
        cleaned_answer = self._clean_model_answer(model_output or "")
        if self._model_signaled_insufficient_evidence(cleaned_answer):
            reasoning.append("guard=model_insufficient_evidence")
            sections = self._build_low_confidence_sections(question, citations)
            return AnswerResult(
                answer=self._render_sections(sections),
                grounded=False,
                citations=citations,
                answer_sections=sections,
                reasoning=reasoning,
                question_type=question_type,
                confidence="low",
                refusal_triggered=True,
            )
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
                body="当前知识库没有检索到足以回答该问题的依据，不能基于弱相关材料作出明确回答。",
            ),
            AnswerSection(
                title="原因",
                body="检索可能命中了一些字面相关材料，但它们没有直接覆盖问题的核心事实、概念或适用规则，因此不作为回答依据。",
            ),
        ]
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

    def _evidence_covers_question(
        self,
        question: str,
        hits: list[RetrievalHit],
        question_type: str,
    ) -> bool:
        if question_type == "should_refuse":
            return True
        if not hits:
            return False

        query_terms = self._question_evidence_terms(question)
        if not query_terms:
            return True

        evidence_text = normalize_text(
            " ".join(
                f"{hit.chunk.section} {hit.chunk.content}"
                for hit in hits[: min(3, len(hits))]
            )
        )
        matched_terms = {term for term in query_terms if term in evidence_text}
        match_count = len(matched_terms)
        coverage = match_count / max(1, len(query_terms))

        if len(query_terms) <= 2:
            return match_count >= 1
        if len(query_terms) <= 5:
            return match_count >= 2 or coverage >= 0.5
        return match_count >= 2 and coverage >= 0.25

    def _question_evidence_terms(self, question: str) -> list[str]:
        return meaningful_query_terms(question)

    def _clean_model_answer(self, answer: str) -> str:
        cleaned = normalize_text(answer)
        cleaned = re.sub(r"^(Primary Model|Fallback Model|[A-Za-z][A-Za-z0-9 _-]{0,30})基于检索证据的回答[:：]?\s*", "", cleaned)
        cleaned = re.sub(r"^结论[:：]\s*", "", cleaned)
        cleaned = re.sub(r"\s*Citations:.*$", "", cleaned)
        return cleaned.strip()

    def _model_signaled_insufficient_evidence(self, answer: str) -> bool:
        normalized = normalize_text(answer).upper()
        return normalized == "EVIDENCE_INSUFFICIENT"

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
