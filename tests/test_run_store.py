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


class RunStoreTests(unittest.TestCase):
    def test_run_store_persists_saved_runs(self) -> None:
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

        request = AgentRequest(query="主模型失败时如何 fallback？", speak_response=False)
        response = container.agent.run(request)
        record = container.run_store.save(workflow="unit_test", request=request, response=response)
        runs = container.run_store.list_runs(limit=5)

        self.assertEqual(len(runs), 1)
        self.assertEqual(runs[0].run_id, record.run_id)
        self.assertEqual(runs[0].workflow, "unit_test")
        self.assertEqual(runs[0].citation_count, len(response.citations))


if __name__ == "__main__":
    unittest.main()
