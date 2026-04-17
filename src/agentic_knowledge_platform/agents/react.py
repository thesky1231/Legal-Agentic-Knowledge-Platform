from __future__ import annotations

from agentic_knowledge_platform.types import AgentRequest, AgentResponse, AgentStep


class ReActAgent:
    def __init__(self, knowledge_base, voice_pipeline) -> None:
        self.knowledge_base = knowledge_base
        self.voice_pipeline = voice_pipeline

    def run(self, request: AgentRequest) -> AgentResponse:
        steps: list[AgentStep] = []

        retrieval_hits = self.knowledge_base.retrieve(request.query)
        steps.append(
            AgentStep(
                index=1,
                thought="先从知识库检索与问题最相关的证据块，确认有没有足够上下文。",
                action="knowledge_retrieve",
                observation=f"命中 {len(retrieval_hits)} 个 chunk。",
            )
        )

        answer_result = self.knowledge_base.answer(request.query)
        steps.append(
            AgentStep(
                index=2,
                thought="基于引用证据组织回答，并检查 grounded 阈值是否通过。",
                action="answer_with_citations",
                observation=f"grounded={answer_result.grounded}; citations={len(answer_result.citations)}",
            )
        )

        voice_job = None
        if request.speak_response and answer_result.grounded:
            voice_job = self.voice_pipeline.narrate(answer_result.answer)
            steps.append(
                AgentStep(
                    index=3,
                    thought="用户需要语音讲解，因此把回答转成讲解脚本并交给 TTS 与 A2F 渲染。",
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
        )
