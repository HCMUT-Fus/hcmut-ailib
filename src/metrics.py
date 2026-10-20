"""Ranking metrics for the retrieval benchmark."""

from __future__ import annotations

from collections.abc import Sequence


def reciprocal_rank(ranked_ids: Sequence[str], relevant: set[str]) -> float:
    """1 / rank of the first relevant result, or 0 if none is retrieved."""
    for rank, paper_id in enumerate(ranked_ids, 1):
        if paper_id in relevant:
            return 1.0 / rank
    return 0.0


def precision_at_k(ranked_ids: Sequence[str], relevant: set[str], k: int = 5) -> float:
    """Fraction of the top-k positions holding relevant papers (missing positions count as misses)."""
    return sum(paper_id in relevant for paper_id in ranked_ids[:k]) / k


def recall_at_k(ranked_ids: Sequence[str], relevant: set[str], k: int = 10) -> float:
    return sum(paper_id in relevant for paper_id in ranked_ids[:k]) / len(relevant) if relevant else 0.0


def mean(values: Sequence[float]) -> float:
    return sum(values) / len(values) if values else 0.0


def evaluate_run(run: dict[str, Sequence[str]], qrels: dict[str, set[str]], k: int = 5) -> dict:
    """Aggregate MRR, P@k and Recall@10 of ``run`` (qid -> ranked ids) against ``qrels``."""
    qids = sorted(qrels)
    return {
        "mrr": mean([reciprocal_rank(run.get(q, []), qrels[q]) for q in qids]),
        f"p@{k}": mean([precision_at_k(run.get(q, []), qrels[q], k) for q in qids]),
        "recall@10": mean([recall_at_k(run.get(q, []), qrels[q], 10) for q in qids]),
        "n_queries": len(qids),
    }
