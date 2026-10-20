# HCMUT-AILib

[![CI](https://github.com/HCMUT-Fus/hcmut-ailib/actions/workflows/ci.yml/badge.svg)](https://github.com/HCMUT-Fus/hcmut-ailib/actions/workflows/ci.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](LICENSE)
![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)

**A zero-cost, local-first semantic search engine and research assistant for open-access academic papers.**
Built for CO2001 – Professional Skills for Engineers, Faculty of Computer Science and Engineering, HCMUT.

Library catalogues match the exact words you type. HCMUT-AILib matches *meaning*. Ask
"mixing two languages within one conversation" and it finds *A Survey of Code-switching*,
even though the two share almost no words. Everything runs on an ordinary laptop
(no GPU, no paid API, no data leaves your machine).

![Search page](docs/screenshots/search_light.png)

## Features

- **Semantic search** over 1,000 arXiv papers (cs.AI, cs.LG, cs.CL, cs.IR; 2021–2025)
- **Filters**: number of results (1–20), publication year, arXiv category, author
- **Paper cards**: match score, category badges, key terms, abstract, PDF / arXiv / DOI links
- **Find similar papers** for any result
- **One-click citations** in BibTeX, APA 7 and IEEE
- Light and dark themes; no query logging, no telemetry

## Results (v1.0.0)

Measured on a 2-core Intel i3-1115G4 laptop with 8 GB RAM, using a 30-query benchmark
([protocol](docs/benchmark_protocol.md), [raw results](reports/results/evaluation.json)):

| | HCMUT-AILib | BM25 keyword baseline | Target |
| --- | ---: | ---: | ---: |
| Mean Reciprocal Rank | **0.911** | 0.693 | > 0.7 |
| Precision@5 (ceiling 0.367) | **0.327** | 0.207 | reported |
| Query latency (mean / max) | **14 ms / 22 ms** | – | < 1.5 s |
| Index build (1,000 papers) | **51 s** | – | < 3 min |
| Cost | **$0** | | $0 |

The benchmark's relevance labels are a first pass that the QA lead still has to review.
See the [final evaluation report](reports/final_evaluation.pdf) for the method and its limitations.

## Quick start

Requires Python 3.12 and about 1.5 GB of disk space.

```bash
# 1. Install (CPU-only PyTorch, then the rest)
pip install torch --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt

# 2. Build the vector index from the included dataset (~1 min; downloads the 90 MB model once)
python -m src.indexer

# 3. Run the app, then open http://localhost:8501
streamlit run src/app.py
```

<details>
<summary>Other commands</summary>

```bash
python -m src.ingest            # re-download the 1,000-paper sample from arXiv (~2 min, 3 s between requests)
python -m src.evaluate          # benchmark: MRR, P@5, latency, memory, PCA figure
pytest -q                       # 31 tests (retrieval and UI tests need the index)
python reports/build_reports.py # rebuild the PDF reports (needs Microsoft Edge)
python docs/draw_architecture.py
```
</details>

## Architecture

![Architecture](docs/architecture.png)

| Layer | Module | What it does |
| --- | --- | --- |
| Ingestion | [src/ingest.py](src/ingest.py) | arXiv API → normalized JSON ([schema](docs/data_schema.md)) |
| Vector index | [src/indexer.py](src/indexer.py) | `all-MiniLM-L6-v2` embeddings → ChromaDB (cosine, HNSW) |
| Retrieval | [src/search_engine.py](src/search_engine.py) | query embedding, top-k search, filters, find-similar |
| Assistant | [src/citations.py](src/citations.py), [src/keywords.py](src/keywords.py) | citations, key terms |
| Presentation | [src/app.py](src/app.py) | Streamlit dashboard |
| Evaluation | [src/evaluate.py](src/evaluate.py), [src/lexical_baseline.py](src/lexical_baseline.py) | benchmark vs BM25 |

## Repository layout

```
.github/            CI workflow, PR and issue templates
data/raw/           arxiv_sample_1000.json (committed)
data/processed/     vector_index/ (generated, git-ignored)
docs/               architecture, mind maps, wireframes, test plan, benchmark protocol,
                    meeting minutes, usability (SUS) kit, defence Q&A, release notes
reports/            outline_report.pdf (W3), ethics_legal_audit.pdf (W4), final_evaluation.pdf (W7)
src/                application code
tests/              pytest suite + benchmark queries and judging pool
```

## Team

| Member | Role |
| --- | --- |
| Nguyễn Phước Bảo Phú | Project Lead & System Architect |
| Từ Công Phú | Data & Retrieval Engineer |
| Nguyễn Vi Kiên | Frontend & Integration Engineer |
| Trần Kiện Đông | QA, Ethics & Compliance Lead |


## Limitations

- The model is English-only; Vietnamese queries work poorly.
- The sample has 1,000 papers, all submitted in early January of each year. A missing result does not mean the literature does not exist.
- Match scores rank results within one query; they are not comparable across queries.

## License and acknowledgements

Code: [GNU GPLv3](LICENSE). Paper metadata comes from arXiv (metadata CC0 1.0); papers
remain under their authors' licences and are only linked, never redistributed.
Thank you to arXiv for use of its open access interoperability. This project is not
affiliated with or endorsed by arXiv.
