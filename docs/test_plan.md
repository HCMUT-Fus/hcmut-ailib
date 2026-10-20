# Test Plan

**Owner:** Trần Kiện Đông (QA, Ethics & Compliance Lead) · **Applies to:** v1.0.0 · **Related:** `tests/`, `.github/workflows/`

## 1. Objectives

1. Detect regressions automatically on every pull request (CI smoke tests).
2. Verify that the measurable criteria hold: latency < 1.5 s (K1), MRR > 0.7 (K2), Precision@5 reported (K3), indexing < 3 min (K4).
3. Verify functional requirements FR1–FR10 end to end in Chrome, Firefox and Edge.

## 2. Test levels

| Level | Scope | Tool | When |
| :--- | :--- | :--- | :--- |
| Static | Syntax and import errors across `src/` and `tests/` | `python -m compileall`, linter | Every push / PR (CI) |
| Unit | Data schema, normalisation, citations, keywords, BM25, score normalisation | `pytest` | Every PR (CI) |
| Integration / retrieval | Index build → search → filters → find-similar; 30-query benchmark (MRR, P@5) | `pytest` (`tests/test_retrieval.py`) | Every PR to `develop`/`main` (CI); before release |
| System (manual E2E) | Streamlit UI in real browsers | Checklist (Section 4) | End of W6, before release |
| Performance | Query latency, indexing time, memory | Procedure (Section 5) | W7, before release |
| Usability | SUS with 10–15 students | `docs/usability/sus_survey.md` | W7 |

## 3. CI smoke-test plan

**Trigger:** `push` and `pull_request` on `main` and `develop`. **Runner:** `ubuntu-latest`, Python 3.11 or later, CPU only.

| # | Step | Pass condition |
| :---: | :--- | :--- |
| S1 | Check out the repository; set up Python; `pip install -r requirements.txt` (pip cache enabled) | Installation exits with code 0 |
| S2 | `python -m compileall -q src tests` | No syntax errors |
| S3 | `pytest tests/test_ingest.py` | The dataset has exactly 1,000 records; all required fields are present with the correct types; `id` values are unique and contain no version suffix; dates are ISO `YYYY-MM-DD`; `doi` is a string or null; 200 records per year 2021–2025; every record carries at least one sampled category |
| S4 | Unit tests for citations, keywords, BM25 and score normalisation | All pass; scores lie in [0, 1] |
| S5 | Build the index from the committed JSON (model cached between runs) | The collection count equals 1,000 |
| S6 | `pytest tests/test_retrieval.py` | MRR > 0.7 on the 30-query benchmark; P@5 is computed and printed; filters return only matching records; find-similar excludes the seed |
| S7 | Smoke query latency | Median per-query latency on the CI runner is within the configured bound (tolerant of shared-runner variance; the authoritative latency check is Section 5) |

**Policy:** a pull request may be merged only when every CI step is green. The network is not used in CI except for `pip` and the one-off model download, and the arXiv API is **never** called from CI. Ingestion is tested on the committed dataset and on recorded Atom fixtures.

## 4. Manual E2E cross-browser checklist

Run `streamlit run src/app.py`, then test in the latest stable **Chrome**, **Firefox** and **Edge** on Windows. Mark ✔ (pass), ✘ (fail, then open a GitHub Issue and record its number) or – (not applicable).

| ID | Test case | Expected result | Chrome | Firefox | Edge |
| :--- | :--- | :--- | :---: | :---: | :---: |
| E1 | Load the app | Title, tabs and sidebar render; no error trace | | | |
| E2 | Submit an empty query | Information message; no crash | | | |
| E3 | Query "low resource neural machine translation" | 10 results by default, with scores in descending order | | | |
| E4 | Move the Top-K slider to 1 and then to 20 | Exactly 1 and then 20 results | | | |
| E5 | Set the year range to 2024–2024 | All results dated 2024 | | | |
| E6 | Select cs.IR only | All results include cs.IR | | | |
| E7 | Enter an author substring that matches a known author | Only that author's papers | | | |
| E8 | Combine filters that match nothing | "No papers match" message | | | |
| E9 | Expand the abstract | Full abstract shown; collapses again | | | |
| E10 | Click PDF | arXiv PDF opens in a new tab | | | |
| E11 | Click DOI on a record with a DOI; check a record without one | doi.org opens; button hidden when there is no DOI | | | |
| E12 | Open Cite → BibTeX/APA/IEEE → copy | Clipboard contains a well-formed citation | | | |
| E13 | Click Find similar | Similar tab lists neighbours; the seed is not included | | | |
| E14 | Open the About tab | Score explanation, limitations, licences and arXiv acknowledgement present | | | |
| E15 | Unicode query, e.g. "học máy" (Vietnamese diacritics) | No crash; results returned (quality is expected to be low; this is a known limitation) | | | |
| E16 | Very long query (> 1,000 characters) | No crash; results returned | | | |
| E17 | Switch between light and dark themes | Text and badges remain readable | | | |
| E18 | Resize the browser to 1024 px and to 1366 px wide | Layout usable; no overlapping widgets | | | |
| E19 | Keyboard only: Tab to the query box, Enter to search | Search runs | | | |
| E20 | Restart the app | Second start is fast (cached index); no re-indexing | | | |

Record the tester, date, browser versions and OS in the header of each completed copy of this checklist.

## 5. Latency measurement procedure

**Environment.** Record the CPU model, cores, RAM, OS, Python version and library versions. Close other heavy applications and plug in the laptop's power supply.

1. **Cold start:** time from `streamlit run` until the first results appear (reported separately; not part of K1).
2. **Engine latency (authoritative for K1):** in a single Python process, load the engine once, run 3 warm-up queries, then time each of the 30 benchmark queries with `time.perf_counter()` around `search(query, k=10)`. Repeat 5 rounds, giving 150 measurements.
3. **UI latency:** in each browser, measure the time from pressing Search until the results render, using a stopwatch or DevTools performance trace, for 5 queries. This is reported as indicative only.
4. **Indexing time (K4):** time a full `indexer` run on 1,000 records from scratch.
5. **Memory:** record peak resident memory (RSS) of the engine process with Task Manager or `psutil`.

**Report.** Give the mean, median, p95 and maximum for step 2, and the average for step 3. **Pass criterion:** p95 < 1.5 s and maximum < 1.5 s on the weakest team laptop.

| Round | Mean (s) | Median (s) | p95 (s) | Max (s) |
| :---: | :---: | :---: | :---: | :---: |
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| **All** | | | | |

## 6. Defect management

Each defect becomes a GitHub Issue labelled `bug` with a severity (S1 crash or data loss, S2 wrong results, S3 cosmetic), steps to reproduce, the browser and OS, and a screenshot. S1 and S2 defects block a release. Fixes go through `fix/<name>` branches with a regression test where feasible.

## 7. Exit criteria for v1.0.0

- All CI steps are green on `main`.
- E1–E20 pass in all three browsers, or have documented known limitations.
- K1, K2 and K4 are met, or any miss is documented in the final report with an analysis.
- No open S1 or S2 issues.
