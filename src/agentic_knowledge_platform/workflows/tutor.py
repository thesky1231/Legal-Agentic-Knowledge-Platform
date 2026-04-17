from __future__ import annotations

from agentic_knowledge_platform.types import AgentRequest, DocumentIngestRequest, WorkflowRun


class TutoringWorkflow:
    def __init__(self, knowledge_base, agent, team_agent, run_store) -> None:
        self.knowledge_base = knowledge_base
        self.agent = agent
        self.team_agent = team_agent
        self.run_store = run_store

    def run(
        self,
        document_request: DocumentIngestRequest,
        question: str,
        speak_response: bool = False,
        agent_mode: str = "single",
        session_id: str = "default",
        tenant_id: str = "default",
    ) -> WorkflowRun:
        ingestion = self.knowledge_base.ingest(document_request)
        request = AgentRequest(
            query=question,
            session_id=session_id,
            speak_response=speak_response,
            tenant_id=tenant_id,
        )
        if agent_mode == "team":
            agent_response = self.team_agent.run(request)
        else:
            agent_response = self.agent.run(request)
        self.run_store.save(workflow="document_qa", request=request, response=agent_response)
        return WorkflowRun(
            document_id=ingestion.document.document_id,
            chunk_count=len(ingestion.chunks),
            agent_response=agent_response,
        )
