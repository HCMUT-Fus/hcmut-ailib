# CLAUDE.md

> **Rule: keep this file current.** Any change to commands, structure, dependencies,
> deployment, or a gotcha you hit must be reflected here in the same change.

## What this is

HCMUT-AILib: a local-first semantic search engine over 1,000 arXiv papers (cs.AI/LG/CL/IR,
2021–2025). CO2001 course project at HCMUT, team of 4 (see README "Team").
Stack: Python 3.12, `sentence-transformers` (`all-MiniLM-L6-v2`, CPU) → ChromaDB (cosine,
HNSW) → Streamlit UI. No paid API, no GPU, no telemetry.

Docs: `README.md` (user-facing), `TCP.md` (handover notes, results, open TODOs),
`PLAN.md` (Vietnamese 8-week plan, team rules §5), `docs/` (design, test plan, protocol).

## Commands (Windows, from repo root)

```bash
python -m venv .venv
.venv/Scripts/pip install torch --index-url https://download.pytorch.org/whl/cpu   # CPU torch FIRST
.venv/Scripts/pip install -r requirements.txt
.venv/Scripts/python -m src.indexer          # build index (~1 min, downloads 90 MB model once)
.venv/Scripts/streamlit run src/app.py       # http://localhost:8501
.venv/Scripts/python -m pytest -q            # 31 tests; retrieval/UI tests skip without index
.venv/Scripts/python -m ruff check src tests --select E9,F   # same lint as CI
.venv/Scripts/python -m src.evaluate         # benchmark → reports/results/evaluation.json
```

Linux/macOS: replace `.venv/Scripts/` with `.venv/bin/`.

## Architecture

| Module | Role |
| --- | --- |
| `src/ingest.py` | arXiv API → `data/raw/arxiv_sample_1000.json` (≥3 s between requests, arXiv ToU) |
| `src/indexer.py` | embeds `"title. abstract"`, writes ChromaDB to `data/processed/vector_index/` |
| `src/search_engine.py` | `SearchEngine.search/similar/get`, `build_where` filters, score = (1+cos)/2 |
| `src/citations.py`, `src/keywords.py` | BibTeX/APA/IEEE; TF-IDF key terms |
| `src/lexical_baseline.py`, `src/metrics.py`, `src/evaluate.py` | BM25 baseline, MRR/P@k, benchmark |
| `src/app.py` | Streamlit UI (tabs: Search, Similar papers, About) |

Invariants:
- Indexer and search must use the same `indexer.MODEL_NAME`; changing it requires a rebuild.
- Category filters rely on boolean metadata keys `cat:<category>` (`indexer.category_key`).
- Author filtering is done in Python after retrieval (Chroma can't substring-match).
- `src/app.py` inserts the repo root into `sys.path`, so `streamlit run src/app.py` works
  from the root; modules import each other as `from src import ...`.
- `tests/benchmark_queries.json` labels are tied to the committed dataset; re-running
  `src.ingest` changes the data and invalidates them.

## Conventions

- Branches: `main` (protected), `develop`, `feat/<member>-<feature>`, `fix/<bug>`; PRs only.
- Commits: Conventional Commits, `type(scope): imperative summary`.
- CI (`.github/workflows/ci.yml`): compileall + ruff, then tests, index build, benchmark
  (MRR > 0.7, latency < 1.5 s), UI tests.
- Pinned versions in `requirements.txt` match the working `.venv` (torch 2.14.1+cpu,
  streamlit 1.66.0, chromadb 1.5.9). Don't bump without re-running the full test suite.
- Streamlit: use `width="stretch"`, not the deprecated `use_container_width`.

## Gotchas

- **Never commit unresolved merge conflicts.** Merge `0ffdc11` committed `<<<<<<< HEAD`
  markers into four `src/` files (a "#TODO" stub branch merged over real code), which broke
  the app with a SyntaxError for everyone who pulled. Before committing a merge, run
  `git grep -nE '^(<<<<<<<|=======|>>>>>>>)( |$)'` and the tests.
- The vector index is git-ignored: every fresh clone must run `python -m src.indexer`
  before the app or the index-dependent tests work.
- Install CPU torch before `requirements.txt`, otherwise Linux pip pulls the multi-GB CUDA build.
- The original dev machine has a nearly full C: drive; TCP.md §3.2 sets `TMP`/`HF_HOME` to
  `G:` and `HF_HUB_OFFLINE=1`. That is machine-specific; other machines don't need it.
- Running Streamlit and the test suite together can exhaust RAM on 8 GB machines (~577 MB RSS each).

## Deployment

Target: Hugging Face Spaces (Docker SDK, free CPU tier). `Dockerfile` installs CPU torch,
builds the index at image build time, and serves Streamlit on port 7860. `.dockerignore`
keeps the venv, caches, local index and large reports out of the image. Lovable cannot host
this (it only builds JS front-ends; no Python/torch runtime). Note: once deployed, queries
go to the server, so the README/About "never leaves your machine" claim applies only to local runs.
