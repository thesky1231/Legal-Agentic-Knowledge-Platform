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

    def test_legal_text_parser_splits_articles_with_legacy_regex_style(self) -> None:
        parser = MultiModalDocumentParser()
        document = parser.parse(
            DocumentIngestRequest(
                title="中华人民共和国刑法节选",
                source="unit",
                modality="legal_text",
                content="""
--- PAGE 1 ---
北京京师律师事务所
第一条【立法目的】为了惩罚犯罪，保护人民，根据宪法，制定本法。

第二条【本法任务】中华人民共和国刑法的任务，是用刑罚同一切犯罪行为作斗争。
""".strip(),
            )
        )

        headings = [element for element in document.elements if element.kind == "heading"]
        paragraphs = [element for element in document.elements if element.kind == "paragraph"]

        self.assertEqual(2, len(headings))
        self.assertEqual(2, len(paragraphs))
        self.assertEqual("第一条 立法目的", headings[0].content)
        self.assertEqual("第二条 本法任务", headings[1].content)
        self.assertTrue(paragraphs[0].content.startswith("第一条"))
        self.assertNotIn("北京京师律师事务所", paragraphs[0].content)
        self.assertIn("第一条 立法目的", document.outline)
        self.assertIn("第二条 本法任务", document.outline)


if __name__ == "__main__":
    unittest.main()
