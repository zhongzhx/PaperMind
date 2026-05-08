"""SQLite storage adapter (minimal implementation).

Provides relational persistence for the Learning Engine.
Can be replaced by the main ResearchOS database adapter later.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from researchos_learning_engine.domain.schemas import (
    ConsolidationResult,
    EvidenceGraphEdge,
    MemoryRecord,
    ResearchPattern,
)


class SQLiteStorageAdapter:
    """SQLite-backed storage for the Learning Engine.

    Uses a single database file with separate tables for each
    data type. JSON serialization is used for complex nested fields.
    """

    def __init__(self, db_path: str = "data/learning_engine.db") -> None:
        self.db_path = str(Path(db_path))
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_conn()
        try:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS memories (
                    memory_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_memories_project ON memories(project_id);

                CREATE TABLE IF NOT EXISTS patterns (
                    pattern_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_patterns_project ON patterns(project_id);

                CREATE TABLE IF NOT EXISTS edges (
                    edge_id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_edges_project ON edges(project_id);

                CREATE TABLE IF NOT EXISTS consolidations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id TEXT NOT NULL,
                    data TEXT NOT NULL,
                    created_at TEXT DEFAULT (datetime('now'))
                );
                CREATE INDEX IF NOT EXISTS idx_consolidations_project
                    ON consolidations(project_id);

                CREATE TABLE IF NOT EXISTS raw_store (
                    key TEXT PRIMARY KEY,
                    data TEXT NOT NULL,
                    updated_at TEXT DEFAULT (datetime('now'))
                );
                """
            )
            conn.commit()
        finally:
            conn.close()

    # --- Memory ---

    def save_memory(self, memory: MemoryRecord) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO memories (memory_id, project_id, data)
                   VALUES (?, ?, ?)""",
                (memory.memory_id, memory.project_id, json.dumps(memory.to_dict(), default=str)),
            )
            conn.commit()
        finally:
            conn.close()

    def load_memories(self, project_id: str | None = None) -> list[MemoryRecord]:
        conn = self._get_conn()
        try:
            if project_id:
                rows = conn.execute(
                    "SELECT data FROM memories WHERE project_id = ?", (project_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT data FROM memories").fetchall()
            return [MemoryRecord.from_dict(json.loads(r["data"])) for r in rows]
        finally:
            conn.close()

    # --- Patterns ---

    def save_pattern(self, pattern: ResearchPattern) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO patterns (pattern_id, project_id, data)
                   VALUES (?, ?, ?)""",
                (pattern.pattern_id, pattern.project_id, json.dumps(pattern.to_dict(), default=str)),
            )
            conn.commit()
        finally:
            conn.close()

    def load_patterns(self, project_id: str | None = None) -> list[ResearchPattern]:
        conn = self._get_conn()
        try:
            if project_id:
                rows = conn.execute(
                    "SELECT data FROM patterns WHERE project_id = ?", (project_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT data FROM patterns").fetchall()
            return [ResearchPattern.from_dict(json.loads(r["data"])) for r in rows]
        finally:
            conn.close()

    # --- Edges ---

    def save_edge(self, edge: EvidenceGraphEdge) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO edges (edge_id, project_id, data)
                   VALUES (?, ?, ?)""",
                (edge.edge_id, edge.project_id, json.dumps(edge.to_dict(), default=str)),
            )
            conn.commit()
        finally:
            conn.close()

    def load_edges(self, project_id: str | None = None) -> list[EvidenceGraphEdge]:
        conn = self._get_conn()
        try:
            if project_id:
                rows = conn.execute(
                    "SELECT data FROM edges WHERE project_id = ?", (project_id,)
                ).fetchall()
            else:
                rows = conn.execute("SELECT data FROM edges").fetchall()
            return [EvidenceGraphEdge.from_dict(json.loads(r["data"])) for r in rows]
        finally:
            conn.close()

    # --- Consolidation ---

    def save_consolidation_result(self, result: ConsolidationResult) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT INTO consolidations (project_id, data)
                   VALUES (?, ?)""",
                (result.project_id, json.dumps(result.to_dict(), default=str)),
            )
            conn.commit()
        finally:
            conn.close()

    def load_latest_consolidation(
        self, project_id: str
    ) -> ConsolidationResult | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                """SELECT data FROM consolidations
                   WHERE project_id = ?
                   ORDER BY id DESC LIMIT 1""",
                (project_id,),
            ).fetchone()
            if row:
                return ConsolidationResult.from_dict(json.loads(row["data"]))
            return None
        finally:
            conn.close()

    # --- Raw ---

    def save_raw(self, key: str, data: Any) -> None:
        conn = self._get_conn()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO raw_store (key, data)
                   VALUES (?, ?)""",
                (key, json.dumps(data, default=str)),
            )
            conn.commit()
        finally:
            conn.close()

    def load_raw(self, key: str) -> Any | None:
        conn = self._get_conn()
        try:
            row = conn.execute(
                "SELECT data FROM raw_store WHERE key = ?", (key,)
            ).fetchone()
            if row:
                return json.loads(row["data"])
            return None
        finally:
            conn.close()
