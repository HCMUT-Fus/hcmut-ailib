"""Benchmark HCMUT-AILib against the BM25 baseline.

    python -m src.evaluate --pool      # write the judging pool for the 30 queries
    python -m src.evaluate             # metrics, latency, memory, PCA figure

Results go to reports/results/ and reports/figures/.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import tempfile
import time
from pathlib import Path

from src import indexer, ingest
from src.lexical_baseline import BM25
from src.metrics import evaluate_run, reciprocal_rank
from src.search_engine import SearchEngine

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "tests" / "benchmark_queries.json"
POOL_PATH = ROOT / "tests" / "judging_pool.json"
RESULTS_DIR = ROOT / "reports" / "results"
FIGURES_DIR = ROOT / "reports" / "figures"
POOL_DEPTH = 10
LATENCY_REPEATS = 5


def load_benchmark(path: Path = BENCHMARK) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["queries"]


def qrels(queries: list[dict]) -> dict[str, set[str]]:
    return {q["qid"]: set(q["relevant"]) for q in queries if q.get("relevant")}


def rss_mb() -> float | None:
    try:
        import psutil
    except ImportError:
        return None
    return psutil.Process(os.getpid()).memory_info().rss / 2**20


def runs(engine: SearchEngine, bm25: BM25, queries: list[dict], depth: int):
    semantic = {q["qid"]: [r.paper.id for r in engine.search(q["query"], depth)] for q in queries}
    lexical = {q["qid"]: bm25.search(q["query"], depth) for q in queries}
    return semantic, lexical


def write_pool(engine: SearchEngine, bm25: BM25, queries: list[dict]) -> None:
    """Union of both systems' top results, sorted by id so the judge cannot see the source."""
    papers = {p["id"]: p for p in ingest.load()}
    semantic, lexical = runs(engine, bm25, queries, POOL_DEPTH)
    pool = []
    for q in queries:
        ids = sorted(set(semantic[q["qid"]]) | set(lexical[q["qid"]]))
        pool.append({"qid": q["qid"], "query": q["query"], "candidates": [
            {"id": i, "title": papers[i]["title"], "abstract": papers[i]["abstract"][:600]}
            for i in ids]})
    POOL_PATH.write_text(json.dumps(pool, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"Wrote {sum(len(p['candidates']) for p in pool)} candidates to {POOL_PATH}")


def measure_latency(engine: SearchEngine, queries: list[dict]) -> dict:
    for q in queries[:3]:  # warm-up
        engine.search(q["query"], 10)
    timings = []
    for _ in range(LATENCY_REPEATS):
        for q in queries:
            start = time.perf_counter()
            engine.search(q["query"], 10)
            timings.append(time.perf_counter() - start)
    timings.sort()
    return {
        "n": len(timings),
        "mean_s": statistics.mean(timings),
        "median_s": statistics.median(timings),
        "p95_s": timings[int(0.95 * (len(timings) - 1))],
        "max_s": timings[-1],
    }


def time_index_build(papers: list[dict], model) -> float:
    # Chroma keeps its files open, which blocks deletion on Windows; ignore that.
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        start = time.perf_counter()
        indexer.build_index(papers, Path(tmp) / "index", model=model)
        return time.perf_counter() - start


def plot_embeddings(engine: SearchEngine, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    data = engine.collection.get(include=["embeddings", "metadatas"])
    vectors = np.asarray(data["embeddings"])
    centered = vectors - vectors.mean(axis=0)
    _, singular, vt = np.linalg.svd(centered, full_matrices=False)
    coords = centered @ vt[:2].T
    explained = (singular[:2] ** 2).sum() / (singular ** 2).sum()

    groups = ["cs.CL", "cs.LG", "cs.IR", "cs.AI"]
    labels = [m["primary_category"] if m["primary_category"] in groups else "other"
              for m in data["metadatas"]]
    fig, ax = plt.subplots(figsize=(7, 5.5), dpi=150)
    for group, colour in zip(groups + ["other"],
                             ["#2a6fdb", "#e07b39", "#3a9d5d", "#b8459b", "#9a9a9a"]):
        mask = np.array([label == group for label in labels])
        ax.scatter(coords[mask, 0], coords[mask, 1], s=9, alpha=0.65, c=colour,
                   label=f"{group} ({mask.sum()})", edgecolors="none")
    ax.set_title(f"PCA of 1,000 paper embeddings (2 components, {explained:.1%} variance)")
    ax.set_xlabel("PC 1")
    ax.set_ylabel("PC 2")
    ax.legend(title="primary category", fontsize=8, markerscale=2)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)


def evaluate(engine: SearchEngine, bm25: BM25, queries: list[dict]) -> dict:
    labelled = qrels(queries)
    if not labelled:
        raise SystemExit("No relevance labels in the benchmark; judge the pool first.")
    semantic, lexical = runs(engine, bm25, queries, 10)
    per_query = [{
        "qid": q["qid"], "query": q["query"], "n_relevant": len(labelled[q["qid"]]),
        "rr_semantic": reciprocal_rank(semantic[q["qid"]], labelled[q["qid"]]),
        "rr_bm25": reciprocal_rank(lexical[q["qid"]], labelled[q["qid"]]),
    } for q in queries]
    return {
        "semantic": evaluate_run(semantic, labelled),
        "bm25": evaluate_run(lexical, labelled),
        # Best P@5 any system could reach: queries with < 5 relevant papers cap it.
        "p@5_ceiling": evaluate_run({q: sorted(r) for q, r in labelled.items()}, labelled)["p@5"],
        "per_query": per_query,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pool", action="store_true", help="write the judging pool and exit")
    parser.add_argument("--skip-index-timing", action="store_true")
    args = parser.parse_args()

    queries = load_benchmark()
    papers = ingest.load()
    rss_start = rss_mb()
    start = time.perf_counter()
    engine = SearchEngine()
    startup_s = time.perf_counter() - start
    bm25 = BM25(papers)

    if args.pool:
        write_pool(engine, bm25, queries)
        return

    report = evaluate(engine, bm25, queries)
    report["latency"] = measure_latency(engine, queries)
    report["startup_s"] = startup_s
    report["rss_mb"] = {"before_load": rss_start, "after_queries": rss_mb()}
    if not args.skip_index_timing:
        report["index_build_s"] = time_index_build(papers, engine.model)
    report["environment"] = {
        "python": platform.python_version(),
        "platform": platform.platform(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
    }
    plot_embeddings(engine, FIGURES_DIR / "embedding_pca.png")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / "evaluation.json"
    out.write_text(json.dumps(report, indent=1), encoding="utf-8")
    s, b, lat = report["semantic"], report["bm25"], report["latency"]
    print(f"Semantic  MRR={s['mrr']:.3f}  P@5={s['p@5']:.3f}  R@10={s['recall@10']:.3f}")
    print(f"BM25      MRR={b['mrr']:.3f}  P@5={b['p@5']:.3f}  R@10={b['recall@10']:.3f}")
    print(f"Latency   mean={lat['mean_s'] * 1000:.1f} ms  p95={lat['p95_s'] * 1000:.1f} ms  "
          f"max={lat['max_s'] * 1000:.1f} ms  (startup {startup_s:.1f} s)")
    print(f"RSS       {report['rss_mb']}")
    if "index_build_s" in report:
        print(f"Index build {report['index_build_s']:.1f} s")
    print(f"Saved {out}")


if __name__ == "__main__":
    main()
