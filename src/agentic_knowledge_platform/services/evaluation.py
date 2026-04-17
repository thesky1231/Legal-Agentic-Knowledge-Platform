from __future__ import annotations

import json
import time
from pathlib import Path

from agentic_knowledge_platform.text import short_snippet, top_keywords
from agentic_knowledge_platform.types import AgentRequest, EvalCase, EvalCaseResult, EvalRun


class EvaluationService:
    def __init__(self, agent, team_agent) -> None:
        self.agent = agent
        self.team_agent = team_agent

    def load_cases(self, dataset_path: str) -> list[EvalCase]:
        payload = json.loads(Path(dataset_path).read_text(encoding="utf-8"))
        raw_cases = payload.get("cases", []) if isinstance(payload, dict) else payload
        cases: list[EvalCase] = []
        for item in raw_cases:
            if not isinstance(item, dict):
                continue
            should_refuse = item.get("should_refuse")
            expected_keywords = [str(value) for value in item.get("expected_keywords", [])]
            if not expected_keywords and item.get("reference_answer"):
                expected_keywords = top_keywords(str(item.get("reference_answer", "")), limit=4)
            cases.append(
                EvalCase(
                    case_id=str(item.get("case_id", item.get("id", f"case-{len(cases) + 1}"))),
                    tenant_id=str(item.get("tenant_id", "default")),
                    question=str(item.get("question", "")),
                    expected_keywords=expected_keywords,
                    min_citations=int(item.get("min_citations", 0 if should_refuse else 1)),
                    agent_mode=str(item.get("agent_mode", "single")),
                    expected_question_type=(
                        str(item.get("expected_question_type"))
                        if item.get("expected_question_type") is not None
                        else (str(item.get("type")) if item.get("type") is not None else None)
                    ),
                    should_refuse=bool(should_refuse) if should_refuse is not None else None,
                    expected_articles=[str(value) for value in item.get("expected_articles", [])],
                )
            )
        return cases

    def evaluate(self, dataset_name: str, cases: list[EvalCase]) -> EvalRun:
        results: list[EvalCaseResult] = []
        for case in cases:
            started = time.perf_counter()
            request = AgentRequest(
                query=case.question,
                tenant_id=case.tenant_id,
                speak_response=False,
            )
            if case.agent_mode == "team":
                response = self.team_agent.run(request)
            else:
                response = self.agent.run(request)
            latency_ms = int((time.perf_counter() - started) * 1000)
            scored_text = f"{response.answer} {response.review_summary or ''}"
            keyword_hit_rate = self._keyword_hit_rate(scored_text, case.expected_keywords)
            question_type_match = (
                response.question_type == case.expected_question_type
                if case.expected_question_type is not None
                else True
            )
            refusal_match = (
                response.refusal_triggered == case.should_refuse
                if case.should_refuse is not None
                else True
            )
            citation_match = self._citation_match(response.citations, case.expected_articles)
            policy_passed = question_type_match and refusal_match
            passed = (
                (response.grounded or response.refusal_triggered)
                and len(response.citations) >= case.min_citations
                and keyword_hit_rate >= 0.5
                and citation_match
                and policy_passed
            )
            results.append(
                EvalCaseResult(
                    case_id=case.case_id,
                    tenant_id=case.tenant_id,
                    grounded=response.grounded,
                    citation_count=len(response.citations),
                    keyword_hit_rate=keyword_hit_rate,
                    passed=passed,
                    latency_ms=latency_ms,
                    answer_preview=short_snippet(response.answer, limit=180),
                    question_type=response.question_type,
                    confidence=response.confidence,
                    question_type_match=question_type_match,
                    refusal_match=refusal_match,
                    citation_match=citation_match,
                    policy_passed=policy_passed,
                )
            )

        case_count = len(results)
        grounded_rate = self._ratio(sum(1 for item in results if item.grounded), case_count)
        citation_coverage_rate = self._ratio(sum(1 for item in results if item.citation_count > 0), case_count)
        pass_rate = self._ratio(sum(1 for item in results if item.passed), case_count)
        question_type_match_rate = self._ratio(sum(1 for item in results if item.question_type_match), case_count)
        refusal_match_rate = self._ratio(sum(1 for item in results if item.refusal_match), case_count)
        citation_match_rate = self._ratio(sum(1 for item in results if item.citation_match), case_count)
        policy_pass_rate = self._ratio(sum(1 for item in results if item.policy_passed), case_count)
        avg_latency_ms = int(sum(item.latency_ms for item in results) / case_count) if case_count else 0
        return EvalRun(
            dataset_name=dataset_name,
            case_count=case_count,
            grounded_rate=grounded_rate,
            citation_coverage_rate=citation_coverage_rate,
            pass_rate=pass_rate,
            avg_latency_ms=avg_latency_ms,
            results=results,
            question_type_match_rate=question_type_match_rate,
            refusal_match_rate=refusal_match_rate,
            citation_match_rate=citation_match_rate,
            policy_pass_rate=policy_pass_rate,
        )

    def evaluate_from_file(self, dataset_path: str) -> EvalRun:
        cases = self.load_cases(dataset_path)
        dataset_name = Path(dataset_path).name
        return self.evaluate(dataset_name=dataset_name, cases=cases)

    def _keyword_hit_rate(self, answer: str, keywords: list[str]) -> float:
        if not keywords:
            return 1.0
        lowered = answer.lower()
        hits = sum(1 for keyword in keywords if keyword.lower() in lowered)
        return round(hits / len(keywords), 4)

    def _ratio(self, numerator: int, denominator: int) -> float:
        if denominator == 0:
            return 0.0
        return round(numerator / denominator, 4)

    def _citation_match(self, citations: list[object], expected_articles: list[str]) -> bool:
        if not expected_articles:
            return True
        actual_titles = [
            f"{getattr(citation, 'title', '')}{getattr(citation, 'section', '')}".replace(" ", "")
            for citation in citations
        ]
        normalized_expected = [article.replace(" ", "") for article in expected_articles]
        for expected in normalized_expected:
            if any(expected in actual or actual in expected for actual in actual_titles if actual):
                return True
        return False
