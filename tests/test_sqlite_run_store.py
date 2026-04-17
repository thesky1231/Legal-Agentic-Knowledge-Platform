from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from agentic_knowledge_platform.services.run_store import SQLiteRunStore
from agentic_knowledge_platform.types import AgentRequest, AgentResponse


class SQLiteRunStoreTests(unittest.TestCase):
    def test_sqlite_run_store_persists_across_instances(self) -> None:
        db_uri = "file:sqlite_run_store_test?mode=memory&cache=shared"
        store = SQLiteRunStore(db_path=db_uri)
        reloaded_store = SQLiteRunStore(db_path=db_uri)
        try:
            request = AgentRequest(query="How does fallback work?", tenant_id="tenant-a")
            response = AgentResponse(
                answer="Fallback uses the backup model.",
                grounded=True,
                citations=[],
                steps=[],
                agent_mode="single",
            )
            record = store.save(workflow="unit_sqlite", request=request, response=response)

            rows = reloaded_store.list_runs(limit=5, tenant_id="tenant-a")

            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0].run_id, record.run_id)
            self.assertEqual(rows[0].tenant_id, "tenant-a")
        finally:
            reloaded_store.close()
            store.close()


if __name__ == "__main__":
    unittest.main()
