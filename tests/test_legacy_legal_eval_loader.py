from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container


class LegacyLegalEvalLoaderTests(unittest.TestCase):
    def test_loader_accepts_legacy_list_dataset(self) -> None:
        container = build_container()
        dataset_path = ROOT / "examples" / "legal" / "answer_eval_dataset.json"

        cases = container.evaluation_service.load_cases(str(dataset_path))

        self.assertEqual(len(cases), 15)
        self.assertEqual(cases[0].expected_question_type, "direct_answer")
        self.assertEqual(cases[8].should_refuse, True)


if __name__ == "__main__":
    unittest.main()
