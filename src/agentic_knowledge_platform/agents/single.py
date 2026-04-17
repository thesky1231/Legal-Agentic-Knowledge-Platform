from __future__ import annotations

from agentic_knowledge_platform.types import AgentRequest, AgentResponse, AgentStep


class ReActAgent:
    def __init__(self, knowledge_base, voice_pipeline) -> None:
        self.knowledge_base = knowledge_base
        self.voice_pipeline = voice_pipeline

    def run(self, request: AgentRequest) -> AgentResponse:
        steps: list[AgentStep] = []

        retrieval_hits = self.knowledge_base.retrieve(request.query, tenant_id=request.tenant_id)
        steps.append(
            AgentStep(
                index=1,
                agent="react-agent",
                thought="Retrieve the most relevant evidence blocks before composing the answer.",
                action="knowledge_retrieve",
                observation=f"Retrieved {len(retrieval_hits)} chunks.",
            )
        )

        answer_result = self.knowledge_base.answer(request.query, tenant_id=request.tenant_id)
        steps.append(
            AgentStep(
                index=2,
                agent="react-agent",
                thought="Compose a grounded answer and verify the confidence threshold.",
                action="answer_with_citations",
                observation=(
                    f"grounded={answer_result.grounded}; citations={len(answer_result.citations)}; "
                    f"type={answer_result.question_type}; confidence={answer_result.confidence}; "
                    f"refusal={answer_result.refusal_triggered}"
                ),
            )
        )

        voice_job = None
        if request.speak_response and answer_result.grounded:
            voice_job = self.voice_pipeline.narrate(answer_result.answer)
            steps.append(
                AgentStep(
                    index=3,
                    agent="react-agent",
                    thought="Turn the answer into a speech-friendly script and trigger TTS/A2F rendering.",
                    action="voice_narration",
                    observation=f"voice_job={voice_job.job_id}; avatar={voice_job.avatar_job_id}",
                )
            )

        return AgentResponse(
            answer=answer_result.answer,
            grounded=answer_result.grounded,
            citations=answer_result.citations,
            steps=steps,
            voice_job=voice_job,
            agent_mode="single",
            question_type=answer_result.question_type,
            confidence=answer_result.confidence,
            refusal_triggered=answer_result.refusal_triggered,
        )
