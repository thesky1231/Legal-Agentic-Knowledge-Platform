from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.core.serialization import to_dict
from agentic_knowledge_platform.types import DocumentIngestRequest


def main() -> None:
    container = build_container()
    handbook_path = ROOT / "examples" / "legal" / "legal_assistant_handbook.md"
    content = handbook_path.read_text(encoding="utf-8")
    container.knowledge_base.ingest(
        DocumentIngestRequest(
            title="刑事法律知识助手示例手册",
            content=content,
            source=str(handbook_path),
            tenant_id="demo",
            metadata={"tenant": "demo"},
        )
    )
    result = container.evaluation_service.evaluate_from_file(str(ROOT / "examples" / "eval_dataset.json"))
    print(json.dumps(to_dict(result), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
