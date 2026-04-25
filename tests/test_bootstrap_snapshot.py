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
from agentic_knowledge_platform.services.bootstrap_snapshot import build_snapshot, save_snapshot
from agentic_knowledge_platform.services.chunking import StructureAwareChunker
from agentic_knowledge_platform.services.embeddings import HashEmbeddingService
from agentic_knowledge_platform.services.parsing import MultiModalDocumentParser


class BootstrapSnapshotTests(unittest.TestCase):
    def test_build_container_can_load_precomputed_snapshot(self) -> None:
        corpus_file = ROOT / "tests" / "fixtures" / "criminal_law_bootstrap.txt"
        parser = MultiModalDocumentParser()
        chunker = StructureAwareChunker()
        embeddings = HashEmbeddingService(dimensions=96)

        snapshot = build_snapshot(
            parser=parser,
            chunker=chunker,
            embeddings=embeddings,
            path_spec=str(corpus_file),
            tenant_id="demo",
            embedding_batch_size=8,
        )

        artifacts_dir = ROOT / "test_artifacts"
        artifacts_dir.mkdir(exist_ok=True)
        snapshot_path = artifacts_dir / "bootstrap_snapshot.json.gz"
        try:
            save_snapshot(snapshot, snapshot_path)

            settings = Settings(
                bootstrap_snapshot_path=str(snapshot_path),
                bootstrap_tenant_id="demo",
            )
            container = build_container(settings)

            documents = container.knowledge_base.list_documents(tenant_id="demo")
            self.assertEqual(1, len(documents))
            self.assertEqual(2, documents[0]["chunk_count"])

            hits = container.knowledge_base.retrieve("立法目的", tenant_id="demo")
            self.assertGreaterEqual(len(hits), 1)
        finally:
            if snapshot_path.exists():
                try:
                    snapshot_path.unlink()
                except PermissionError:
                    pass


if __name__ == "__main__":
    unittest.main()
