"""ID generation utilities."""

from __future__ import annotations

import uuid


def new_id(prefix: str = "mem") -> str:
    """Generate a unique ID with an optional prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def new_paper_id() -> str:
    return new_id("paper")


def new_pattern_id() -> str:
    return new_id("pat")


def new_memory_id() -> str:
    return new_id("mem")


def new_edge_id() -> str:
    return new_id("edge")


def new_node_id() -> str:
    return new_id("node")
