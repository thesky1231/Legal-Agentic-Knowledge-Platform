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


class RefusalPolicyTests(unittest.TestCase):
    def test_should_refuse_question_returns_conservative_answer(self) -> None:
        container = build_container()
        content = (ROOT / "examples" / "legal" / "legal_assistant_handbook.md").read_text(encoding="utf-8")
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑事法律知识助手示例手册",
                content=content,
                source="legal_assistant_handbook.md",
                tenant_id="demo",
            )
        )

        result = container.knowledge_base.answer(
            "如果只有聊天记录，能不能直接认定合同诈骗？",
            tenant_id="demo",
        )

        self.assertEqual(result.question_type, "should_refuse")
        self.assertTrue(result.refusal_triggered)
        self.assertEqual(result.confidence, "low")


if __name__ == "__main__":
    unittest.main()
