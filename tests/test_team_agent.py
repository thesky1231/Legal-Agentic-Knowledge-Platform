from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.types import AgentRequest, DocumentIngestRequest


class TeamAgentTests(unittest.TestCase):
    def test_team_agent_adds_review_step_and_summary(self) -> None:
        container = build_container()
        sample_path = ROOT / "examples" / "employee_handbook.md"
        content = sample_path.read_text(encoding="utf-8")
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="企业知识库 Agent 平台交付手册",
                content=content,
                source=str(sample_path),
            )
        )

        response = container.team_agent.run(
            AgentRequest(
                query="请解释多 Agent 如何分工完成检索、审核和讲解。",
                speak_response=True,
            )
        )

        self.assertEqual(response.agent_mode, "team")
        self.assertIsNotNone(response.review_summary)
        self.assertTrue(any(step.agent == "review-agent" for step in response.steps))
        self.assertIsNotNone(response.voice_job)


if __name__ == "__main__":
    unittest.main()
