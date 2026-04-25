from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

try:
    from fastapi.testclient import TestClient
except ModuleNotFoundError:  # pragma: no cover - depends on local test environment.
    TestClient = None

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.main import create_app
from agentic_knowledge_platform.types import DocumentIngestRequest


@unittest.skipIf(TestClient is None, "FastAPI test client is not available")
class StreamApiTests(unittest.TestCase):
    def test_rag_stream_endpoint_emits_meta_and_done_events(self) -> None:
        container = build_container()
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="legal-demo",
                content=(
                    "## 抢劫罪\n"
                    "抢劫通常强调暴力、胁迫或者其他足以压制反抗的方法。\n\n"
                    "## 抢夺罪\n"
                    "抢夺通常是乘人不备公然夺取财物，不以暴力压制反抗为核心。"
                ),
                source="unit",
                modality="markdown",
                tenant_id="demo",
            )
        )
        app = create_app(container)
        client = TestClient(app)

        with client.stream(
            "POST",
            "/rag/query/stream",
            json={"question": "抢劫与抢夺的区别", "tenant_id": "demo", "top_k": 8},
        ) as response:
            lines = [json.loads(line) for line in response.iter_lines() if line]

        self.assertEqual(response.status_code, 200)
        self.assertGreaterEqual(len(lines), 2)
        self.assertEqual("meta", lines[0]["type"])
        self.assertEqual("done", lines[-1]["type"])
        self.assertIn("result", lines[-1])
        self.assertIn("answer_sections", lines[-1]["result"])


if __name__ == "__main__":
    unittest.main()
