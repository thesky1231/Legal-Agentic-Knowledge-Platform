from __future__ import annotations

import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.core.serialization import to_dict
from agentic_knowledge_platform.types import AgentRequest, DocumentIngestRequest


def main() -> None:
    container = build_container()
    sample_path = ROOT / "examples" / "employee_handbook.md"
    content = sample_path.read_text(encoding="utf-8")

    ingestion = container.knowledge_base.ingest(
        DocumentIngestRequest(
            title="企业知识库 Agent 平台交付手册",
            content=content,
            source=str(sample_path),
            modality="markdown",
            tenant_id="demo",
            metadata={"tenant": "demo"},
        )
    )

    single_request = AgentRequest(
        query="如果主模型限流了，平台会怎么保证回答链路继续工作？顺便说明语音讲解是怎么接进去的。",
        speak_response=True,
        tenant_id="demo",
    )
    single_started_at = time.perf_counter()
    single_response = container.agent.run(single_request)
    single_latency_ms = max(1, int((time.perf_counter() - single_started_at) * 1000))
    container.run_store.save(
        workflow="demo_showcase_single",
        request=single_request,
        response=single_response,
    )
    container.metrics.record_pipeline_run(
        workflow="demo_showcase_single",
        mode=single_response.agent_mode,
        grounded=single_response.grounded,
        citation_count=len(single_response.citations),
        latency_ms=single_latency_ms,
        voice_enabled=single_response.voice_job is not None,
    )

    team_request = AgentRequest(
        query="请用多 Agent 视角说明这个平台如何做检索、审核和讲解。",
        speak_response=False,
        tenant_id="demo",
    )
    team_started_at = time.perf_counter()
    team_response = container.team_agent.run(team_request)
    team_latency_ms = max(1, int((time.perf_counter() - team_started_at) * 1000))
    container.run_store.save(
        workflow="demo_showcase_team",
        request=team_request,
        response=team_response,
    )
    container.metrics.record_pipeline_run(
        workflow="demo_showcase_team",
        mode=team_response.agent_mode,
        grounded=team_response.grounded,
        citation_count=len(team_response.citations),
        latency_ms=team_latency_ms,
        voice_enabled=team_response.voice_job is not None,
    )

    payload = {
        "document_id": ingestion.document.document_id,
        "chunk_count": len(ingestion.chunks),
        "single_agent_answer": to_dict(single_response),
        "team_agent_answer": to_dict(team_response),
        "recent_runs": to_dict(container.run_store.list_runs(limit=5)),
        "ops_overview": to_dict(container.metrics.snapshot()),
        "prometheus_preview": container.metrics.render_prometheus().splitlines()[:18],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
