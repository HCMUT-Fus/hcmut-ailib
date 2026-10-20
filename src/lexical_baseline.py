"""Okapi BM25 keyword search, used as the lexical baseline in the A/B evaluation."""

from __future__ import annotations

import math
from collections import Counter

from src.keywords import STOPWORDS, tokenize


def analyze(text: str) -> list[str]:
    return [t for t in tokenize(text) if t not in STOPWORDS]


class BM25:
    def __init__(self, papers: list[dict], k1: float = 1.5, b: float = 0.75):
        self.ids = [p["id"] for p in papers]
        self.docs = [Counter(analyze(f"{p['title']} {p['abstract']}")) for p in papers]
        self.lengths = [sum(d.values()) for d in self.docs]
        self.avg_length = sum(self.lengths) / len(self.docs)
        self.k1, self.b = k1, b
        df = Counter(term for doc in self.docs for term in doc)
        n = len(self.docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}

    def scores(self, query: str) -> list[float]:
        terms = [t for t in analyze(query) if t in self.idf]
        result = []
        for doc, length in zip(self.docs, self.lengths):
            norm = self.k1 * (1 - self.b + self.b * length / self.avg_length)
            result.append(sum(self.idf[t] * doc[t] * (self.k1 + 1) / (doc[t] + norm)
                              for t in terms if t in doc))
        return result

    def search(self, query: str, top_k: int = 10) -> list[str]:
        """Return the ids of the ``top_k`` best-matching papers (score > 0)."""
        ranked = sorted(zip(self.scores(query), self.ids), key=lambda x: -x[0])
        return [paper_id for score, paper_id in ranked[:top_k] if score > 0]
