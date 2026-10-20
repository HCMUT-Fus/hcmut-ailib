# Final Defence – Speaking Plan and Q&A Script

**Coordinator:** Nguyễn Phước Bảo Phú · **Format:** about 15-minute presentation and live demo, followed by committee Q&A · **Backup:** pre-recorded 3–5 min demo video (`v1.0.0`), offline copy of the slides and the index.

> Fill in the bracketed values `[…]` from `reports/final_evaluation.pdf` before rehearsal. Never quote a number that is not in the final report.

## 1. Speaking split (target 15:00)

| Time | Speaker | Content | Slides |
| :--- | :--- | :--- | :---: |
| 0:00–1:30 | **Nguyễn Phước Bảo Phú** | Opening, team and roles; the problem (vocabulary mismatch in OPAC) with a concrete failing keyword query | 1–3 |
| 1:30–4:00 | **Nguyễn Phước Bảo Phú** | Constraints and criteria; options A/B/C; weighted matrix (4.40 vs 3.85 vs 2.90); four-layer architecture | 4–7 |
| 4:00–6:30 | **Từ Công Phú** | Data: arXiv API, rate limit, stratified sample (4 categories × 5 years × 50), schema and normalisation; embeddings (MiniLM, 384-d, title + abstract); ChromaDB cosine/HNSW; indexing time | 8–10 |
| 6:30–10:30 | **Nguyễn Vi Kiên** | Live demo: natural-language query → filters → result card → full abstract → copy citation → find similar → About tab; then the SUS results | 11–13 |
| 10:30–13:30 | **Trần Kiện Đông** | Evaluation: benchmark design, MRR/P@5 vs BM25, latency table; ethics and legal (CC0 metadata, linking, PDPL, AI Law, GPLv3 compatibility, bias) | 14–17 |
| 13:30–15:00 | **Nguyễn Phước Bảo Phú** | Limitations, future work (multilingual, hybrid, full-text with licence checks), professional lessons, thanks | 18–19 |

**Hand-off phrases** (keep transitions short):

- Bảo Phú → Công Phú: "…so the architecture starts with data. Công Phú."
- Công Phú → Kiên: "…with the index built, let's see it in action. Kiên."
- Kiên → Đông: "…but does it actually find the right papers? Đông."
- Đông → Bảo Phú: "…which brings us to what we would improve next."

**Demo fallback:** if the live app fails within 30 seconds, Kiên switches to the backup video at the same step without apologising at length.

## 2. Q&A allocation

| Topic area | Primary | Backup |
| :--- | :--- | :--- |
| Design process, architecture, teamwork | Bảo Phú | Đông |
| Data, embeddings, vector DB, scaling | Công Phú | Bảo Phú |
| UI/UX, usability study | Kiên | Bảo Phú |
| Evaluation, testing, ethics, law, licences | Đông | Công Phú |

## 3. Anticipated questions and suggested answers

### Design and architecture

**Q1. Why not just use ChatGPT or another LLM API?**
*Bảo Phú:* Three constraints ruled it out. It has a recurring cost (C1), it sends every query to a third party (privacy), and network round-trips are slow. In our weighted matrix it scored 2.90 against 4.40 for local vector search. LLMs can also hallucinate references, which is a serious risk in an academic tool. Our system only returns papers that actually exist in the index.

**Q2. Why is BM25 not enough? It is the industry standard.**
*Đông:* BM25 is excellent when the user knows the right terms, so we use it as our baseline. Our problem is precisely queries that *don't* share words with the relevant papers. In our benchmark, semantic search achieved MRR 0.911 against 0.693 for BM25. Queries such as "mixing two languages within one conversation", where BM25 finds nothing relevant but we rank *A Survey of Code-switching* first, show the difference. With 30 queries the gap is not yet statistically significant (sign test p = 0.057), and we say so. A hybrid of the two is our main future-work item.

**Q3. Why all-MiniLM-L6-v2 and not a larger or scientific model (e.g., SPECTER, mpnet)?**
*Công Phú:* It fits our hardware constraint. It has about 22 M parameters, 384 dimensions, and is fast on CPU, while still producing good sentence embeddings. Larger models such as mpnet are more accurate but several times slower on CPU. Scientific models like SPECTER are trained on citation data and are a good candidate for future work. Our modular indexer makes the model a single configuration change.

**Q4. Why ChromaDB rather than FAISS?**
*Công Phú:* ChromaDB runs embedded with no server, persists to disk, and supports metadata `where` filters (year, category) together with HNSW search. FAISS is faster at very large scale, but we would have to build metadata storage and filtering ourselves. At 1,000 records, simplicity and correctness matter more than raw speed.

**Q5. How is the score computed? Is 85 % "85 % relevant"?**
*Bảo Phú:* No. We take the cosine similarity between the query and paper embeddings and rescale it as (1 + cos)/2 to [0, 1]. It is a geometric similarity, comparable only within one query, not a probability of relevance. We state this in the About tab.

**Q6. Abstracts can be long. Did you chunk them?**
*Công Phú:* Abstracts are short. The model truncates input beyond 256 word pieces, and almost all title + abstract pairs fit within that limit. Chunking would only be needed for full texts, which we deliberately do not index.

**Q7. How does it scale to 100,000 or 1 million papers?**
*Công Phú:* Embedding is linear in corpus size: 51 s for 1,000 papers on a 2-core laptop CPU, so a million would take hours as a one-off batch job, which is acceptable. HNSW search grows roughly logarithmically, so query latency stays low. Memory for 1 M × 384 float32 vectors is about 1.5 GB. Beyond that we would consider quantisation or a server-mode vector DB. The ingestion stage is limited by the arXiv API rate; for bulk data we would use arXiv's bulk metadata (OAI-PMH) instead of the search API.

### Evaluation

**Q8. Is 30 queries enough? How did you avoid biased ground truth?**
*Đông:* Thirty queries is small but adequate for a course prototype, and is in line with common practice (TREC topic sets are typically 50). We labelled relevance from metadata **before** looking at the system's rankings, [confirm: used two labellers per query], and published the benchmark so others can audit it. We report it as an indicative result, not a general claim.

**Q9. Why MRR? What about recall?**
*Đông:* Our users usually want *one good starting paper* quickly, and MRR measures exactly how high the first relevant result appears. We complement it with Precision@5 for early precision. Recall is hard to measure without exhaustive judgements over all 1,000 papers per query, which is beyond our labelling budget.

**Q10. How did you measure latency, and on what machine?**
*Đông:* After warm-up, we time `search()` with `perf_counter` over 30 queries × 5 rounds and report the mean, median, p95 and maximum: 13.6 / 13.3 / 17.1 / 22.2 ms on an Intel i3-1115G4 (2 cores, 4 threads) with 8 GB RAM. UI latency was measured separately in three browsers. The cold start (model loading) is reported separately, and caching keeps it to a one-time cost.

**Q11. What if you had not reached MRR > 0.7?**
*Đông:* We would report it honestly, together with an error analysis of which queries failed and why (e.g., very short queries, or topics outside the sample). Professional integrity matters more than the number.

### Ethics, law and licensing

**Q12. Are you allowed to store and show arXiv abstracts?**
*Đông:* arXiv dedicates all metadata to the public domain under CC0. We still treat abstracts conservatively. Our use is non-commercial and attributed, which fits the exceptions in Article 25 of the Vietnamese IP Law. We never store or serve PDFs, only link to arXiv, as the arXiv API Terms of Use encourage. We also respect the 3-second rate limit and include arXiv's required acknowledgement.

**Q13. Which Vietnamese laws apply, and did anything change?**
*Đông:* Yes, quite a lot changed. The 2006 IT Law was replaced on 1 July 2026 by the Law on Digital Transformation (148/2025/QH15). Personal data is now governed by the Personal Data Protection Law (91/2025/QH15, in force 1 January 2026). The AI Law (134/2025/QH15) took effect on 1 March 2026, and the 2025 IP amendment (131/2025/QH15) added a research/AI-training provision. Our audit covers all of them and flags which points still need checking against the official texts.

**Q14. Author names are personal data. Is that a problem?**
*Đông:* Author names are personal data, but they were published by the authors for exactly this purpose: being identified and cited. We store names only, do no profiling, log no user queries, and provide a correction or removal channel.

**Q15. Why GPLv3? Can you use Apache-licensed libraries in a GPL project?**
*Bảo Phú:* GPLv3 keeps derivatives open, which suits a university tool. Apache-2.0 is compatible with GPLv3 in one direction: Apache code can be part of a GPLv3 work, but not the reverse. All our dependencies are Apache-2.0, BSD or MIT.

**Q16. What biases does the system have?**
*Đông:* The main biases are the following. The model is English-only, so Vietnamese queries perform poorly. The sample covers four CS categories from 2021–2025, so "no result" does not mean "no research exists". The model's fine-tuning data comes from web communities. We avoid popularity bias by not using citation counts or clicks. All of this is disclosed in the About tab.

### Teamwork and professionalism

**Q17. How did you divide the work, and how did you handle disagreements?**
*Bảo Phú:* Roles and a RACI matrix were defined from Week 1, with one accountable owner per artefact. We used protected branches, PR reviews, CI and weekly Saturday stand-ups with minutes. Technical disagreements were settled with data where possible, for example the feasibility matrix. Otherwise the artefact owner decided, and the rationale was recorded in the minutes.

**Q18. What would you do differently?**
*Bảo Phú:* We would build the benchmark even earlier so that every design change could be measured, and plan a multilingual model from the start for Vietnamese users. *(Each member should prepare one personal lesson as well.)*

**Q19. How do you know it is reproducible?**
*Công Phú:* We pinned the dependencies, committed the dataset, and ran a clean-machine test: clone → `pip install -r requirements.txt` → build index → `streamlit run`. CI also rebuilds and tests on a fresh runner for every PR.

## 4. Rehearsal checklist

- ☐ Two full timed rehearsals (target 14:30 ± 0:30).
- ☐ Every member answers at least 3 questions from this list aloud.
- ☐ Demo laptop: index pre-built, Wi-Fi independent, browser zoom at 125 %, notifications off.
- ☐ Backup video and slides on a USB drive and in the cloud.
