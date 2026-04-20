from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.types import DocumentIngestRequest


class EvaluationTests(unittest.TestCase):
    def test_evaluation_service_returns_summary_metrics(self) -> None:
        container = build_container()
        handbook_path = ROOT / "examples" / "legal" / "legal_assistant_handbook.md"
        content = handbook_path.read_text(encoding="utf-8")
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑事法律知识助手示例手册",
                content=content,
                source=str(handbook_path),
                tenant_id="demo",
                metadata={"tenant": "demo"},
            )
        )

        eval_run = container.evaluation_service.evaluate_from_file(str(ROOT / "examples" / "eval_dataset.json"))

        self.assertEqual(eval_run.case_count, 3)
        self.assertGreaterEqual(eval_run.grounded_rate, 0.66)
        self.assertGreaterEqual(eval_run.citation_coverage_rate, 0.66)
        self.assertEqual(len(eval_run.results), 3)


if __name__ == "__main__":
    unittest.main()
