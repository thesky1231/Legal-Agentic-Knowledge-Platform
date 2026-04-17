from __future__ import annotations

from agentic_knowledge_platform.types import AgentRequest, AgentResponse, AgentStep


class ReviewAgent:
    def review(self, response: AgentResponse) -> str:
        if not response.grounded:
            return "Reviewer rejected the answer because the evidence confidence was below the grounded threshold."
        if not response.citations:
            return "Reviewer rejected the answer because no citations were attached."
        if len(response.citations) == 1:
            return "Reviewer approved the answer with a note to retrieve more supporting evidence in production."
        return "Reviewer approved the answer as grounded, cited, and ready for delivery."


class CollaborativeTeamAgent:
    def __init__(self, react_agent, voice_pipeline, reviewer: ReviewAgent | None = None) -> None:
        self.react_agent = react_agent
        self.voice_pipeline = voice_pipeline
        self.reviewer = reviewer or ReviewAgent()

    def run(self, request: AgentRequest) -> AgentResponse:
        base_response = self.react_agent.run(
            AgentRequest(
                query=request.query,
                session_id=request.session_id,
                speak_response=False,
                tenant_id=request.tenant_id,
            )
        )
        steps = list(base_response.steps)
        review_summary = self.reviewer.review(base_response)
        steps.append(
            AgentStep(
                index=len(steps) + 1,
                agent="review-agent",
                thought="Validate that the drafted answer is grounded and carries enough citations.",
                action="review_answer",
                observation=review_summary,
            )
        )

        voice_job = base_response.voice_job
        if request.speak_response and base_response.grounded:
            voice_job = self.voice_pipeline.narrate(base_response.answer)
            steps.append(
                AgentStep(
                    index=len(steps) + 1,
                    agent="narration-agent",
                    thought="Convert the approved answer into a narration job for TTS and avatar rendering.",
                    action="narrate_answer",
                    observation=f"voice_job={voice_job.job_id}; avatar={voice_job.avatar_job_id}",
                )
            )

        return AgentResponse(
            answer=base_response.answer,
            grounded=base_response.grounded,
            citations=base_response.citations,
            steps=steps,
            voice_job=voice_job,
            agent_mode="team",
            review_summary=review_summary,
            question_type=base_response.question_type,
            confidence=base_response.confidence,
            refusal_triggered=base_response.refusal_triggered,
        )
