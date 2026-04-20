from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.demo_ui import load_demo_sample, render_demo_page
from agentic_knowledge_platform.showcase_ui import render_showcase_page


class DemoUiTests(unittest.TestCase):
    def test_demo_sample_loads_legal_content(self) -> None:
        sample = load_demo_sample()
        self.assertEqual(sample["source"], "examples/legal/legal_assistant_handbook.md")
        self.assertTrue(sample["content"].strip())
        self.assertIn("tenant_id", sample)

    def test_demo_page_contains_frontend_hooks(self) -> None:
        html = render_demo_page("Agentic Knowledge Platform")
        self.assertIn("法律知识问答 Agent 平台", html)
        self.assertIn("/agent/team/run", html)
        self.assertIn("Recent Runs", html)

    def test_showcase_page_contains_product_demo_copy(self) -> None:
        html = render_showcase_page("Agentic Knowledge Platform")
        self.assertIn("法律知识助手", html)
        self.assertIn("Legal Knowledge Assistant", html)
        self.assertIn("Grounded Answer", html)
        self.assertIn("生成回答", html)
        self.assertNotIn("API Key", html)
        self.assertNotIn("Tenant ID", html)


if __name__ == "__main__":
    unittest.main()
