from __future__ import annotations

from agentic_knowledge_platform.types import (
    AgentRequest,
    AgentResponse,
    AgentStep,
    AnswerResult,
    QuestionType,
)


class ExecutionRouter:
    def __init__(self, knowledge_base, single_agent, team_agent, question_policy) -> None:
        self.knowledge_base = knowledge_base
        self.single_agent = single_agent
        self.team_agent = team_agent
        self.question_policy = question_policy

    def run_auto(self, request: AgentRequest) -> AgentResponse:
        question_type = self.question_policy.classify(request.query)
        route_step = self._router_step(
            index=1,
            action="classify_and_route",
            observation=(
                f"question_type={question_type}, selected_mode={self._initial_mode(question_type)}, "
                f"reason={self._initial_reason(question_type)}"
            ),
        )

        if question_type in {"confusing", "complex_reasoning", "should_refuse"}:
            response = self.team_agent.run(request)
            response.steps = self._prepend_steps([route_step], response.steps)
            response.agent_mode = "auto_team"
            return response

        rag_result = self.knowledge_base.answer(
            request.query,
            top_k=self.question_policy.top_k_for(question_type),
            tenant_id=request.tenant_id,
        )
        if self._is_rag_result_good_enough(rag_result, question_type):
            return self._wrap_rag_result_as_agent_response(
                answer_result=rag_result,
                question_type=question_type,
                selected_mode="auto_rag",
                route_reason="普通 RAG 结果具备引用、grounded 状态和可接受置信度。",
            )

        escalation_step = self._router_step(
            index=2,
            action="escalate",
            observation=(
                "RAG result not good enough: "
                f"grounded={rag_result.grounded}, citation_count={len(rag_result.citations)}, "
                f"confidence={rag_result.confidence}, refusal={rag_result.refusal_triggered}; "
                "escalate to single agent"
            ),
        )
        response = self.single_agent.run(request)
        response.steps = self._prepend_steps([route_step, escalation_step], response.steps)
        response.agent_mode = "auto_single"
        return response

    def _is_rag_result_good_enough(self, answer_result: AnswerResult, question_type: QuestionType) -> bool:
        if question_type in {"confusing", "complex_reasoning"}:
            return False
        if question_type == "should_refuse":
            return answer_result.refusal_triggered and answer_result.confidence == "low"
        if not answer_result.grounded:
            return False
        if not answer_result.citations:
            return False
        if answer_result.confidence == "low":
            return False
        if answer_result.refusal_triggered:
            return False
        return True

    def _wrap_rag_result_as_agent_response(
        self,
        answer_result: AnswerResult,
        question_type: QuestionType,
        selected_mode: str,
        route_reason: str,
    ) -> AgentResponse:
        steps = [
            self._router_step(
                index=1,
                action="classify_and_route",
                observation=(
                    f"question_type={question_type}, selected_mode=rag, reason={route_reason}"
                ),
            ),
            AgentStep(
                index=2,
                agent="rag-engine",
                thought="Use retrieval and grounded answer generation for a simple legal question.",
                action="answer_with_retrieval",
                observation=(
                    f"grounded={answer_result.grounded}; citations={len(answer_result.citations)}; "
                    f"confidence={answer_result.confidence}; refusal={answer_result.refusal_triggered}"
                ),
            ),
        ]
        return AgentResponse(
            answer=answer_result.answer,
            grounded=answer_result.grounded,
            citations=answer_result.citations,
            steps=steps,
            answer_sections=answer_result.answer_sections,
            agent_mode=selected_mode,
            question_type=question_type,
            confidence=answer_result.confidence,
            refusal_triggered=answer_result.refusal_triggered,
        )

    def _router_step(self, index: int, action: str, observation: str) -> AgentStep:
        return AgentStep(
            index=index,
            agent="router-agent",
            thought="Classify the legal question and select the lowest-risk execution path.",
            action=action,
            observation=observation,
        )

    def _prepend_steps(self, prefix: list[AgentStep], steps: list[AgentStep]) -> list[AgentStep]:
        merged: list[AgentStep] = []
        for step in [*prefix, *steps]:
            merged.append(
                AgentStep(
                    index=len(merged) + 1,
                    agent=step.agent,
                    thought=step.thought,
                    action=step.action,
                    observation=step.observation,
                )
            )
        return merged

    def _initial_mode(self, question_type: QuestionType) -> str:
        if question_type in {"confusing", "complex_reasoning", "should_refuse"}:
            return "team"
        return "rag"

    def _initial_reason(self, question_type: QuestionType) -> str:
        if question_type == "confusing":
            return "混淆或边界问题需要多证据对比和审核"
        if question_type == "complex_reasoning":
            return "复杂推理问题风险更高，需要 reviewer 复核"
        if question_type == "should_refuse":
            return "问题要求确定性判断，优先走保守回答和审核"
        if question_type == "definition":
            return "定义类问题优先尝试带引用 RAG"
        return "简单法律问答优先尝试普通 RAG"
