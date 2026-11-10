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
import numpy as np

ROOT = Path(__file__).resolve().parent.parent
BENCHMARK = ROOT / "tests" / "benchmark_queries.json"
POOL_PATH = ROOT / "tests" / "judging_pool.json"
RESULTS_DIR = ROOT / "reports" / "results"
FIGURES_DIR = ROOT / "reports" / "figures"
POOL_DEPTH = 10
LATENCY_REPEATS = 5

SCIFACT_DIR = ROOT / "data" / "benchmarks" / "scifact"
SCIFACT_URL = "https://public.ukp.informatik.tu-darmstadt.de/thakur/BEIR/datasets/scifact.zip"
SCIFACT_EMB_CACHE = SCIFACT_DIR / "embeddings_minilm.npz"
SCIFACT_INDEX_DIR = ROOT / "data" / "processed" / "scifact_index"


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


def evaluate_scifact(top_k: int = 100, model_name: str = indexer.MODEL_NAME, dim: int = 384) -> dict:
    """Benchmark Semantic, BM25, and Hybrid retrieval against the BEIR SciFact dataset."""
    from beir import util
    from beir.datasets.data_loader import GenericDataLoader
    from beir.retrieval.evaluation import EvaluateRetrieval

    if not SCIFACT_DIR.exists():
        print(f"Downloading SciFact dataset to {SCIFACT_DIR.parent}...", flush=True)
        util.download_and_unzip(SCIFACT_URL, str(SCIFACT_DIR.parent))

    corpus, queries, qrels = GenericDataLoader(str(SCIFACT_DIR)).load(split="test")
    print(f"SciFact: {len(corpus)} documents, {len(queries)} queries, {len(qrels)} judged queries.", flush=True)

    model = indexer.load_model(model_name, dim=dim)

    clean_name = "minilm" if "MiniLM" in model_name else "leaf384"
    emb_cache = SCIFACT_DIR / f"embeddings_{clean_name}.npz"
    index_dir = ROOT / "data" / "processed" / f"scifact_index_{clean_name}"

    # Load or compute embeddings cache
    if emb_cache.exists():
        print(f"Loading precomputed SciFact embeddings from {emb_cache}...", flush=True)
        data = np.load(emb_cache)
        doc_ids = list(data["ids"])
        embeddings = data["embeddings"]
    else:
        print(f"Precomputing SciFact embeddings with {model_name} (dim={dim})...", flush=True)
        doc_ids = list(corpus.keys())
        texts = [f"{corpus[cid]['title']}. {corpus[cid]['text']}".strip() for cid in doc_ids]
        t0 = time.perf_counter()
        embs = model.encode(texts, batch_size=64, show_progress_bar=True, normalize_embeddings=True)
        embeddings = embs.astype(np.float32)
        print(f"Encoded {len(texts)} abstracts in {time.perf_counter() - t0:.1f}s", flush=True)
        np.savez_compressed(emb_cache, ids=np.array(doc_ids), embeddings=embeddings)

    papers = []
    for cid in doc_ids:
        c = corpus[cid]
        papers.append({
            "id": cid,
            "title": c.get("title", ""),
            "abstract": c.get("text", ""),
            "authors": ["SciFact Author"],
            "doi": "",
            "categories": ["cs.AI"],
            "primary_category": "cs.AI",
            "published_date": "2020-01-01",
            "pdf_url": "",
        })

    # Build or verify ChromaDB index
    client = indexer.open_client(index_dir)
    try:
        col = client.get_collection(indexer.COLLECTION)
        if col.count() != len(papers):
            raise ValueError("Size mismatch")
        print(f"Existing SciFact index found ({col.count()} docs).", flush=True)
    except Exception:
        print(f"Building SciFact index at {index_dir}...", flush=True)
        try:
            client.delete_collection(indexer.COLLECTION)
        except Exception:
            pass
        col = client.create_collection(indexer.COLLECTION, metadata={"hnsw:space": "cosine"})
        batch_size = 500
        for i in range(0, len(papers), batch_size):
            p_chunk = papers[i:i + batch_size]
            emb_chunk = embeddings[i:i + batch_size]
            metadatas = [indexer.to_metadata(p) for p in p_chunk]
            col.add(
                ids=[p["id"] for p in p_chunk],
                embeddings=emb_chunk.tolist(),
                documents=[p["abstract"] for p in p_chunk],
                metadatas=metadatas,
            )
        print(f"Indexed {col.count()} documents.", flush=True)

    engine = SearchEngine(index_dir=index_dir, model=model)
    bm25 = BM25(papers)
    engine._bm25 = bm25

    print("\nRunning benchmark on 300 test queries...", flush=True)
    semantic_runs = {}
    lexical_runs = {}
    hybrid_runs = {}
    rerank_runs = {}

    beir_semantic = {}
    beir_lexical = {}
    beir_hybrid = {}
    beir_rerank = {}

    t0 = time.perf_counter()
    for idx, (qid, qtext) in enumerate(queries.items(), 1):
        if idx % 100 == 0 or idx == len(queries):
            print(f"Processed {idx}/{len(queries)} queries...", flush=True)
        s_res = engine.search(qtext, top_k=top_k)
        semantic_runs[qid] = [r.paper.id for r in s_res]
        beir_semantic[qid] = {r.paper.id: r.score for r in s_res}

        b_res = bm25.search(qtext, top_k=top_k)
        lexical_runs[qid] = b_res
        beir_lexical[qid] = {doc_id: float(top_k - rank) for rank, doc_id in enumerate(b_res)}

        h_res = engine.hybrid_search(qtext, top_k=top_k)
        hybrid_runs[qid] = [r.paper.id for r in h_res]
        beir_hybrid[qid] = {r.paper.id: r.score for r in h_res}

        hr_res = engine.hybrid_search(qtext, top_k=top_k, rerank=True)
        rerank_runs[qid] = [r.paper.id for r in hr_res]
        beir_rerank[qid] = {r.paper.id: r.score for r in hr_res}

    total_query_time = time.perf_counter() - t0
    qrels_sets = {qid: set(docs.keys()) for qid, docs in qrels.items()}

    s_metrics = evaluate_run(semantic_runs, qrels_sets)
    b_metrics = evaluate_run(lexical_runs, qrels_sets)
    h_metrics = evaluate_run(hybrid_runs, qrels_sets)
    r_metrics = evaluate_run(rerank_runs, qrels_sets)

    k_vals = [1, 3, 5, 10, 100]
    beir_eval_results = {}
    for name, run_dict in [("bm25", beir_lexical), ("semantic", beir_semantic), ("hybrid", beir_hybrid), ("rerank", beir_rerank)]:
        ndcg, _map, recall, precision = EvaluateRetrieval.evaluate(qrels, run_dict, k_vals)
        beir_eval_results[name] = {"ndcg": ndcg, "map": _map, "recall": recall, "precision": precision}

    report = {
        "dataset": "BEIR-SciFact",
        "n_documents": len(corpus),
        "n_queries": len(queries),
        "total_time_s": total_query_time,
        "avg_latency_ms": (total_query_time / len(queries)) * 1000,
        "metrics_ailib": {
            "bm25": b_metrics,
            "semantic": s_metrics,
            "hybrid": h_metrics,
            "rerank": r_metrics,
        },
        "metrics_beir": beir_eval_results,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out = RESULTS_DIR / f"scifact_evaluation_{clean_name}.json"
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("\n" + "=" * 70, flush=True)
    print("           BEIR-SciFact Retrieval Benchmark Evaluation", flush=True)
    print("=" * 70, flush=True)
    print(f"Corpus: {len(corpus)} scientific papers | Test Queries: {len(queries)}", flush=True)
    print(f"Total time: {total_query_time:.2f} s ({total_query_time / len(queries) * 1000:.1f} ms / query)\n", flush=True)

    print("--- HCMUT-AILib Metrics (Apples-to-Apples with Project Targets) ---", flush=True)
    print(f"BM25 Baseline:       MRR={b_metrics['mrr']:.4f}  P@5={b_metrics['p@5']:.4f}  R@10={b_metrics['recall@10']:.4f}", flush=True)
    print(f"Semantic (Dense):    MRR={s_metrics['mrr']:.4f}  P@5={s_metrics['p@5']:.4f}  R@10={s_metrics['recall@10']:.4f}", flush=True)
    print(f"Hybrid (Dense+BM25): MRR={h_metrics['mrr']:.4f}  P@5={h_metrics['p@5']:.4f}  R@10={h_metrics['recall@10']:.4f}", flush=True)
    print(f"Hybrid + Cross-Enc:  MRR={r_metrics['mrr']:.4f}  P@5={r_metrics['p@5']:.4f}  R@10={r_metrics['recall@10']:.4f}", flush=True)

    print("\n--- BEIR Standard Metrics (nDCG@10, MAP@10, Recall@10) ---", flush=True)
    for label, key in [
        ("BM25 Baseline", "bm25"),
        ("Semantic (Dense)", "semantic"),
        ("Hybrid (Dense+BM25)", "hybrid"),
        ("Hybrid + Cross-Enc", "rerank"),
    ]:
        b = beir_eval_results[key]
        print(f"[{label:20}] nDCG@10={b['ndcg']['NDCG@10']:.4f}  MAP@10={b['map']['MAP@10']:.4f}  Recall@10={b['recall']['Recall@10']:.4f}  P@5={b['precision']['P@5']:.4f}", flush=True)

    print("=" * 70, flush=True)
    print(f"Results saved to {out}", flush=True)
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--pool", action="store_true", help="write the judging pool and exit")
    parser.add_argument("--skip-index-timing", action="store_true")
    parser.add_argument("--scifact", action="store_true", help="evaluate on BEIR SciFact dataset")
    parser.add_argument("--model", type=str, default=indexer.MODEL_NAME, help="Model name or HF ID")
    parser.add_argument("--dim", type=int, default=384, help="Embedding dimension")
    args = parser.parse_args()

    if args.scifact:
        evaluate_scifact(model_name=args.model, dim=args.dim)
        return

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
