from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import _build_embeddings
from agentic_knowledge_platform.core.config import Settings
from agentic_knowledge_platform.services.bootstrap_snapshot import build_snapshot, save_snapshot
from agentic_knowledge_platform.services.chunking import StructureAwareChunker
from agentic_knowledge_platform.services.parsing import MultiModalDocumentParser


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a bootstrap vector snapshot for deployment.")
    parser.add_argument("--paths", required=True, help="Corpus file or directory paths separated by ';'")
    parser.add_argument("--output", required=True, help="Snapshot output path, e.g. examples/legal/law_snapshot.json.gz")
    parser.add_argument("--tenant-id", default="demo", help="Tenant id to stamp into the snapshot")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    settings = Settings(
        bootstrap_knowledge_paths=args.paths,
        bootstrap_tenant_id=args.tenant_id,
    )
    parser = MultiModalDocumentParser()
    chunker = StructureAwareChunker(
        max_chars=settings.chunk_size,
        overlap=settings.chunk_overlap,
    )
    embeddings = _build_embeddings(settings)
    snapshot = build_snapshot(
        parser=parser,
        chunker=chunker,
        embeddings=embeddings,
        path_spec=args.paths,
        tenant_id=args.tenant_id,
        embedding_batch_size=settings.embedding_batch_size,
    )
    target = save_snapshot(snapshot, ROOT / args.output)
    print(
        f"snapshot_ready path={target} documents={len(snapshot['documents'])} chunks={len(snapshot['chunks'])}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
