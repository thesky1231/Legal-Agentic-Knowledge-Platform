from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.container import build_container
from agentic_knowledge_platform.types import DocumentIngestRequest


class TenantIsolationTests(unittest.TestCase):
    def test_retrieval_filters_by_tenant(self) -> None:
        container = build_container()
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="Tenant A Handbook",
                content=(
                    "The platform uses fallback routing. "
                    "When the primary model fails or is rate limited, the backup-router continues the answer flow. "
                    "Reviewer validation is also available in team mode."
                ),
                source="unit-a",
                tenant_id="tenant-a",
            )
        )
        container.knowledge_base.ingest(
            DocumentIngestRequest(
                title="Tenant B Handbook",
                content="Annual leave policy allows 20 days off every year.",
                source="unit-b",
                tenant_id="tenant-b",
            )
        )

        answer = container.knowledge_base.answer(
            "How does backup-router fallback work when the primary model fails?",
            tenant_id="tenant-a",
        )
        documents = container.knowledge_base.list_documents(tenant_id="tenant-a")

        self.assertTrue(answer.grounded)
        self.assertTrue(all(citation.title == "Tenant A Handbook" for citation in answer.citations))
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["tenant_id"], "tenant-a")


if __name__ == "__main__":
    unittest.main()
