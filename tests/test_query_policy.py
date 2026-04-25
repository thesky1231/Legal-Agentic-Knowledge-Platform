from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.query_policy import QuestionPolicyService


class QuestionPolicyTests(unittest.TestCase):
    def test_classify_refusal_question(self) -> None:
        service = QuestionPolicyService()
        self.assertEqual(
            service.classify("能不能直接判断这个人一定构成故意伤害罪？"),
            "should_refuse",
        )

    def test_classify_comparison_question(self) -> None:
        service = QuestionPolicyService()
        self.assertEqual(
            service.classify("抢劫罪和抢夺罪有什么区别？"),
            "confusing",
        )

    def test_constitutive_elements_question_stays_direct(self) -> None:
        service = QuestionPolicyService()
        self.assertEqual(
            service.classify("盗窃罪的构成要件是什么？"),
            "direct_answer",
        )


if __name__ == "__main__":
    unittest.main()
