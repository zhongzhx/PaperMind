"""Recursively scan a local folder for paper files.

Supports .txt, .md, .pdf files. Handles spaces in paths.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterator, List, Tuple


SUPPORTED_EXTENSIONS: Tuple[str, ...] = (".txt", ".md", ".pdf")


def scan_folder(input_dir: str, max_papers: int = 0) -> List[dict]:
    """Recursively scan *input_dir* for supported paper files.

    Returns list of dicts:
        {
            "file_path": str,       # absolute path
            "rel_path": str,        # path relative to input_dir
            "file_name": str,
            "file_stem": str,
            "ext": str,             # lowercase extension
            "parent_dir": str,
            "parent_dir_name": str,
            "size_bytes": int,
        }
    """
    results: List[dict] = []
    input_path = Path(input_dir).resolve()
    if not input_path.is_dir():
        return results

    for entry in sorted(input_path.rglob("*")):
        if not entry.is_file():
            continue
        ext = entry.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        results.append({
            "file_path": str(entry),
            "rel_path": str(entry.relative_to(input_path)),
            "file_name": entry.name,
            "file_stem": entry.stem,
            "ext": ext,
            "parent_dir": str(entry.parent),
            "parent_dir_name": entry.parent.name,
            "size_bytes": entry.stat().st_size,
        })

        if max_papers and len(results) >= max_papers:
            break

    return results


def scan_files_iter(input_dir: str, max_papers: int = 0) -> Iterator[dict]:
    """Generator version of *scan_folder* for memory efficiency."""
    count = 0
    input_path = Path(input_dir).resolve()
    if not input_path.is_dir():
        return

    for entry in sorted(input_path.rglob("*")):
        if not entry.is_file():
            continue
        ext = entry.suffix.lower()
        if ext not in SUPPORTED_EXTENSIONS:
            continue

        yield {
            "file_path": str(entry),
            "rel_path": str(entry.relative_to(input_path)),
            "file_name": entry.name,
            "file_stem": entry.stem,
            "ext": ext,
            "parent_dir": str(entry.parent),
            "parent_dir_name": entry.parent.name,
            "size_bytes": entry.stat().st_size,
        }

        count += 1
        if max_papers and count >= max_papers:
            return
