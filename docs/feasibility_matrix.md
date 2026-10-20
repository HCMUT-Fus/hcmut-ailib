# Feasibility Decision Matrix

**Owner:** Trần Kiện Đông (QA, Ethics & Compliance Lead) · **Design step:** 5 (Explore options) · **Used in:** `reports/outline_report.pdf`, Section 6

## 1. Options compared

| Option | Description | Representative stack |
| :--- | :--- | :--- |
| **A – Cloud LLM** | Hosted generative LLM ranks papers or answers questions (retrieval-augmented generation) | OpenAI / Anthropic API |
| **B – Inverted Index** | Local full-text keyword search with BM25 ranking | Apache Lucene / Elasticsearch / `rank-bm25` |
| **C – Local Vector DB** | Local dense embeddings + approximate nearest-neighbour search on cosine similarity | `sentence-transformers` (all-MiniLM-L6-v2) + ChromaDB |

## 2. Criteria and weights

The weights were agreed by consensus **before** any scoring. They sum to 1.00 and are traceable to the project's constraints (C) and criteria (K/O) defined in the outline report.

| Criterion | Weight | Traces to | What a "5" means |
| :--- | :---: | :--- | :--- |
| Financial cost | 0.25 | C1 zero cost | $0, with no recurring fees |
| Semantic retrieval quality | 0.25 | Problem statement, K2 | Handles synonyms and paraphrases robustly |
| Hardware fit (4-core CPU, 8 GB RAM, no GPU) | 0.15 | C2 | Runs comfortably alongside a browser |
| Data privacy & offline operation | 0.15 | C7, NFR2 | No query leaves the machine; works offline |
| Query latency | 0.10 | K1 (< 1.5 s) | Well under 0.5 s |
| Engineering feasibility in 8 weeks | 0.10 | C5 | Team can build, test and explain it within the schedule |

## 3. Scores (1 = poor … 5 = excellent) and weighted totals

| Criterion | Weight | A: Cloud LLM | B: Inverted Index | C: Local Vector DB |
| :--- | :---: | :---: | :---: | :---: |
| Financial cost | 0.25 | 1 (0.25) | 5 (1.25) | 5 (1.25) |
| Semantic retrieval quality | 0.25 | 5 (1.25) | 2 (0.50) | 4 (1.00) |
| Hardware fit | 0.15 | 5 (0.75) | 3 (0.45) | 4 (0.60) |
| Privacy & offline | 0.15 | 1 (0.15) | 5 (0.75) | 5 (0.75) |
| Query latency | 0.10 | 2 (0.20) | 5 (0.50) | 4 (0.40) |
| Engineering feasibility | 0.10 | 3 (0.30) | 4 (0.40) | 4 (0.40) |
| **Weighted total** | **1.00** | **2.90** | **3.85** | **4.40** |

Each cell shows the raw score with the weighted contribution (score × weight) in parentheses.

## 4. Score rationale

| Criterion | A: Cloud LLM | B: Inverted Index | C: Local Vector DB |
| :--- | :--- | :--- | :--- |
| Cost | Pay-per-token; recurring; violates C1 | Open source, $0 | Open source, open model weights, $0 |
| Semantic quality | Best language understanding | Literal term matching only; fails on vocabulary mismatch | Dense embeddings capture synonymy and paraphrase; somewhat weaker than large LLMs |
| Hardware | Computation offloaded to the vendor | Python BM25 is light, but Elasticsearch needs a JVM with a large heap | ~22 M-parameter model, ~90 MB weights; embedding 1,000 abstracts takes minutes on CPU |
| Privacy | Every query is sent to a third party; needs internet | Fully local | Fully local; offline after the one-off model download |
| Latency | Network round-trip plus generation, typically seconds | Milliseconds | Query encoding plus HNSW search, tens to hundreds of ms |
| Feasibility | Simple to call, but API keys, cost control and non-determinism complicate testing | Well understood | Well-documented libraries; high learning value; deterministic and testable |

## 5. Sensitivity analysis

| Weighting scheme | A | B | C | Winner |
| :--- | :---: | :---: | :---: | :---: |
| Agreed weights (above) | 2.90 | 3.85 | **4.40** | C |
| Equal weights (1/6 each) | 2.83 | 4.00 | **4.33** | C |
| Cost-agnostic (cost weight 0; others rescaled to sum to 1) | 3.53 | 3.47 | **4.20** | C |
| Quality-heavy (semantic 0.40, cost 0.20, others 0.10 each) | 3.30 | 3.50 | **4.30** | C |

Option C wins under every scheme tested. The C − B margin equals 2·w(semantic) + 1·w(hardware) − 1·w(latency), so B would win only if latency were weighted more heavily than twice the semantic weight plus the hardware weight. That would contradict the problem statement (vocabulary mismatch). A becomes competitive only if cost and privacy are *both* given zero weight.

## 6. Decision

**Option C (Local Vector DB) is selected.** We keep Option B as an **evaluation baseline**: a BM25 implementation is used to measure how much semantic retrieval improves MRR and Precision@5 on the 30-query benchmark. Hybrid lexical-plus-semantic ranking is recorded as future work.
