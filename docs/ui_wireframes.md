# UI Wireframes – HCMUT-AILib (Streamlit)

**Owner:** Nguyễn Vi Kiên · **Implements:** FR1–FR10 (outline report, Section 8.3) · **Target:** `src/app.py`

These are low-fidelity layout wireframes. Streamlit's own widgets (slider, multiselect, expander, tabs, `st.code` with copy button) set the final look. Widths are indicative.

## 1. Search page (default tab)

```
+--------------------------+-------------------------------------------------------------------+
| HCMUT-AILib              |  [ Search ]   [ Similar papers ]   [ About ]                       |
| Semantic paper search    |-------------------------------------------------------------------|
|--------------------------|                                                                   |
| FILTERS                  |   Find papers by meaning, not just keywords                       |
|                          |   +-----------------------------------------------------+ +-----+ |
| Results (Top-K)          |   | e.g. "translation for languages with little data"   | |Search| |
| 1 o-------●----------- 20|   +-----------------------------------------------------+ +-----+ |
|            10            |   Try: [graph neural networks for molecules] [RAG evaluation]     |
|                          |        [bias in large language models]                            |
| Publication year         |                                                                   |
| 2021 ●=============● 2025|   10 results · 0.21 s · filters: 2023–2025, cs.CL                 |
|                          |                                                                   |
| Categories               |   +-------------------------------------------------------------+ |
| [x] cs.AI   [x] cs.LG    |   | RESULT CARD  (see Section 2)                                | |
| [x] cs.CL   [x] cs.IR    |   +-------------------------------------------------------------+ |
|                          |   +-------------------------------------------------------------+ |
| Author contains          |   | RESULT CARD                                                 | |
| [ e.g. "Bengio"       ]  |   +-------------------------------------------------------------+ |
|                          |   ...                                                             |
| [ Reset filters ]        |                                                                   |
|--------------------------|                                                                   |
| 1,000 papers indexed     |                                                                   |
| Model: all-MiniLM-L6-v2  |                                                                   |
+--------------------------+-------------------------------------------------------------------+
```

States:

```
Empty query  ->  (i) "Type a research question or topic to start searching."
No results   ->  (!) "No papers match these filters. Try widening the year range or categories."
Loading      ->  (spinner) "Searching 1,000 papers..."
Index missing->  (x) "Vector index not found. Run: python -m src.indexer"   (with docs link)
```

## 2. Result card

```
+--------------------------------------------------------------------------------------------+
| 1. Low-Resource Neural Machine Translation with Cross-Lingual Transfer          [ 87% ]    |
|    J. Nguyen, A. Smith, K. Lee, et al.  ·  2023-05-14  ·  arXiv:2305.01234                 |
|    [cs.CL] [cs.LG]                                    score ████████████████░░░  0.87     |
|                                                                                            |
|    We study translation for language pairs with fewer than 100k parallel sentences and     |
|    show that multilingual pre-training ... (truncated to ~300 characters)                  |
|    v Show full abstract                                                                    |
|                                                                                            |
|    Keywords: low-resource · transfer learning · multilingual · back-translation · BLEU     |
|                                                                                            |
|    [ PDF ↗ ]  [ DOI ↗ ]  [ Find similar ]                                                  |
|    v Cite this paper                                                                       |
|      ( BibTeX | APA | IEEE )                                                               |
|      +--------------------------------------------------------------------------[copy]+    |
|      | @article{nguyen2023lowresource,                                                |    |
|      |   title   = {Low-Resource Neural Machine Translation with ...},                |    |
|      |   author  = {Nguyen, J. and Smith, A. and Lee, K.},                            |    |
|      |   journal = {arXiv preprint arXiv:2305.01234}, year = {2023} }                 |    |
|      +--------------------------------------------------------------------------------+    |
+--------------------------------------------------------------------------------------------+
```

Rules:

- The score is shown both as a number and as a bar, so it is not conveyed by colour alone (NFR5). The tooltip reads "Cosine similarity rescaled to 0–1; compare within this query only."
- The DOI button is hidden when `doi` is null. The PDF button opens `pdf_url` on arXiv in a new tab, and nothing is downloaded by the app.
- Authors are truncated to 3 names followed by "et al."; the full list is shown inside the abstract expander.
- *Find similar* switches to the Similar-papers tab with this paper preselected.
- The example record above is illustrative, not a real paper.

## 3. Similar-papers tab

```
+--------------------------+-------------------------------------------------------------------+
| (same sidebar filters)   |  [ Search ]   [ Similar papers ]   [ About ]                       |
|                          |-------------------------------------------------------------------|
|                          |  Seed paper                                                       |
|                          |  +-------------------------------------------------------------+  |
|                          |  | v Select a paper (type to search titles) ...                |  |
|                          |  +-------------------------------------------------------------+  |
|                          |  Seed: "Low-Resource Neural Machine Translation ..." (2023)       |
|                          |        [cs.CL]  [ PDF ↗ ]                                         |
|                          |                                                                   |
|                          |  Papers most similar to the seed (seed excluded)                  |
|                          |  +-------------------------------------------------------------+  |
|                          |  | RESULT CARD (same component, score = similarity to seed)    |  |
|                          |  +-------------------------------------------------------------+  |
|                          |  ...                                                              |
+--------------------------+-------------------------------------------------------------------+
```

## 4. About tab

```
+----------------------------------------------------------------------------------------------+
|  About HCMUT-AILib                                                                           |
|  ------------------------------------------------------------------------------------------  |
|  What it does   Semantic search over 1,000 arXiv papers (cs.AI, cs.LG, cs.CL, cs.IR,          |
|                 2021–2025, 50 per category per year).                                         |
|  How it works   Title + abstract -> all-MiniLM-L6-v2 (384-d) -> ChromaDB (cosine, HNSW).      |
|                 Your query is embedded the same way; nearest papers are shown.               |
|  The score      (1 + cosine)/2 in [0, 1]. A similarity, not a probability of relevance;      |
|                 compare scores only within one query.                                        |
|  Limitations    English-only model · small sample · abstracts only · no citation counts.     |
|                 Not a substitute for reading the papers.                                     |
|  Privacy        Runs locally. Queries are not logged or sent anywhere.                       |
|  Licences       Code: GNU GPLv3. Metadata: arXiv, CC0 1.0. Papers: their authors' licences;  |
|                 we link to arXiv and do not redistribute full texts.                         |
|  Acknowledgement  "Thank you to arXiv for use of its open access interoperability."          |
|                 This project is not affiliated with or endorsed by arXiv.                    |
|  Team           Nguyễn Phước Bảo Phú · Từ Công Phú · Nguyễn Vi Kiên · Trần Kiện Đông         |
|                 CO2001, Faculty of Computer Science and Engineering, HCMUT                   |
+----------------------------------------------------------------------------------------------+
```

## 5. Interaction flow

```
[Open app] -> [Type query] -> [Results] --(expand)--> [Full abstract]
                                 |   \--(Cite)-----> [Copy BibTeX/APA/IEEE]
                                 |   \--(PDF/DOI)--> [arXiv / doi.org in new tab]
                                 \--(Find similar)--> [Similar-papers tab] -> [Results]
```

The key task (search → open paper → copy citation) takes 3 interactions or fewer (NFR3).
