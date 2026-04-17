from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.parsing import MultiModalDocumentParser
from agentic_knowledge_platform.types import DocumentIngestRequest


class ParserTests(unittest.TestCase):
    def test_markdown_parser_extracts_tables_and_formula(self) -> None:
        parser = MultiModalDocumentParser()
        document = parser.parse(
            DocumentIngestRequest(
                title="解析测试",
                source="unit",
                content="""
# 概览

这里是第一段。

| 字段 | 说明 |
| --- | --- |
| score | 检索分 |

$$
score = dense + rerank
$$
""".strip(),
            )
        )

        kinds = [element.kind for element in document.elements]
        self.assertIn("heading", kinds)
        self.assertIn("table", kinds)
        self.assertIn("formula", kinds)
        self.assertIn("概览", document.outline)


if __name__ == "__main__":
    unittest.main()
