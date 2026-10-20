"""Retrieval tests: metrics, filters, and the 30-query MRR / latency benchmark."""

import time

import pytest

from src import indexer
from src.evaluate import load_benchmark, qrels
from src.metrics import evaluate_run, precision_at_k, recall_at_k, reciprocal_rank
from src.search_engine import build_where, normalize_score

MRR_TARGET = 0.7
LATENCY_TARGET_S = 1.5


# --- metrics -----------------------------------------------------------------

def test_reciprocal_rank():
    assert reciprocal_rank(["a", "b", "c"], {"a"}) == 1.0
    assert reciprocal_rank(["a", "b", "c"], {"c", "b"}) == 0.5
    assert reciprocal_rank(["a", "b"], {"z"}) == 0.0
    assert reciprocal_rank([], {"a"}) == 0.0


def test_precision_and_recall():
    ranked = ["a", "x", "b", "y", "c", "d"]
    assert precision_at_k(ranked, {"a", "b", "c", "d"}, 5) == 0.6
    assert precision_at_k(["a"], {"a"}, 5) == 0.2  # short lists are penalized
    assert recall_at_k(ranked, {"a", "b", "z", "w"}, 10) == 0.5


def test_evaluate_run_averages_over_labelled_queries():
    run = {"q1": ["a", "b"], "q2": ["c", "d"]}
    result = evaluate_run(run, {"q1": {"b"}, "q2": {"c"}})
    assert result["mrr"] == pytest.approx(0.75)
    assert result["n_queries"] == 2


def test_normalize_score_bounds():
    assert normalize_score(0.0) == 1.0
    assert normalize_score(1.0) == 0.5
    assert normalize_score(2.0) == 0.0
    assert normalize_score(-1e-7) == 1.0


def test_build_where():
    assert build_where() is None
    assert build_where(categories=["cs.CL"]) == {"cat:cs.CL": True}
    assert build_where((2022, 2023), ["cs.CL", "cs.IR"]) == {"$and": [
        {"year": {"$gte": 2022}}, {"year": {"$lte": 2023}},
        {"$or": [{"cat:cs.CL": True}, {"cat:cs.IR": True}]}]}


def test_benchmark_has_30_labelled_queries():
    queries = load_benchmark()
    assert len(queries) == 30
    assert len({q["qid"] for q in queries}) == 30
    labelled = qrels(queries)
    assert len(labelled) == 30
    assert all(q["seed"] in labelled[q["qid"]] for q in queries)


# --- engine (needs the vector index) ------------------------------------------

@pytest.fixture(scope="module")
def engine():
    if not (indexer.INDEX_DIR / "chroma.sqlite3").exists():
        pytest.skip("vector index not built; run `python -m src.indexer`")
    from src.search_engine import SearchEngine
    return SearchEngine()


def test_index_contains_all_papers(engine):
    assert len(engine) == 1000


def test_search_ranks_by_score(engine):
    results = engine.search("neural machine translation for low-resource languages", top_k=10)
    assert len(results) == 10
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)
    assert all(0.0 <= s <= 1.0 for s in scores)
    assert [r.rank for r in results] == list(range(1, 11))


def test_empty_query_returns_nothing(engine):
    assert engine.search("") == []
    assert engine.search("   ") == []


def test_filters_are_respected(engine):
    results = engine.search("recommendation", top_k=20, year_range=(2022, 2023),
                            categories=["cs.IR"])
    assert results
    for r in results:
        assert 2022 <= r.paper.year <= 2023
        assert "cs.IR" in r.paper.categories


def test_author_filter(engine):
    some_author = engine.search("language models", top_k=1)[0].paper.authors[0]
    results = engine.search("language models", top_k=5, author=some_author.lower())
    assert results
    assert all(some_author.lower() in "; ".join(r.paper.authors).lower() for r in results)


def test_impossible_filter_returns_empty(engine):
    assert engine.search("anything", year_range=(1990, 1991)) == []


def test_similar_excludes_source(engine):
    source = engine.search("graph neural networks", top_k=1)[0].paper
    similar = engine.similar(source.id, top_k=5)
    assert len(similar) == 5
    assert source.id not in {r.paper.id for r in similar}


def test_benchmark_mrr(engine):
    queries = load_benchmark()
    run = {q["qid"]: [r.paper.id for r in engine.search(q["query"], 10)] for q in queries}
    result = evaluate_run(run, qrels(queries))
    print(f"\nMRR={result['mrr']:.3f} P@5={result['p@5']:.3f} R@10={result['recall@10']:.3f}")
    assert result["mrr"] > MRR_TARGET


def test_query_latency(engine):
    queries = load_benchmark()
    engine.search(queries[0]["query"])  # warm-up
    timings = []
    for q in queries:
        start = time.perf_counter()
        engine.search(q["query"], 10)
        timings.append(time.perf_counter() - start)
    assert max(timings) < LATENCY_TARGET_S
