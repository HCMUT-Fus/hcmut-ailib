"""Vector generation and vector storage builder."""

from __future__ import annotations

from typing import Any


def build_vector_index(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Minimal index scaffold storing records in insertion order."""
    return list(records)
