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
            service.classify("抢劫和抢夺的区别是什么？"),
            "confusing",
        )


if __name__ == "__main__":
    unittest.main()
