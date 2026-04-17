from __future__ import annotations

import sqlite3
import uuid
from collections import deque
from pathlib import Path
from datetime import datetime, timezone
from typing import Protocol

from agentic_knowledge_platform.text import short_snippet
from agentic_knowledge_platform.types import AgentRequest, AgentResponse, RunRecord


class RunStore(Protocol):
    def create_run_id(self) -> str:
        ...

    def save(self, workflow: str, request: AgentRequest, response: AgentResponse) -> RunRecord:
        ...

    def list_runs(self, limit: int = 20, tenant_id: str | None = None) -> list[RunRecord]:
        ...


class InMemoryRunStore:
    def __init__(self, max_runs: int = 200) -> None:
        self.max_runs = max_runs
        self.records: deque[RunRecord] = deque(maxlen=max_runs)

    def create_run_id(self) -> str:
        return f"run-{uuid.uuid4().hex[:10]}"

    def save(
        self,
        workflow: str,
        request: AgentRequest,
        response: AgentResponse,
    ) -> RunRecord:
        record = RunRecord(
            run_id=response.run_id or self.create_run_id(),
            workflow=workflow,
            agent_mode=response.agent_mode,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
            query=request.query,
            grounded=response.grounded,
            citation_count=len(response.citations),
            answer_preview=short_snippet(response.answer, limit=160),
            created_at=datetime.now(timezone.utc),
            review_summary=response.review_summary,
        )
        response.run_id = record.run_id
        self.records.appendleft(record)
        return record

    def list_runs(self, limit: int = 20, tenant_id: str | None = None) -> list[RunRecord]:
        records = list(self.records)
        if tenant_id:
            records = [record for record in records if record.tenant_id == tenant_id]
        return records[:limit]


class SQLiteRunStore:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path
        self.connection = self._connect()
        self._ensure_database()

    def create_run_id(self) -> str:
        return f"run-{uuid.uuid4().hex[:10]}"

    def save(
        self,
        workflow: str,
        request: AgentRequest,
        response: AgentResponse,
    ) -> RunRecord:
        record = RunRecord(
            run_id=response.run_id or self.create_run_id(),
            workflow=workflow,
            agent_mode=response.agent_mode,
            session_id=request.session_id,
            tenant_id=request.tenant_id,
            query=request.query,
            grounded=response.grounded,
            citation_count=len(response.citations),
            answer_preview=short_snippet(response.answer, limit=160),
            created_at=datetime.now(timezone.utc),
            review_summary=response.review_summary,
        )
        response.run_id = record.run_id
        self.connection.execute(
            """
            INSERT INTO runs (
                run_id,
                workflow,
                agent_mode,
                session_id,
                tenant_id,
                query,
                grounded,
                citation_count,
                answer_preview,
                created_at,
                review_summary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record.run_id,
                record.workflow,
                record.agent_mode,
                record.session_id,
                record.tenant_id,
                record.query,
                1 if record.grounded else 0,
                record.citation_count,
                record.answer_preview,
                record.created_at.isoformat(),
                record.review_summary,
            ),
        )
        self.connection.commit()
        return record

    def list_runs(self, limit: int = 20, tenant_id: str | None = None) -> list[RunRecord]:
        query = """
            SELECT
                run_id,
                workflow,
                agent_mode,
                session_id,
                tenant_id,
                query,
                grounded,
                citation_count,
                answer_preview,
                created_at,
                review_summary
            FROM runs
        """
        parameters: list[object] = []
        if tenant_id:
            query += " WHERE tenant_id = ?"
            parameters.append(tenant_id)
        query += " ORDER BY created_at DESC LIMIT ?"
        parameters.append(limit)
        rows = self.connection.execute(query, parameters).fetchall()
        return [self._row_to_record(row) for row in rows]

    def _ensure_database(self) -> None:
        db_file = Path(self.db_path)
        if not self.db_path.startswith("file:") and db_file.parent and str(db_file.parent) not in {"", "."}:
            db_file.parent.mkdir(parents=True, exist_ok=True)
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                workflow TEXT NOT NULL,
                agent_mode TEXT NOT NULL,
                session_id TEXT NOT NULL,
                tenant_id TEXT NOT NULL,
                query TEXT NOT NULL,
                grounded INTEGER NOT NULL,
                citation_count INTEGER NOT NULL,
                answer_preview TEXT NOT NULL,
                created_at TEXT NOT NULL,
                review_summary TEXT
            )
            """
        )
        self.connection.commit()

    def _row_to_record(self, row: sqlite3.Row) -> RunRecord:
        return RunRecord(
            run_id=str(row["run_id"]),
            workflow=str(row["workflow"]),
            agent_mode=str(row["agent_mode"]),
            session_id=str(row["session_id"]),
            tenant_id=str(row["tenant_id"]),
            query=str(row["query"]),
            grounded=bool(row["grounded"]),
            citation_count=int(row["citation_count"]),
            answer_preview=str(row["answer_preview"]),
            created_at=datetime.fromisoformat(str(row["created_at"])),
            review_summary=str(row["review_summary"]) if row["review_summary"] is not None else None,
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(
            self.db_path,
            uri=self.db_path.startswith("file:"),
            check_same_thread=False,
        )
        connection.row_factory = sqlite3.Row
        return connection

    def close(self) -> None:
        self.connection.close()
