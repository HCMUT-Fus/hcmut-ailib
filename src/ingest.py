"""Public API query and JSON normalization helpers."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


REQUIRED_KEYS = ("title", "abstract", "authors", "doi")


def normalize_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = []
    for item in records:
        normalized.append(
            {
                "title": str(item.get("title", "")).strip(),
                "abstract": str(item.get("abstract", "")).strip(),
                "authors": item.get("authors", []) if isinstance(item.get("authors", []), list) else [],
                "doi": str(item.get("doi", "")).strip(),
            }
        )
    return normalized


def load_and_normalize(path: str | Path) -> list[dict[str, Any]]:
    with Path(path).open("r", encoding="utf-8") as file:
        data = json.load(file)
    if not isinstance(data, list):
        raise ValueError("Input JSON must be a list of records")
    return normalize_records(data)
