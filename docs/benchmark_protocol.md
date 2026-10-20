# Retrieval Benchmark Protocol

**Files:** [tests/benchmark_queries.json](../tests/benchmark_queries.json) (queries + labels),
[tests/judging_pool.json](../tests/judging_pool.json) (what was judged),
[reports/results/evaluation.json](../reports/results/evaluation.json) (latest results).
**Owner:** Trần Kiện Đông (QA) · **Run:** `python -m src.evaluate` · **Asserted by:** `tests/test_retrieval.py`

## 1. Query construction

1. **Seed sampling.** 30 seed papers were drawn at random from the 1,000-paper dataset with
   `random.seed(2001); random.sample(papers, 60)[:30]`. No paper was hand-picked.
2. **Query writing.** For each seed, one natural-language query was written from its abstract,
   phrased as a researcher's information need and deliberately avoiding the seed's title
   wording where possible (the *vocabulary-mismatch* situation the project targets).
3. **Freeze before running.** All 30 queries were written and saved **before** either retrieval
   system was run, and were not edited afterwards. They must not be tuned to improve scores.

## 2. Relevance judgement (pooling)

1. For each query, the top-10 results of the semantic engine and of the BM25 baseline were
   merged into one pool (500 candidates in total, on average 16.7 per query), sorted by arXiv id
   so the judge could not tell which system retrieved a candidate (`python -m src.evaluate --pool`).
2. Each candidate was judged **binary**: *relevant* if it directly addresses the query's core
   information need, not merely if it shares method words. Rules applied:
   * the subject must match (e.g. Q12 needs *video* privacy, not text privacy);
   * a methodological qualifier in the query may be relaxed when the core topic matches
     (e.g. for Q05, a GNN survey on tabular learning counts; for Q08, topic models count);
   * when the query asks for a survey (Q19), primary-method papers are not relevant.
3. Result: **58 relevant labels**, 1–7 per query (mean 1.93). Every seed is relevant to its query.

> **Provenance and limitation.** The first-pass labels were drafted by an AI coding assistant
> working from titles and abstracts, following the rules above. Before the final report, the QA
> lead must **re-judge every pooled candidate** and record any changes in a commit, so the
> benchmark meets the course requirement of human-annotated ground truth. Pooling means papers
> retrieved by neither system were never judged, so Recall@10 is relative to the pool and
> overstates true recall.

## 3. Metrics

| Metric | Definition | Target |
| --- | --- | --- |
| MRR | mean over queries of 1 / rank of the first relevant result in the top 10 (0 if none) | **> 0.7** |
| P@5 | relevant results in the top 5, divided by 5 | reported; ceiling = mean(min(#relevant, 5)) / 5 = **0.367** |
| Recall@10 | relevant results in the top 10 / #relevant (pool-relative) | reported |
| Latency | wall-clock time of `SearchEngine.search(query, 10)`, embedding + ANN query, 30 queries × 5 repeats after warm-up | **< 1.5 s** |

Because 23 of 30 queries have one or two relevant papers, P@5 cannot exceed 0.367 for *any*
system. The original plan's "Precision@5 > 80%" target is therefore not achievable with this
benchmark and is replaced by the P@5 ceiling ratio (achieved P@5 / ceiling).

## 4. Re-running

```bash
python -m src.indexer        # if the index is missing
python -m src.evaluate       # writes reports/results/evaluation.json and reports/figures/embedding_pca.png
pytest -q -s tests/test_retrieval.py
```

If the dataset is re-ingested, the seed sample changes and the benchmark must be rebuilt
(new queries + new judging).
