from __future__ import annotations

import json
import sys
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
    sample_path = ROOT / "examples" / "legal" / "legal_assistant_handbook.md"
    content = sample_path.read_text(encoding="utf-8")

    ingestion = container.knowledge_base.ingest(
        DocumentIngestRequest(
            title="刑事法律知识助手示例手册",
            content=content,
            source=str(sample_path),
            modality="markdown",
            tenant_id="demo",
            metadata={"tenant": "demo"},
        )
    )

    response = container.agent.run(
        AgentRequest(
            query="如果只有聊天记录，能不能直接认定合同诈骗？如果需要讲给用户听，语音讲解链路会怎么接入？",
            speak_response=True,
            tenant_id="demo",
        )
    )
    container.run_store.save(
        workflow="demo_cli_single",
        request=AgentRequest(
            query="如果只有聊天记录，能不能直接认定合同诈骗？如果需要讲给用户听，语音讲解链路会怎么接入？",
            speak_response=True,
            tenant_id="demo",
        ),
        response=response,
    )

    team_response = container.team_agent.run(
        AgentRequest(
            query="请比较抢劫和抢夺的区别，并说明多 Agent 模式会怎样审核回答。",
            speak_response=False,
            tenant_id="demo",
        )
    )
    container.run_store.save(
        workflow="demo_cli_team",
        request=AgentRequest(
            query="请比较抢劫和抢夺的区别，并说明多 Agent 模式会怎样审核回答。",
            speak_response=False,
            tenant_id="demo",
        ),
        response=team_response,
    )

    payload = {
        "document_id": ingestion.document.document_id,
        "chunk_count": len(ingestion.chunks),
        "single_agent_answer": to_dict(response),
        "team_agent_answer": to_dict(team_response),
        "recent_runs": to_dict(container.run_store.list_runs(limit=5)),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
