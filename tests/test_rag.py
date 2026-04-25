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


LEGAL_SAMPLE = """
# 刑事法律知识

## 抢劫罪和抢夺罪的区别
抢劫罪通常以暴力、胁迫或者其他足以压制被害人反抗的方法取得财物，行为同时侵犯财产法益和人身安全。
抢夺罪通常表现为乘人不备、公然夺取财物，一般不以暴力压制反抗为核心。比较二者时，应重点关注行为方式、暴力胁迫程度、保护法益和法条适用边界。

## 盗窃罪构成要件
盗窃罪通常围绕非法占有目的、秘密窃取行为、公私财物对象以及数额或情节要求展开。回答构成要件时应结合具体事实和证据链。
"""


class RagTests(unittest.TestCase):
    def setUp(self) -> None:
        self.container = build_container()
        self.container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑事法律知识",
                content=LEGAL_SAMPLE,
                source="unit",
                modality="markdown",
                tenant_id="demo",
            )
        )

    def test_grounded_answer_contains_citations(self) -> None:
        answer = self.container.knowledge_base.answer("请比较抢劫罪和抢夺罪的区别。", tenant_id="demo")
        self.assertTrue(answer.grounded)
        self.assertGreaterEqual(len(answer.citations), 1)
        self.assertEqual(answer.question_type, "confusing")
        self.assertEqual(answer.answer_sections[0].title, "结论")

    def test_unknown_question_is_rejected(self) -> None:
        answer = self.container.knowledge_base.answer("公司年假有多少天？", tenant_id="demo")
        self.assertFalse(answer.grounded)
        self.assertTrue(answer.refusal_triggered)

    def test_labor_question_rejects_weak_company_crime_match(self) -> None:
        container = build_container()
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="刑法条文",
                content=(
                    "## 挪用资金罪\n"
                    "公司、企业或者其他单位的工作人员，利用职务上的便利，"
                    "挪用本单位资金归个人使用或者借贷给他人，数额较大、超过三个月未还的，"
                    "依照相关刑法条文处理。"
                ),
                source="unit",
                modality="markdown",
                tenant_id="demo",
            )
        )

        answer = container.knowledge_base.answer("公司年假有多少天？", tenant_id="demo")

        self.assertFalse(answer.grounded)
        self.assertTrue(answer.refusal_triggered)
        self.assertIn("guard=lexical_mismatch", answer.reasoning)


if __name__ == "__main__":
    unittest.main()
