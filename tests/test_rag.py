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


class RagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = build_container()
        sample_path = ROOT / "examples" / "employee_handbook.md"
        self.content = sample_path.read_text(encoding="utf-8")
        self.container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="企业知识库 Agent 平台交付手册",
                content=self.content,
                source=str(sample_path),
                modality="markdown",
            )
        )

    def test_grounded_answer_contains_citations(self) -> None:
        answer = self.container.knowledge_base.answer("主模型限流以后系统如何 fallback？")
        self.assertTrue(answer.grounded)
        self.assertGreaterEqual(len(answer.citations), 1)
        self.assertIn("fallback", answer.answer.lower())

    def test_unknown_question_is_rejected(self) -> None:
        answer = self.container.knowledge_base.answer("公司年假有多少天？")
        self.assertFalse(answer.grounded)


if __name__ == "__main__":
    unittest.main()
