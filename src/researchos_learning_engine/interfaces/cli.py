"""CLI interface for the Learning Engine.

This is a THIN wrapper around the Python API. No business logic lives here.
It reads JSON input, calls run_sleep_cycle(), and writes JSON output.
"""

from __future__ import annotations

import argparse
import sys

from researchos_learning_engine.domain.schemas import ConsolidationInput
from researchos_learning_engine.interfaces.python_api import run_sleep_cycle
from researchos_learning_engine.utils.json_io import read_json, write_json


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="ResearchOS Learning Engine — memory consolidation CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # consolidate command
    consolidate_parser = subparsers.add_parser(
        "consolidate", help="Run sleep-cycle consolidation"
    )
    consolidate_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to ConsolidationInput JSON file",
    )
    consolidate_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to write ConsolidationResult JSON file",
    )

    # score command (quick memory scoring without full consolidation)
    score_parser = subparsers.add_parser(
        "score", help="Score memory records only"
    )
    score_parser.add_argument(
        "--input",
        "-i",
        required=True,
        help="Path to ConsolidationInput JSON file",
    )
    score_parser.add_argument(
        "--output",
        "-o",
        required=True,
        help="Path to write scored memories JSON",
    )

    return parser


def main() -> None:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    if args.command == "consolidate":
        _run_consolidate(args)
    elif args.command == "score":
        _run_score(args)
    else:
        parser.print_help()
        sys.exit(1)


def _run_consolidate(args: argparse.Namespace) -> None:
    """Read input → consolidate → write output."""
    raw = read_json(args.input)
    input_data = ConsolidationInput.from_dict(raw)
    result = run_sleep_cycle(input_data)
    write_json(args.output, result.to_dict())
    print(f"Consolidation complete. Result written to: {args.output}")


def _run_score(args: argparse.Namespace) -> None:
    """Read input → score memories only → write output."""
    from researchos_learning_engine.application.memory_scoring_service import (
        MemoryScoringService,
    )
    from researchos_learning_engine.domain.scoring import score_and_update_memory

    raw = read_json(args.input)
    input_data = ConsolidationInput.from_dict(raw)

    service = MemoryScoringService()
    scored = service.score_all(input_data.memory_records)

    output = {
        "project_id": input_data.project_id,
        "scored_memories": [m.to_dict() for m in scored],
    }
    write_json(args.output, output)
    print(f"Scoring complete. {len(scored)} memories scored. Result written to: {args.output}")


if __name__ == "__main__":
    main()
