"""JSON file read/write utilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def read_json(path: str) -> Any:
    """Read and parse a JSON file."""
    with open(path, "r") as f:
        return json.load(f)


def write_json(path: str, data: Any, indent: int = 2) -> None:
    """Write data as JSON to a file, creating parent dirs if needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=indent, default=str)
