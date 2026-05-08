#!/usr/bin/env python3
"""CLI query script for the General Methods Knowledge Base.

Queries a built SQLite database produced by build_knowledge_base().

Usage:
    python query_kb.py --sqlite-path path/to/kb.sqlite --query "western blot protocol"
    python query_kb.py --sqlite-path path/to/kb.sqlite --category animal_experiment
    python query_kb.py --sqlite-path path/to/kb.sqlite --recent-only --query "flow cytometry"
    python query_kb.py --sqlite-path path/to/kb.sqlite --animal-subcategory dosing
    python query_kb.py --sqlite-path path/to/kb.sqlite --omics-subcategory transcriptomics
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_SRC = (_HERE / ".." / ".." / "src").resolve()
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from researchos_learning_engine.general_methods_kb.query_service import (
    get_evidence_for_paper,
    get_record,
    list_animal_experiment_records,
    list_omics_records,
    query_by_category,
    query_by_keyword,
    query_operation_reference,
    query_recent_five_years,
)


def _print_results(results, verbose=False):
    if not results:
        print("No results found.")
        return
    print(f"Found {len(results)} result(s):\n")
    for i, r in enumerate(results, 1):
        print(f"--- Result {i} ---")
        print(f"  Paper ID:   {r.get('paper_id', '')}")
        print(f"  Title:      {r.get('title', '')}")
        print(f"  Journal:    {r.get('journal', '')} ({r.get('year', '')})")
        print(f"  DOI:        {r.get('doi', 'N/A')}")
        print(f"  Source:     {r.get('source_family', '')} / {r.get('source_journal_group', '')}")
        print(f"  Category:   {r.get('method_category', '')}")
        subcats = r.get("method_subcategories", [])
        if subcats:
            print(f"  Subcategories: {', '.join(subcats)}")
        print(f"  Role:       {r.get('article_role', '')}")
        print(f"  Confidence: {r.get('confidence_score', 0):.3f}")
        val = r.get("methodological_learning_value_cn", "") or ""
        if val:
            print(f"  Learning Value: {val[:120]}")
        if verbose:
            qc = r.get("quality_control_points", [])
            if qc:
                print(f"  QC Points:  {'; '.join(qc[:5])}")
            ops = r.get("operation_reference_points", [])
            if ops:
                print(f"  Operation Ref Points: {'; '.join(ops[:5])}")
            ev_count = len(r.get("evidence_items", []))
            if ev_count:
                print(f"  Evidence Items: {ev_count}")
            questions = r.get("researchos_trigger_questions", [])
            if questions:
                print(f"  Trigger Qs: {'; '.join(questions[:3])}")
        print()


def _pretty(result):
    return json.dumps(result, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Query a built General Methods Knowledge Base.",
    )
    parser.add_argument(
        "--sqlite-path", required=True,
        help="Path to the built SQLite database",
    )
    parser.add_argument(
        "--query", default="",
        help="Free-text keyword query",
    )
    parser.add_argument(
        "--category", default=None,
        help="Filter by method category (e.g. animal_experiment, western_blot)",
    )
    parser.add_argument(
        "--recent-only", action="store_true",
        help="Only return recent (2021+) papers",
    )
    parser.add_argument(
        "--animal-subcategory", default=None,
        help="Filter animal experiment records by subcategory (e.g. dosing, tissue_collection)",
    )
    parser.add_argument(
        "--omics-subcategory", default=None,
        help="Filter omics records by subcategory (e.g. transcriptomics, metabolomics)",
    )
    parser.add_argument(
        "--paper-id", default=None,
        help="Get a single record by paper ID",
    )
    parser.add_argument(
        "--evidence-for", default=None,
        help="Get evidence items for a paper ID",
    )
    parser.add_argument(
        "--operation-ref", default=None,
        help="Search operation reference points by task description",
    )
    parser.add_argument(
        "--limit", type=int, default=10,
        help="Max results (default: 10)",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Show detailed output including QC, ops, evidence counts",
    )
    parser.add_argument(
        "--json", action="store_true",
        help="Output raw JSON instead of formatted text",
    )

    args = parser.parse_args()

    db_path = args.sqlite_path
    if not Path(db_path).is_file():
        print(f"Error: database not found: {db_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Single record lookup
        if args.paper_id:
            r = get_record(db_path, args.paper_id)
            if args.json:
                print(_pretty(r))
            elif r:
                _print_results([r], args.verbose)
            else:
                print(f"No record found for paper_id: {args.paper_id}")
            return

        # Evidence lookup
        if args.evidence_for:
            items = get_evidence_for_paper(db_path, args.evidence_for)
            if args.json:
                print(_pretty(items))
            elif items:
                print(f"Evidence items for {args.evidence_for}:\n")
                for j, it in enumerate(items, 1):
                    print(f"  {j}. [{it['evidence_type']}] {it['claim'][:100]}")
                    print(f"     Quote: {it['short_quote'][:80]}")
                    print(f"     Section: {it['section']} | Confidence: {it['confidence']}")
                    print()
            else:
                print(f"No evidence items for paper_id: {args.evidence_for}")
            return

        # Subcategory queries
        if args.animal_subcategory:
            results = list_animal_experiment_records(
                db_path, subcategory=args.animal_subcategory, limit=args.limit,
            )
        elif args.omics_subcategory:
            results = list_omics_records(
                db_path, subcategory=args.omics_subcategory, limit=args.limit,
            )
        elif args.operation_ref:
            results = query_operation_reference(
                db_path, task_description=args.operation_ref,
                category=args.category, limit=args.limit,
            )
        elif args.recent_only:
            results = query_recent_five_years(
                db_path, category=args.category, limit=args.limit,
            )
        elif args.category:
            results = query_by_category(db_path, args.category, limit=args.limit)
        else:
            results = query_by_keyword(db_path, args.query, limit=args.limit)

        if args.json:
            print(_pretty(results))
        else:
            _print_results(results, args.verbose)

    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Query error: {type(e).__name__}: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
