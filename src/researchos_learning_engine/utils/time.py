"""Timestamp utilities."""

from __future__ import annotations

from datetime import datetime, timezone


def now_iso() -> str:
    """Return current UTC time as ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def parse_iso(value: str) -> datetime:
    """Parse an ISO 8601 string to datetime."""
    return datetime.fromisoformat(value)
