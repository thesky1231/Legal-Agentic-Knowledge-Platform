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


class AnswerSectionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = build_container()
        self.container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑事法律知识",
                content=(
                    "# 刑事法律知识\n"
                    "## 抢劫罪和抢夺罪的区别\n"
                    "抢劫罪通常以暴力、胁迫或者其他方法压制反抗后取得财物。"
                    "抢夺罪通常是乘人不备公然夺取财物。"
                    "回答比较题时应说明行为方式、暴力胁迫、保护法益和适用边界。"
                    "如果问题要求区分两个罪名，系统需要同时检索相关概念并给出可追溯引用，"
                    "避免只凭一个片段作出过度确定的结论。\n"
                ),
                source="unit",
                modality="markdown",
                tenant_id="demo",
            )
        )

    def test_grounded_answers_include_structured_sections(self) -> None:
        answer = self.container.knowledge_base.answer("请比较抢劫罪和抢夺罪的区别。", tenant_id="demo")
        self.assertTrue(answer.grounded)
        self.assertGreaterEqual(len(answer.answer_sections), 3)
        self.assertEqual(answer.answer_sections[0].title, "结论")
        self.assertEqual(answer.answer_sections[1].title, "法条依据")

    def test_refusal_answers_include_structured_sections(self) -> None:
        answer = self.container.knowledge_base.answer("公司年假有多少天？", tenant_id="demo")
        self.assertTrue(answer.refusal_triggered)
        self.assertGreaterEqual(len(answer.answer_sections), 3)
        self.assertEqual(answer.answer_sections[0].title, "结论")


if __name__ == "__main__":
    unittest.main()
