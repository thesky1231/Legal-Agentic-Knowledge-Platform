from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.core.config import Settings


class LocalCorpusBootstrapTests(unittest.TestCase):
    def test_build_container_bootstraps_local_legal_corpus_with_legacy_article_split(self) -> None:
        corpus_file = ROOT / "tests" / "fixtures" / "criminal_law_bootstrap.txt"

        settings = Settings(
            bootstrap_knowledge_paths=str(corpus_file),
            bootstrap_tenant_id="demo",
        )
        container = build_container(settings)

        documents = container.knowledge_base.list_documents(tenant_id="demo")
        self.assertEqual(1, len(documents))
        self.assertEqual("legal_text", documents[0]["modality"])
        self.assertEqual(2, documents[0]["chunk_count"])
        self.assertIn("第一条 立法目的", documents[0]["outline"])

        hits = container.knowledge_base.retrieve("立法目的", tenant_id="demo")
        self.assertGreaterEqual(len(hits), 1)
        self.assertIn("第一条", hits[0].chunk.content)


if __name__ == "__main__":
    unittest.main()
