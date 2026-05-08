#!/usr/bin/env python3
"""CLI entry point for building the General Methods Knowledge Base.

Usage:
    python build_from_local_folder.py \\
        --input-dir "/path/to/paper/folder" \\
        --output-dir "./kb_output"

Optional flags:
    --recent-year-start 2021     Year threshold for "recent 5 years" (default: 2021)
    --max-papers 10              Limit papers processed (0 = unlimited)
    --allowed-source-families    Comma-separated: Nature,Science,Cell (default: all three)
    --mock-llm                   Ignored (no LLM dependency; kept for interface compat)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure src is on the path
_HERE = Path(__file__).resolve().parent
_SRC = (_HERE / ".." / ".." / "src").resolve()
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from researchos_learning_engine.adapters.llm.mock_llm import MockLLMAdapter
from researchos_learning_engine.general_methods_kb.kb_builder import build_knowledge_base


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build the General Methods Knowledge Base from local paper files.",
    )
    parser.add_argument(
        "--input-dir", required=True,
        help="Directory containing paper files (.txt, .md, .pdf)",
    )
    parser.add_argument(
        "--output-dir", required=True,
        help="Directory for output files",
    )
    parser.add_argument(
        "--recent-year-start", type=int, default=2021,
        help="Year threshold for 'recent 5 years' (default: 2021)",
    )
    parser.add_argument(
        "--max-papers", type=int, default=0,
        help="Max papers to process (0 = unlimited)",
    )
    parser.add_argument(
        "--allowed-source-families", default="Nature,Science,Cell",
        help="Comma-separated list of allowed source families",
    )
    parser.add_argument(
        "--mock-llm", action="store_true",
        help="Use MockLLMAdapter (no real API key needed) for deep learning extraction.",
    )

    args = parser.parse_args()

    input_dir = args.input_dir
    if not Path(input_dir).is_dir():
        print(f"Error: input directory not found: {input_dir}", file=sys.stderr)
        sys.exit(1)

    allowed = [f.strip() for f in args.allowed_source_families.split(",") if f.strip()]

    # Prepare LLM adapter if --mock-llm is set
    llm = MockLLMAdapter() if args.mock_llm else None

    print(f"Building General Methods Knowledge Base...")
    print(f"  Input:  {input_dir}")
    print(f"  Output: {args.output_dir}")
    print(f"  Recent year start: {args.recent_year_start}")
    print(f"  Max papers: {args.max_papers or 'unlimited'}")
    print(f"  Allowed families: {', '.join(allowed)}")
    print(f"  LLM: {'MockLLMAdapter' if llm else 'None (no deep learning)'}")
    print()

    result = build_knowledge_base(
        input_dir=input_dir,
        output_dir=args.output_dir,
        recent_year_start=args.recent_year_start,
        max_papers=args.max_papers,
        allowed_source_families=allowed,
        llm_adapter=llm,
    )

    print("Build complete!")
    print(f"  Build ID:     {result['build_id']}")
    print(f"  Processed:    {result['files_processed']} papers")
    print(f"  Skipped:      {result['files_skipped']}")
    print(f"  Failed:       {result['files_failed']}")
    print(f"  Uncertain:    {result['files_uncertain_source']}")
    print(f"  JSONL:        {result['jsonl_path']}")
    print(f"  SQLite DB:    {result['db_path']}")
    print(f"  Summary:      {result['summary_path']}")
    print(f"  Manifest:     {result.get('manifest_path', 'N/A')}")


if __name__ == "__main__":
    main()
