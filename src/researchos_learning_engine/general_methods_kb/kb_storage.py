"""Storage layer for the General Methods Knowledge Base.

Supports:
  - JSONL output (all method knowledge records)
  - SQLite database (papers, method_records, evidence_items, etc.)
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional

from researchos_learning_engine.general_methods_kb.schemas import (
    BuildRunRecord,
    DeepLearningFields,
    MethodKnowledgeRecord,
)


def save_jsonl(
    records: List[MethodKnowledgeRecord],
    output_path: str,
) -> str:
    """Save method knowledge records as JSONL. Returns the file path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")
    return str(path)


def _create_tables(cur: sqlite3.Cursor) -> None:
    cur.executescript("""
        CREATE TABLE IF NOT EXISTS papers (
            paper_id                 TEXT PRIMARY KEY,
            title                    TEXT,
            year                     INTEGER,
            journal                  TEXT,
            doi                      TEXT,
            source_family            TEXT,
            source_journal_group     TEXT,
            source_type              TEXT,
            source_tier              TEXT,
            journal_tier             TEXT,
            learning_depth           TEXT,
            learning_reason          TEXT,
            is_recent_five_years     INTEGER,
            is_user_provided         INTEGER,
            is_classic_foundational  INTEGER,
            publication_age_group    TEXT,
            method_category          TEXT,
            article_role             TEXT,
            confidence_score         REAL,
            created_at               TEXT
        );

        CREATE TABLE IF NOT EXISTS method_records (
            paper_id          TEXT PRIMARY KEY,
            method_category   TEXT,
            method_subcategories TEXT,
            abstract_summary_cn  TEXT,
            methodological_learning_value_cn TEXT,
            method_scope_cn   TEXT,
            retrieval_keywords_cn TEXT,
            retrieval_keywords_en TEXT,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );

        CREATE TABLE IF NOT EXISTS evidence_items (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id        TEXT,
            claim           TEXT,
            short_quote     TEXT,
            section         TEXT,
            evidence_type   TEXT,
            confidence      REAL,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );

        CREATE TABLE IF NOT EXISTS retrieval_keywords (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            paper_id  TEXT,
            language  TEXT,
            keyword   TEXT,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );

        CREATE TABLE IF NOT EXISTS build_runs (
            build_id                     TEXT PRIMARY KEY,
            started_at                   TEXT,
            completed_at                 TEXT,
            input_dir                    TEXT,
            output_dir                   TEXT,
            total_files_found            INTEGER,
            files_processed              INTEGER,
            files_skipped                INTEGER,
            files_failed                 INTEGER,
            files_uncertain_source       INTEGER,
            files_uncertain_metadata     INTEGER,
            records_by_source_tier       TEXT,
            records_by_publication_age_group TEXT,
            records_by_learning_depth    TEXT,
            records_by_category          TEXT,
            engine_version               TEXT,
            schema_version               TEXT,
            status                       TEXT
        );

        CREATE TABLE IF NOT EXISTS skipped_papers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path  TEXT,
            reason     TEXT,
            skipped_at TEXT
        );

        CREATE TABLE IF NOT EXISTS failed_papers (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path     TEXT,
            error_message TEXT,
            failed_at     TEXT
        );

        CREATE TABLE IF NOT EXISTS deep_learning_fields (
            paper_id                      TEXT PRIMARY KEY,
            high_impact_value_cn          TEXT,
            what_researchos_should_learn_cn TEXT,
            applicable_scenarios_cn       TEXT,
            core_protocol_steps           TEXT,
            critical_parameters           TEXT,
            quality_control_points        TEXT,
            reproducibility_points        TEXT,
            common_pitfalls               TEXT,
            troubleshooting_hints         TEXT,
            data_outputs                  TEXT,
            analysis_workflow             TEXT,
            statistical_design            TEXT,
            figure_logic_patterns         TEXT,
            reporting_checklist           TEXT,
            reusable_research_patterns    TEXT,
            operation_reference_points    TEXT,
            researchos_trigger_questions  TEXT,
            related_methods               TEXT,
            limitations                  TEXT,
            FOREIGN KEY (paper_id) REFERENCES papers(paper_id)
        );
    """)


def save_sqlite(
    records: List[MethodKnowledgeRecord],
    output_path: str,
    build_run: Optional[BuildRunRecord] = None,
    skipped_papers: Optional[List[Dict[str, Any]]] = None,
    failed_papers: Optional[List[Dict[str, Any]]] = None,
) -> str:
    """Save all data to SQLite database. Returns the database file path."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    cur = conn.cursor()
    _create_tables(cur)

    for record in records:
        cur.execute(
            """INSERT OR REPLACE INTO papers
               (paper_id, title, year, journal, doi, source_family,
                source_journal_group, source_type, source_tier, journal_tier,
                learning_depth, learning_reason, is_recent_five_years,
                is_user_provided, is_classic_foundational, publication_age_group,
                method_category, article_role, confidence_score, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.paper_id,
                record.title,
                record.year,
                record.journal,
                record.doi,
                record.source_family,
                record.source_journal_group,
                record.source_type,
                record.source_tier,
                record.journal_tier,
                record.learning_depth,
                record.learning_reason,
                1 if record.is_recent_five_years else 0,
                1 if record.is_user_provided else 0,
                1 if record.is_classic_foundational else 0,
                record.publication_age_group,
                record.method_category,
                record.article_role,
                record.confidence_score,
                "",
            ),
        )

        cur.execute(
            """INSERT OR REPLACE INTO method_records
               (paper_id, method_category, method_subcategories,
                abstract_summary_cn, methodological_learning_value_cn,
                method_scope_cn, retrieval_keywords_cn, retrieval_keywords_en)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                record.paper_id,
                record.method_category,
                json.dumps(record.method_subcategories, ensure_ascii=False),
                record.abstract_summary_cn,
                record.methodological_learning_value_cn,
                record.method_scope_cn,
                json.dumps(record.retrieval_keywords_cn, ensure_ascii=False),
                json.dumps(record.retrieval_keywords_en, ensure_ascii=False),
            ),
        )

        for ev in record.evidence_items:
            cur.execute(
                """INSERT INTO evidence_items
                   (paper_id, claim, short_quote, section, evidence_type, confidence)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (record.paper_id, ev.claim, ev.short_quote,
                 ev.section, ev.evidence_type, ev.confidence),
            )

        for kw in record.retrieval_keywords_cn:
            cur.execute(
                "INSERT INTO retrieval_keywords (paper_id, language, keyword) VALUES (?, 'cn', ?)",
                (record.paper_id, kw),
            )
        for kw in record.retrieval_keywords_en:
            cur.execute(
                "INSERT INTO retrieval_keywords (paper_id, language, keyword) VALUES (?, 'en', ?)",
                (record.paper_id, kw),
            )

        # Insert deep learning fields
        if record.deep_learning is not None:
            dl = record.deep_learning
            _deep_list_fields = [
                "core_protocol_steps", "critical_parameters", "quality_control_points",
                "reproducibility_points", "common_pitfalls", "troubleshooting_hints",
                "data_outputs", "figure_logic_patterns", "reporting_checklist",
                "reusable_research_patterns", "operation_reference_points",
                "researchos_trigger_questions", "related_methods", "limitations",
            ]
            dl_data: Dict[str, str] = {"paper_id": record.paper_id}
            for fname in _deep_list_fields:
                dl_data[fname] = json.dumps(
                    getattr(dl, fname, []), ensure_ascii=False,
                )
            for fname in [
                "high_impact_value_cn", "what_researchos_should_learn_cn",
                "applicable_scenarios_cn", "analysis_workflow", "statistical_design",
            ]:
                dl_data[fname] = getattr(dl, fname, "")

            columns = ", ".join(dl_data.keys())
            placeholders = ", ".join(["?"] * len(dl_data))
            cur.execute(
                f"INSERT OR REPLACE INTO deep_learning_fields ({columns}) VALUES ({placeholders})",
                list(dl_data.values()),
            )

    if build_run:
        cur.execute(
            """INSERT OR REPLACE INTO build_runs
               (build_id, started_at, completed_at, input_dir, output_dir,
                total_files_found, files_processed, files_skipped,
                files_failed, files_uncertain_source, files_uncertain_metadata,
                records_by_source_tier, records_by_publication_age_group,
                records_by_learning_depth, records_by_category,
                engine_version, schema_version, status)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                build_run.build_id,
                build_run.started_at,
                build_run.completed_at,
                build_run.input_dir,
                build_run.output_dir,
                build_run.total_files_found,
                build_run.files_processed,
                build_run.files_skipped,
                build_run.files_failed,
                build_run.files_uncertain_source,
                build_run.files_uncertain_metadata,
                json.dumps(build_run.records_by_source_tier, ensure_ascii=False),
                json.dumps(build_run.records_by_publication_age_group, ensure_ascii=False),
                json.dumps(build_run.records_by_learning_depth, ensure_ascii=False),
                json.dumps(build_run.records_by_category, ensure_ascii=False),
                build_run.engine_version,
                build_run.schema_version,
                build_run.status,
            ),
        )

    if skipped_papers:
        for sp in skipped_papers:
            cur.execute(
                "INSERT INTO skipped_papers (file_path, reason, skipped_at) VALUES (?, ?, ?)",
                (sp.get("file_path", ""), sp.get("reason", ""), sp.get("skipped_at", "")),
            )

    if failed_papers:
        for fp in failed_papers:
            cur.execute(
                "INSERT INTO failed_papers (file_path, error_message, failed_at) VALUES (?, ?, ?)",
                (fp.get("file_path", ""), fp.get("error_message", ""), fp.get("failed_at", "")),
            )

    conn.commit()
    conn.close()
    return str(path)
