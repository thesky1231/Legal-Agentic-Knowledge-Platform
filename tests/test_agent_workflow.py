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


class AgentWorkflowTests(unittest.TestCase):
    def test_agent_pipeline_can_generate_voice_job(self) -> None:
        container = build_container()
        sample_path = ROOT / "examples" / "legal" / "legal_assistant_handbook.md"
        content = sample_path.read_text(encoding="utf-8")
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑事法律知识助手示例手册",
                content=content,
                source=str(sample_path),
            )
        )

        response = container.agent.run(
            AgentRequest(
                query="请解释语音讲解链路如何接入法律问答流程。",
                speak_response=True,
            )
        )

        self.assertTrue(response.grounded)
        self.assertIsNotNone(response.voice_job)
        self.assertGreaterEqual(len(response.steps), 3)
        self.assertTrue(response.voice_job.audio_url.startswith("https://demo.local/audio/"))


if __name__ == "__main__":
    unittest.main()
