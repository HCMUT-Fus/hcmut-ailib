"""Cosine similarity and ranking logic."""

from __future__ import annotations

from collections import Counter
from math import sqrt


def _tokenize(text: str) -> list[str]:
    return [token for token in text.lower().split() if token]


def _cosine_similarity(a: str, b: str) -> float:
    va = Counter(_tokenize(a))
    vb = Counter(_tokenize(b))
    dot = sum(va[t] * vb[t] for t in va.keys() & vb.keys())
    na = sqrt(sum(v * v for v in va.values()))
    nb = sqrt(sum(v * v for v in vb.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def search(query: str, records: list[dict[str, object]], top_k: int = 5) -> list[dict[str, object]]:
    scored = []
    for item in records:
        text = f"{item.get('title', '')} {item.get('abstract', '')}"
        score = _cosine_similarity(query, str(text))
        scored.append({"record": item, "score": score})
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:top_k]
