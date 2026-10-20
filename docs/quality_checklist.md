# CO2001 Deliverables and Quality Checklist

**Owner:** Trần Kiện Đông · Tick an item only when the artefact is merged into `develop`/`main` **and** reviewed by at least one other member. Record the reviewer's initials and the PR number.

## 1. Course milestones

| ✓ | Week | Deliverable | Path | Acceptance criteria | Reviewer / PR |
| :---: | :---: | :--- | :--- | :--- | :--- |
| ☐ | W3 | **Milestone 1 – Outline Report** | `reports/outline_report.pdf` (source `reports/src/outline_report.md`) | Design steps 1–6; weighted matrix with explicit weights; architecture figure; user requirements and UI; WBS; RACI; risks; governance; IEEE references | |
| ☐ | W4 | **Milestone 2 – Ethics & Legal Audit** | `reports/ethics_legal_audit.pdf` | IP and licensing; Vietnamese law (status checked); personal data; arXiv ToU; GPLv3 and dependency licences; AI ethics; ACM mapping; compliance checklist; cited sources | |
| ☐ | W7 | **Milestone 3 – Final Evaluation Report (80 %)** | `reports/final_evaluation.pdf` | Measured latency, MRR, P@5 vs BM25, indexing time, memory, SUS; limitations; scalability; honest reporting of any missed target | |
| ☐ | W8 | **Final defence** | Slides, demo video, `docs/defense/qa_script.md` | 15-minute talk split across 4 members; backup video of 3–5 min; Q&A rehearsed | |

## 2. Engineering artefacts

| ✓ | Item | Path | Acceptance criteria |
| :---: | :--- | :--- | :--- |
| ☐ | Repository structure, branch protection, PR and issue templates | `.github/` | `main`/`develop` protected; templates present |
| ☐ | CI pipeline | `.github/workflows/` | Green on `main`; runs the smoke tests in `docs/test_plan.md` §3 |
| ☐ | Ingestion script | `src/ingest.py` | 3 s rate limit; normalisation as in `docs/data_schema.md` |
| ☐ | Dataset | `data/raw/arxiv_sample_1000.json` | 1,000 unique records; passes `tests/test_ingest.py` |
| ☐ | Indexer and vector store | `src/indexer.py`, `data/processed/vector_index/` | 1,000 vectors, 384-d, cosine; built in < 3 min on CPU |
| ☐ | Search engine | `src/search_engine.py` | Top-k, filters, scores in [0, 1], find-similar |
| ☐ | Citations / keywords / BM25 baseline | `src/citations.py`, `src/keywords.py`, `src/lexical_baseline.py` | Unit-tested |
| ☐ | Streamlit app | `src/app.py` | FR1–FR10; E2E checklist passed |
| ☐ | Benchmark | `tests/test_retrieval.py` | 30 queries with ground truth; MRR > 0.7; P@5 reported |
| ☐ | Pinned dependencies | `requirements.txt` | Exact versions; clean-machine install works |
| ☐ | Licence | `LICENSE` | Full GPLv3 text; README licence section |
| ☐ | Release `v1.0.0` | Git tag + `docs/release_notes_v1.0.0.md` | Tag on `main`; notes published on GitHub |

## 3. Documentation and process evidence

| ✓ | Item | Path |
| :---: | :--- | :--- |
| ☐ | README: badges, screenshots, architecture, 3-step install, usage, authors, licence, arXiv acknowledgement | `README.md` |
| ☐ | Architecture diagram | `docs/architecture.png` |
| ☐ | Concept maps (features, design options) | `docs/mindmaps/` |
| ☐ | Feasibility matrix | `docs/feasibility_matrix.md` |
| ☐ | UI wireframes | `docs/ui_wireframes.md` |
| ☐ | Data schema / dataset card | `docs/data_schema.md` |
| ☐ | Test plan (CI, E2E, latency) and completed E2E checklist | `docs/test_plan.md` |
| ☐ | SUS survey: protocol and results | `docs/usability/sus_survey.md` |
| ☐ | Weekly meeting minutes W1–W8, written from the template within 24 h of each meeting | `docs/meeting_minutes/` |
| ☐ | Peer assessment matrix (completed by all members) | `docs/peer_assessment.md` |
| ☐ | Defence Q&A script | `docs/defense/qa_script.md` |

## 4. Report quality gate (apply to every PDF)

- ☐ Title page: course, faculty, group, members and roles.
- ☐ Table of contents; numbered sections; figures and tables captioned and referenced in the text.
- ☐ Every factual or legal claim is cited; IEEE reference style is consistent; no unverifiable references.
- ☐ Numbers match the code and test outputs (re-run before export).
- ☐ Vietnamese names render with correct diacritics.
- ☐ Spell-check and peer proofreading by a member other than the author.
- ☐ PDF rebuilt from source with `python reports/build_reports.py`.

## 5. Code quality gate (every PR)

- ☐ Linked issue and label; Conventional Commit title.
- ☐ CI green; tests added or updated for the behaviour change.
- ☐ Docstrings on public functions; no dead code or secrets.
- ☐ At least one approval (Đông for tests and quality; Bảo Phú for architecture).
