"""Query service for the General Methods Knowledge Base.

Provides SQL-backed search and retrieval across built knowledge bases.
All queries read from an existing SQLite database produced by kb_builder.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

_SEARCH_LIMIT = 20

_RESULT_FIELDS = [
    "title", "journal", "year", "doi",
    "source_family", "source_journal_group",
    "source_tier", "learning_depth", "publication_age_group",
    "is_recent_five_years",
    "method_category", "method_subcategories",
    "article_role", "methodological_learning_value_cn",
    "confidence_score",
]


def _connect(db_path: str) -> sqlite3.Connection:
    path = Path(db_path)
    if not path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _parse_json_list(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    try:
        val = json.loads(raw)
        if isinstance(val, list):
            return val
        return [str(val)]
    except (json.JSONDecodeError, TypeError):
        return [str(raw)] if raw else []


def _deep_field(deep_raw: Optional[str]) -> List[str]:
    """Parse a deep_learning_fields TEXT column that stores a JSON list."""
    return _parse_json_list(deep_raw)


def _build_result(row: sqlite3.Row,
                  evidence: Optional[List[Dict[str, Any]]] = None,
                  deep_row: Optional[sqlite3.Row] = None) -> Dict[str, Any]:
    """Build a structured result dict from a papers + method_records row."""
    result: Dict[str, Any] = {}
    for field in _RESULT_FIELDS:
        if field == "method_subcategories":
            result[field] = _parse_json_list(row["method_subcategories"])
        elif field == "is_recent_five_years":
            result[field] = bool(row["is_recent_five_years"])
        else:
            result[field] = row[field]
    # Add deep learning fields if available
    if deep_row is not None:
        result["operation_reference_points"] = _deep_field(
            deep_row["operation_reference_points"]
        )
        result["quality_control_points"] = _deep_field(
            deep_row["quality_control_points"]
        )
        result["researchos_trigger_questions"] = _deep_field(
            deep_row["researchos_trigger_questions"]
        )
        result["core_protocol_steps"] = _deep_field(
            deep_row["core_protocol_steps"]
        )
    else:
        result["operation_reference_points"] = []
        result["quality_control_points"] = []
        result["researchos_trigger_questions"] = []
        result["core_protocol_steps"] = []
    result["evidence_items"] = evidence or []
    return result


def _fetch_evidence(conn: sqlite3.Connection, paper_id: str) -> List[Dict[str, Any]]:
    cur = conn.execute(
        "SELECT claim, short_quote, section, evidence_type, confidence "
        "FROM evidence_items WHERE paper_id = ? ORDER BY id",
        (paper_id,),
    )
    return [dict(r) for r in cur.fetchall()]


def _fetch_deep(conn: sqlite3.Connection, paper_id: str) -> Optional[sqlite3.Row]:
    cur = conn.execute(
        "SELECT operation_reference_points, quality_control_points, "
        "researchos_trigger_questions, core_protocol_steps "
        "FROM deep_learning_fields WHERE paper_id = ?",
        (paper_id,),
    )
    return cur.fetchone()


def _run_query(
    conn: sqlite3.Connection,
    where_clause: str,
    params: tuple = (),
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    sql = f"""
        SELECT p.*, m.method_subcategories, m.methodological_learning_value_cn
        FROM papers p
        LEFT JOIN method_records m ON p.paper_id = m.paper_id
        WHERE {where_clause}
        ORDER BY p.confidence_score DESC
        LIMIT ?
    """
    cur = conn.execute(sql, params + (limit,))
    results: List[Dict[str, Any]] = []
    for row in cur.fetchall():
        paper_id = row["paper_id"]
        evidence = _fetch_evidence(conn, paper_id)
        deep_row = _fetch_deep(conn, paper_id)
        results.append(_build_result(row, evidence, deep_row))
    return results


# ---------------------------------------------------------------------------
# Public query functions
# ---------------------------------------------------------------------------


def query_by_category(
    db_path: str,
    category: str,
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """Query records by method category (e.g. 'animal_experiment', 'western_blot')."""
    conn = _connect(db_path)
    try:
        return _run_query(conn, "p.method_category = ?", (category,), limit)
    finally:
        conn.close()


def query_by_keyword(
    db_path: str,
    keyword: str,
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """Query records by keyword search across title, journal, category, and learning value."""
    conn = _connect(db_path)
    pattern = f"%{keyword}%"
    try:
        return _run_query(
            conn,
            "(p.title LIKE ? OR p.journal LIKE ? OR p.method_category LIKE ? "
            "OR m.methodological_learning_value_cn LIKE ?)",
            (pattern, pattern, pattern, pattern),
            limit,
        )
    finally:
        conn.close()


def query_recent_five_years(
    db_path: str,
    category: Optional[str] = None,
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """Query records from the recent five years (is_recent_five_years = 1)."""
    conn = _connect(db_path)
    try:
        if category:
            return _run_query(
                conn,
                "p.is_recent_five_years = 1 AND p.method_category = ?",
                (category,),
                limit,
            )
        return _run_query(conn, "p.is_recent_five_years = 1", limit=limit)
    finally:
        conn.close()


def query_operation_reference(
    db_path: str,
    task_description: str,
    category: Optional[str] = None,
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """Search for operation reference points relevant to a task description."""
    conn = _connect(db_path)
    pattern = f"%{task_description}%"
    try:
        sql = """
            SELECT p.*, m.method_subcategories, m.methodological_learning_value_cn,
                   d.operation_reference_points, d.quality_control_points,
                   d.researchos_trigger_questions, d.core_protocol_steps
            FROM papers p
            LEFT JOIN method_records m ON p.paper_id = m.paper_id
            LEFT JOIN deep_learning_fields d ON p.paper_id = d.paper_id
            WHERE (d.operation_reference_points LIKE ?
                   OR d.core_protocol_steps LIKE ?
                   OR m.methodological_learning_value_cn LIKE ?)
        """
        params: List[Any] = [pattern, pattern, pattern]
        if category:
            sql += " AND p.method_category = ?"
            params.append(category)
        sql += " ORDER BY p.confidence_score DESC LIMIT ?"
        params.append(limit)
        cur = conn.execute(sql, params)
        results: List[Dict[str, Any]] = []
        for row in cur.fetchall():
            paper_id = row["paper_id"]
            evidence = _fetch_evidence(conn, paper_id)
            results.append(_build_result(row, evidence, row))
        return results
    finally:
        conn.close()


def get_record(
    db_path: str,
    paper_id: str,
) -> Optional[Dict[str, Any]]:
    """Get a single record by paper_id."""
    conn = _connect(db_path)
    try:
        cur = conn.execute(
            "SELECT p.*, m.method_subcategories, m.methodological_learning_value_cn "
            "FROM papers p LEFT JOIN method_records m ON p.paper_id = m.paper_id "
            "WHERE p.paper_id = ?",
            (paper_id,),
        )
        row = cur.fetchone()
        if row is None:
            return None
        evidence = _fetch_evidence(conn, paper_id)
        deep_row = _fetch_deep(conn, paper_id)
        return _build_result(row, evidence, deep_row)
    finally:
        conn.close()


def get_evidence_for_paper(
    db_path: str,
    paper_id: str,
) -> List[Dict[str, Any]]:
    """Get all evidence items for a specific paper."""
    conn = _connect(db_path)
    try:
        return _fetch_evidence(conn, paper_id)
    finally:
        conn.close()


def list_animal_experiment_records(
    db_path: str,
    subcategory: Optional[str] = None,
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """List animal experiment records, optionally filtered by subcategory."""
    conn = _connect(db_path)
    try:
        if subcategory:
            sub_pattern = f"%{subcategory}%"
            return _run_query(
                conn,
                "p.method_category = 'animal_experiment' AND m.method_subcategories LIKE ?",
                (sub_pattern,),
                limit,
            )
        return _run_query(
            conn, "p.method_category = 'animal_experiment'", limit=limit,
        )
    finally:
        conn.close()


def list_omics_records(
    db_path: str,
    subcategory: Optional[str] = None,
    limit: int = _SEARCH_LIMIT,
) -> List[Dict[str, Any]]:
    """List omics records, optionally filtered by subcategory."""
    conn = _connect(db_path)
    try:
        base_where = (
            "(p.method_category LIKE '%omics%' "
            "OR m.method_subcategories LIKE '%omics%')"
        )
        if subcategory:
            sub_pattern = f"%{subcategory}%"
            return _run_query(
                conn,
                f"{base_where} AND m.method_subcategories LIKE ?",
                (sub_pattern,),
                limit,
            )
        return _run_query(conn, base_where, limit=limit)
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Unified query interface
# ---------------------------------------------------------------------------


def query_general_methods_kb(
    db_path: str,
    query: str,
    category: Optional[str] = None,
    recent_only: bool = False,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Unified query entry point.

    Args:
        db_path: Path to the SQLite database.
        query: Free-text keyword to search for.
        category: Optional method category filter.
        recent_only: If True, only return recent (2021+) papers.
        limit: Maximum number of results.

    Returns:
        List of structured result dicts.
    """
    if recent_only and category:
        return query_recent_five_years(db_path, category=category, limit=limit)
    if category:
        return query_by_category(db_path, category, limit=limit)
    if recent_only:
        return query_recent_five_years(db_path, limit=limit)
    return query_by_keyword(db_path, query, limit=limit)
