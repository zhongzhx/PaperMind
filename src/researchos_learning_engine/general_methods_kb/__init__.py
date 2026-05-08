"""ResearchOS General High-Impact Methods Knowledge Base Builder.

Builds a standalone, structured knowledge base from high-impact
methodological papers (Nature, Science, Cell families).

Public API:
    build_general_methods_kb(input_dir, output_dir, ...)
        Build the full knowledge base from a folder of papers.

    load_general_methods_kb(sqlite_path)
        Load all records from a built SQLite database into dicts.

    query_general_methods_kb(sqlite_path, query, ...)
        Query the knowledge base by keyword, category, or recency.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from researchos_learning_engine.general_methods_kb.kb_builder import build_knowledge_base
from researchos_learning_engine.general_methods_kb.query_service import (
    query_general_methods_kb as _query_internal,
)

__all__ = [
    "build_general_methods_kb",
    "load_general_methods_kb",
    "query_general_methods_kb",
]


def build_general_methods_kb(
    input_dir: str,
    output_dir: str,
    recent_year_start: int = 2021,
    llm=None,
    max_papers: Optional[int] = None,
    overwrite: bool = False,
) -> Dict[str, Any]:
    """Build the General Methods Knowledge Base from a folder of papers.

    Args:
        input_dir: Directory containing paper files (.txt, .md, .pdf).
        output_dir: Directory for output files.
        recent_year_start: Year threshold for "recent" scoring (default 2021).
        llm: Optional LLM adapter for deep learning extraction.
        max_papers: Max papers to process (None = unlimited).
        overwrite: If True, remove existing output dir first.

    Returns:
        Dict with build results summary.
    """
    if overwrite:
        import shutil
        from pathlib import Path
        p = Path(output_dir)
        if p.is_dir():
            shutil.rmtree(str(p))

    return build_knowledge_base(
        input_dir=input_dir,
        output_dir=output_dir,
        recent_year_start=recent_year_start,
        max_papers=max_papers or 0,
        llm_adapter=llm,
    )


def load_general_methods_kb(sqlite_path: str) -> List[Dict[str, Any]]:
    """Load all records from a built SQLite database.

    Args:
        sqlite_path: Path to the SQLite database file.

    Returns:
        List of record dicts with all fields.
    """
    from researchos_learning_engine.general_methods_kb.query_service import (
        query_by_keyword,
    )
    # Use a broad empty-string search to get all records
    return query_by_keyword(sqlite_path, "", limit=999999)


def query_general_methods_kb(
    sqlite_path: str,
    query: str,
    category: Optional[str] = None,
    recent_only: bool = False,
    limit: int = 10,
) -> List[Dict[str, Any]]:
    """Query the knowledge base.

    Args:
        sqlite_path: Path to the built SQLite database.
        query: Free-text keyword to search for.
        category: Optional method category filter.
        recent_only: If True, only return recent (2021+) papers.
        limit: Maximum number of results.

    Returns:
        List of structured result dicts.
    """
    return _query_internal(
        db_path=sqlite_path,
        query=query,
        category=category,
        recent_only=recent_only,
        limit=limit,
    )
