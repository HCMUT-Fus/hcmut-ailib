<div class="titlepage" markdown="1">

**VIETNAM NATIONAL UNIVERSITY – HO CHI MINH CITY**<br>
**HO CHI MINH CITY UNIVERSITY OF TECHNOLOGY (HCMUT)**<br>
**FACULTY OF COMPUTER SCIENCE AND ENGINEERING**

&nbsp;

Course: **CO2001 – Professional Skills for Engineers**<br>
Class CC02 – Group 13 – Semester 1, Academic Year 2026–2027

&nbsp;

# HCMUT-AILib

**Milestone 2 – Ethics & Legal Audit (Week 4)**

&nbsp;

| | |
| :--- | :--- |
| Report owner | Trần Kiện Đông (QA, Ethics & Compliance Lead) |
| Contributors | Nguyễn Phước Bảo Phú (open-source licensing review), Từ Công Phú (data provenance), Nguyễn Vi Kiên (UI disclosures) |
| Scope | Data, model, software dependencies, application behaviour |
| Legal status checked | October 2026 |

Repository: `github.com/HCMUT-Fus/hcmut-ailib` · Licence: GNU GPLv3

Ho Chi Minh City, 2026

</div>

<div class="toc" markdown="1">

[TOC]

</div>

## Executive Summary

This audit examines whether HCMUT-AILib, a local semantic search engine over the metadata and abstracts of 1,000 arXiv papers, complies with applicable law and meets professional ethical standards. Its main findings are:

1. **Data rights are manageable.** arXiv dedicates *all metadata* to the public domain under CC0 1.0 [1]. The papers themselves remain under the licence each author chose: the arXiv perpetual non-exclusive licence, a Creative Commons licence, or CC0 [1]. HCMUT-AILib stores metadata and abstracts only, never stores or serves PDFs, and links users to arXiv, which is the behaviour arXiv explicitly encourages [2]. Treating abstracts conservatively, as works that may still carry authors' rights, our use falls within the non-commercial research, quotation and attribution conditions of the Vietnamese IP Law (Art. 25, as amended) and the 2025 research/AI-training provision (new Art. 7(5)) [8], [10].
2. **The legal landscape changed during 2025–2026.** The Law on Information Technology No. 67/2006/QH11 named in our project plan was **replaced on 1 July 2026** by the Law on Digital Transformation No. 148/2025/QH15 [5], [6]. Decree 13/2023/ND-CP was **superseded on 1 January 2026** by the Law on Personal Data Protection No. 91/2025/QH15 [12], [13]. Vietnam's first **Law on Artificial Intelligence No. 134/2025/QH15** took effect on 1 March 2026 [15], [16]. The audit therefore assesses the project against both the law in force when it was planned and the law in force as of October 2026.
3. **Personal data is limited** to author names (and affiliations, if present) already published by the authors on arXiv. We process them only to display and cite papers, collect no data from users, and log no queries.
4. **Licences are compatible.** All runtime dependencies use permissive licences (Apache-2.0, BSD, MIT) that may be combined into a GPLv3-licensed work. Apache-2.0 is compatible with GPLv3 in one direction only [20].
5. **The main ethical risks** are representational bias (English-only model, four CS categories, 2021–2025 window), over-trust in similarity scores, and misuse that bypasses scholarly reading. These are mitigated by disclosures in the UI, exact citation export, and transparency about how the score is computed.

The compliance checklist (Section 10) records 21 items: 17 compliant, 4 partially compliant with an action owner, and none non-compliant.

## 1. Scope and Method

**System under audit.** The pipeline is `src/ingest.py` (arXiv API client), `src/indexer.py` (embeddings with `all-MiniLM-L6-v2` into ChromaDB), `src/search_engine.py`, `src/citations.py`, `src/keywords.py`, `src/lexical_baseline.py` and `src/app.py` (Streamlit UI). The dataset is `data/raw/arxiv_sample_1000.json` (fields: id, title, abstract, authors, doi, categories, primary_category, published_date, pdf_url).

**Method.**

1. Data-provenance inventory: what is collected, from where, under which terms.
2. Legal mapping against Vietnamese statutes and the platform terms of use.
3. Licence inventory of every dependency, from package metadata (PyPI and installed distributions) and the model card.
4. Ethical risk analysis using the ACM Code of Ethics [24] as the reference framework.
5. Checklist with status and owners.

Legal facts were verified against official texts where they were accessible, and otherwise against reputable secondary sources (law-firm briefings, official government news). These are cited inline. **This audit is a student engineering assessment, not legal advice.** Where we could not confirm an article number or the exact wording, we say so explicitly.

## 2. Data Inventory

| Data item | Source | Stored? | Purpose | Rights status |
| :--- | :--- | :---: | :--- | :--- |
| Title, categories, dates, arXiv ID, DOI, PDF URL | arXiv API | Yes | Display, filter, cite, link | Metadata: CC0 1.0 [1] |
| Abstract | arXiv API | Yes | Embedding, display, keywords | Covered by arXiv's CC0 metadata dedication [1]; also treated conservatively as an author's work (Section 3.2) |
| Author names | arXiv API | Yes | Display, author filter, citation | CC0 metadata; also *personal data* (Section 5) |
| Full-text PDF | arXiv.org | **No** | Linked only | Author's chosen licence; redistribution needs permission [2] |
| 384-d embedding vectors | Derived locally | Yes | Similarity search | Derived numeric data; not a human-readable copy of the work |
| User queries | User input | **No** (held in memory only for the session) | Search | User's own data; not logged |

## 3. Intellectual Property Analysis

### 3.1 Licensing of arXiv content

arXiv requires every submitter to choose a distribution licence. The options currently offered are CC BY 4.0, CC BY-SA 4.0, CC BY-NC-SA 4.0, CC BY-NC-ND 4.0, the *arXiv.org perpetual, non-exclusive license 1.0*, and CC0 [1]. Separately, arXiv states that "a Creative Commons CC0 1.0 Universal Public Domain Dedication will apply to all metadata" [1]. The API Terms of Use repeat that descriptive metadata may be used under CC0 1.0 [2].

The **arXiv non-exclusive licence** grants arXiv the right to distribute the work. It does not grant third parties any right to redistribute it. The API Terms of Use state that "redistribution of e-prints requires permission from the copyright holder", that users should not store and serve e-prints from their own servers without permission or a licence that allows it, and that linking users to arXiv.org is encouraged [2].

The **CC BY family** permits redistribution with attribution. The BY-SA, BY-NC and BY-ND variants add share-alike, non-commercial and no-derivatives conditions respectively [3]. Because licences vary per paper, and because our pipeline does not record the licence field, we **do not rely on any paper-level CC licence**. Instead we follow the most restrictive common rule: we redistribute no full texts.

### 3.2 Abstracts

Abstracts are literary works written by the authors. arXiv's statement that CC0 applies to "all metadata" [1] is generally understood to cover the abstract, which arXiv distributes as part of each record's metadata through the API and OAI-PMH. However, the licence page does not list the abstract explicitly. We therefore also justify our use independently of CC0:

- **Purpose and nature.** The use is non-commercial, educational and research-oriented. Abstracts are displayed with full attribution (authors, title, arXiv ID, link), and the system's function is to send readers to the original. It does not replace the original.
- **Vietnamese copyright exceptions.** Article 25 of the Law on Intellectual Property (Law No. 50/2005/QH11, amended by Laws No. 36/2009/QH12, 42/2019/QH14 and 07/2022/QH15) lists cases where published works may be used without permission or remuneration, *provided the author's name and the source are cited*. These include copying for personal, non-commercial scientific research or study, and reasonable quotation without distorting the author's meaning for commentary, introduction or illustration [8], [9]. The 2022 amendment restructured Article 25 and conditions the exceptions on not unreasonably prejudicing the normal exploitation of the work (the Berne three-step test). We could not confirm the exact clause numbering after the 2022 and 2025 amendments, so we cite Article 25 as a whole.
- **2025 amendment (research and AI training).** Law No. 131/2025/QH15 (adopted 10 Dec 2025, in force 1 Apr 2026) adds clauses 4 and 5 to Article 7. Commentators report that clause 5 permits organisations and individuals to use texts and data that have been lawfully published and made accessible to the public for scientific research, testing and training of AI systems, provided this does not unreasonably prejudice the legitimate rights and interests of authors and right holders. The Government is to issue detailed conditions [10], [11]. Computing embeddings of lawfully published abstracts for a non-commercial research tool fits this description. *We have read the provision only in secondary sources and through a Vietnamese summary of the text; the wording should be checked against the official gazette, and the implementing decree was not verified.*
- **Fair use.** "Fair use" is a United States doctrine (17 U.S.C. §107). Vietnamese law instead uses the closed list of exceptions in Article 25, so we rely on Article 25, not on fair use.

### 3.3 Linking versus redistribution

HCMUT-AILib stores the PDF *URL* and opens arXiv in the user's browser. It never downloads, caches or serves PDF bytes. Hyperlinking to a lawfully published page is not a reproduction of the work, and arXiv explicitly encourages it [2]. **Conclusion: compliant.** Any future feature that indexes full texts must check each paper's licence and keep only derived data (e.g., embeddings) unless the licence permits redistribution.

### 3.4 Embeddings and derived data

The 384-dimensional vectors are numerical representations computed from the text. They cannot be read as the text, and they are used only for similarity ranking. Under the 2025 Art. 7(5) provision and the research exceptions above, we consider their creation lawful. We regenerate them locally rather than distributing them separately from the CC0 metadata.

### 3.5 Software copyright

Under the IP Law, computer programs are protected as literary works. Our own source code is copyright © 2026 of the four team members and is released under GNU GPLv3 (Section 6). Third-party code is used under its own licences, and their notices are preserved.

## 4. Compliance with Vietnamese Information-Technology and Digital Law

### 4.1 Law on Information Technology No. 67/2006/QH11 (in force until 30 June 2026)

The project plan referred to the 2006 IT Law. Its relevant provisions for this project are:

- **Article 12 (prohibited acts).** It prohibits, among other things, infringing IP rights in IT activities. We avoid this by redistributing no protected full texts (Section 3).
- **Article 21 (collection, processing and use of personal information on the network environment).** Clause 1 requires the data subject's consent to collect, process and use their personal information online "unless otherwise provided by law" [7]. Our only personal data, author names, was published by the authors themselves as part of scholarly publication and is processed solely to identify and cite their works. We collect no information from users.
- **Article 22 (storage and provision of personal information).** It gives individuals rights to inspect, correct or delete their information [7]. Section 5 describes our correction and removal procedure.

### 4.2 Law on Digital Transformation No. 148/2025/QH15 (in force from 1 July 2026)

The National Assembly adopted Law No. 148/2025/QH15 on 11 December 2025, and it entered into force on **1 July 2026**. It **replaces Law No. 67/2006/QH11**, except for the transitional cases in Article 48(1)–(2) (approved programmes and projects already under way) [5], [6]. Decree 224/2026/ND-CP guides its implementation [6]. HCMUT-AILib is a student research prototype, not a regulated digital platform or public service. We found no provision of the new law that imposes registration or licensing duties on such a tool. *We did not have access to an authoritative English text and have not reviewed the law article by article; this conclusion should be re-checked if the system is ever deployed as an HCMUT library service.*

### 4.3 Law on Digital Technology Industry No. 71/2025/QH15

Adopted on 14 June 2025, this law took effect on **1 January 2026**, with some incentive provisions effective from 1 July 2025 [17], [18]. It also amended parts of the 2006 IT Law [6]. It mainly governs digital-technology enterprises, products, incentives and digital assets. It also contains provisions on artificial intelligence; their relationship to the later, dedicated AI Law (Section 4.4) was not analysed in this audit. We identified no obligation for a non-commercial student project.

### 4.4 Law on Artificial Intelligence No. 134/2025/QH15

Vietnam's first AI Law was adopted on 10 December 2025 and took effect on **1 March 2026**. It sets up a risk-based framework, with transitional grace periods for existing systems until 1 March 2027, or 1 September 2027 for the health, education and finance sectors [15], [16]. Key risk-classification criteria and incident thresholds depend on implementing decrees that were still being clarified in commentary at the time of writing [16]. HCMUT-AILib ranks bibliographic records. It does not make decisions about people, generate content, or interact with users as an autonomous agent, so on any reasonable reading it is a **low-risk** system. Even so, the law's general principles (transparency, human oversight, accountability) are good practice, and we adopt them voluntarily: we disclose that results are AI-ranked, explain the score, and present the tool as a decision aid. Because this system serves education, the September 2027 sector date may become relevant if the tool is ever deployed institutionally. *We have not verified the article-level text of Law 134/2025/QH15.*

## 5. Personal Data

**Is personal data processed?** Yes. Author names are information that identifies natural persons. Decree 13/2023/ND-CP classified full name as *basic personal data*. The **Law on Personal Data Protection No. 91/2025/QH15** (adopted 26 Jun 2025, in force **1 January 2026**, guided by Decree 356/2025/ND-CP) superseded Decree 13 [12]–[14] and retains a basic/sensitive distinction. No sensitive personal data is processed.

**Lawful basis and the "public data" question.** Author names are disclosed by the authors themselves as an inherent part of scholarly publication and are released by arXiv as CC0 metadata. Vietnamese commentators warn, however, that *public disclosure does not automatically mean freedom of use* under the new law [14]. We could not verify a specific PDPL article that exempts publicly disclosed data or research use. We therefore apply data-protection principles as if they applied in full:

| Principle | Implementation |
| :--- | :--- |
| Purpose limitation | Names are used only to display authorship, filter by author and generate citations, which is the purpose for which they were published |
| Data minimisation | We store names only: no e-mail addresses, affiliations, ORCID iDs or profiling |
| No profiling | There are no author-level analytics or rankings of people |
| Accuracy and correction | Data is refreshed from arXiv; any author may request correction or removal via a GitHub issue, actioned within 7 days |
| Security and locality | Data stays on the user's machine; there is no server and no transfer to third parties |
| Users' data | Queries are not logged or persisted, and there is no analytics |

The Streamlit framework can collect anonymous usage statistics by default. We disable this in the project configuration (`browser.gatherUsageStats = false`). This is tracked as checklist item P4.

## 6. Open-Source Licensing (GNU GPLv3) and Dependency Compatibility

### 6.1 Obligations under GPLv3

HCMUT-AILib is distributed under GPLv3 [19]. Anyone who conveys the program, in source or object form, must:

1. License the whole work under GPLv3.
2. Provide the corresponding source code.
3. Keep copyright and licence notices and the disclaimer of warranty.
4. Mark modified versions as changed, with a relevant date.
5. Not impose further restrictions, including restrictions through patents.

For the repository this means: the full GPLv3 text in `LICENSE`, a licence statement in `README.md`, copyright headers where practical, and no proprietary components. Running the software privately creates no obligations. GPLv3 is not the AGPL, so offering the app over a network would not by itself trigger source-disclosure duties. However, because the source is public, we satisfy them in any case.

### 6.2 Dependency licence inventory

Licences were taken from PyPI metadata (October 2026), the installed distributions, and the Hugging Face model card.

| Component | Version checked | Licence | Compatible with GPLv3? |
| :--- | :--- | :--- | :---: |
| sentence-transformers | 6.1.0 | Apache-2.0 | Yes (one-way) |
| all-MiniLM-L6-v2 (model weights) | – | Apache-2.0 [21] | Yes (one-way) |
| transformers / huggingface-hub | 5.20.2 / 2.2.0 | Apache-2.0 | Yes (one-way) |
| PyTorch (`torch`) | 2.14.1+cpu | BSD-3-Clause-style main licence; the distribution metadata also lists bundled components under Apache-2.0, BSD-2-Clause, BSL-1.0 and MIT | Yes |
| ChromaDB (`chromadb`) | 1.5.9 | Apache-2.0 | Yes (one-way) |
| Streamlit | 1.66.0 | Apache-2.0 | Yes (one-way) |
| rank-bm25 | 0.2.2 | Apache-2.0 | Yes (one-way) |
| scikit-learn | 1.9.1 | BSD-3-Clause | Yes |
| NumPy | 2.5.4 | BSD-3-Clause (plus 0BSD, MIT, Zlib and CC0 for bundled parts) | Yes |
| pytest (development only) | 9.1.1 | MIT | Yes |
| markdown (report tooling only) | – | BSD-3-Clause | Yes |

**Apache-2.0 and GPL.** The Free Software Foundation considers Apache-2.0 compatible with GPLv3 but *not* with GPLv2 [20]. The direction matters: Apache-2.0 code may be included in a GPLv3 project, and the combined work is then distributed under GPLv3, but GPLv3 code cannot be relicensed under Apache-2.0. Our use is the permitted direction. We must preserve Apache `NOTICE` files and licence texts if we ever *vendor* (copy) these libraries. Installing them through `pip` already satisfies this, because their own distributions carry the notices.

**Training data of the model.** The model card states that `all-MiniLM-L6-v2` was fine-tuned on over one billion sentence pairs drawn from about 20 public datasets, including Reddit comments, S2ORC citation pairs, Stack Exchange, MS MARCO, WikiAnswers and SNLI/MultiNLI [21]. Those datasets carry their own terms. We use only the released weights under Apache-2.0 and do not redistribute the training data. This residual upstream-provenance uncertainty is accepted and disclosed.

## 7. arXiv API Terms of Use

| Requirement [2], [4] | Implementation | Status |
| :--- | :--- | :---: |
| No more than **one request every three seconds**, on a **single connection at a time**, across all machines under our control | `ingest.py` sleeps 3 s between sequential requests; no parallelism; one ingestion run per dataset build | ✔ |
| Acknowledge arXiv: *"Thank you to arXiv for use of its open access interoperability."* | Text shown in the About tab and in `README.md` | ✔ |
| Do not imply endorsement by arXiv; do not use arXiv's names, logos or colours to suggest it | Project name does not contain "arXiv"; no arXiv logo; About tab states that the project is not affiliated with or endorsed by arXiv | ✔ |
| Metadata use under CC0 | Metadata stored and redistributed in the repository dataset | ✔ |
| Do not store or serve e-prints without permission; link to arXiv instead | Links only (Section 3.3) | ✔ |
| Do not circumvent limits with multiple machines | Single machine, single process | ✔ |

## 8. AI Ethics Assessment

### 8.1 Bias and representativeness

- **Language bias.** `all-MiniLM-L6-v2` is an English model [21]. Vietnamese queries, or papers in other languages, will be ranked poorly. This disadvantages users who search in Vietnamese. *Mitigation:* this limitation is stated in the About tab, and a multilingual model (e.g., `paraphrase-multilingual-MiniLM-L12-v2`) is listed as future work.
- **Corpus or coverage bias.** The corpus contains four categories (cs.AI, cs.LG, cs.CL, cs.IR) with 50 papers per category per year for 2021–2025. This stratified design deliberately avoids letting the high-volume cs.LG category dominate. Even so, the system simply cannot find papers outside the sample, and "no result" must not be read as "no such research exists". *Mitigation:* the dataset composition is shown in the About tab.
- **Recency and popularity bias.** We rank purely by semantic similarity, with no citation counts or click-through data. This avoids the rich-get-richer feedback loop of popularity-based ranking. Text-only similarity can still favour papers whose abstracts use mainstream vocabulary, and the fine-tuning data (Reddit, Stack Exchange, MS MARCO) may encode community-specific language patterns.
- **Evaluation bias.** The ground truth for our 30 benchmark queries is labelled by team members, who might favour results they have already seen. *Mitigation:* the labelling protocol requires relevance to be judged from the metadata *before* inspecting system rankings, with disagreements resolved by discussion. The benchmark is published in the repository so others can audit it.

### 8.2 Transparency and explainability

The displayed score is (1 + cos θ)/2 ∈ [0, 1], where θ is the angle between the query and paper embeddings. A score of 0.80 does **not** mean an "80 % probability of relevance". It is a geometric similarity, and scores are only comparable within a single query. The About tab explains this. Results also show categories, dates and keywords so users can judge relevance themselves, and the BM25 comparison in the final report shows where semantic search helps and where it does not.

### 8.3 Human judgement and academic integrity

HCMUT-AILib is a **discovery aid, not a substitute for scholarly reading**. The interface encourages users to open the original paper. It generates no summaries or claims that could be quoted as if they came from the authors, and it produces correctly formatted citations (BibTeX/APA/IEEE) from authoritative metadata. These features encourage proper attribution and reduce citation errors. Users remain responsible for reading and correctly citing what they use, in line with HCMUT academic-integrity rules.

### 8.4 Privacy

The design is privacy-preserving: there is no account, no query logging, no telemetry, and no third-party API at query time. After the one-off model download, the app runs fully offline. This is a key advantage over the cloud-LLM alternative, which was rejected partly because it would send every query to a vendor.

### 8.5 Environmental cost

Training large models has a substantial carbon footprint [23]. Our design reuses a small pre-trained model (about 22 M parameters), performs no training, embeds 1,000 abstracts once in a few minutes on a CPU, and answers queries with a single forward pass. No GPU or data-centre resources are used. The marginal energy cost is negligible compared with the cloud-LLM alternative.

### 8.6 Security and misuse

Inputs are only plain-text queries and filter values. Metadata filters are passed as structured parameters to ChromaDB, not concatenated into query strings, so injection is not possible. Abuse potential is low because the system exposes only public bibliographic data.

## 9. Professional Responsibility: ACM Code of Ethics Mapping

| ACM principle [24] | How HCMUT-AILib addresses it |
| :--- | :--- |
| 1.1 Contribute to society and human well-being | Gives students free, offline access to better literature discovery |
| 1.2 Avoid harm | No redistribution of protected works; no personal profiling; limitations disclosed |
| 1.3 Be honest and trustworthy | Score semantics explained; benchmark results reported honestly, including misses; no claim of arXiv endorsement |
| 1.4 Be fair and take action not to discriminate | Language and coverage bias documented; multilingual model planned |
| 1.5 Respect the work required to produce new ideas and creative works | Attribution on every result; citation export; links to the original; licence-aware design |
| 1.6 Respect privacy | Data minimisation; no query logging; telemetry disabled |
| 2.1 Strive for high quality in processes and products | Code review, CI, tests, benchmark with MRR/P@5 |
| 2.3 Know and respect existing rules | This audit: IP, digital, personal-data and AI law; arXiv ToU; GPLv3 |
| 2.5 Give comprehensive evaluations of systems and their impacts, including risks | Risk register (outline report) and this audit |
| 2.7 Foster public awareness and understanding of computing | About tab explains embeddings and similarity in plain language |
| 3.1 Ensure the public good is the central concern | Open-source release; no commercial use of contributors' data |

In engineering terms, this follows the duty to hold paramount the interests of users and the public, to act within one's competence (we state that the legal analysis is not legal advice), and to be honest about limitations.

## 10. Compliance Checklist

| ID | Item | Status | Owner / Action |
| :--- | :--- | :---: | :--- |
| L1 | Only metadata and abstracts stored; no PDFs stored or served | ✔ Compliant | Công Phú |
| L2 | Every result attributes authors, title and arXiv ID, and links to the source | ✔ Compliant | Kiên |
| L3 | Citation export uses authoritative metadata | ✔ Compliant | Công Phú |
| L4 | arXiv rate limit (≤ 1 request/3 s, single connection) | ✔ Compliant | Công Phú |
| L5 | arXiv acknowledgement in UI and README | ✔ Compliant | Kiên |
| L6 | No implied arXiv endorsement; no arXiv logo | ✔ Compliant | Kiên |
| L7 | Use within IP Law Art. 25 conditions (non-commercial, attributed) | ✔ Compliant | Đông |
| L8 | IP Law Art. 7(5) (Law 131/2025/QH15) research/AI-training conditions | ◐ Partial: wording and implementing decree to be verified against the official gazette | Đông |
| L9 | Digital Transformation Law 148/2025/QH15 reviewed (replaces IT Law 2006) | ◐ Partial: article-level review pending | Đông |
| L10 | AI Law 134/2025/QH15: low-risk self-assessment; transparency disclosures | ◐ Partial: re-assess when risk-classification decrees are final | Đông / Bảo Phú |
| P1 | Personal data limited to published author names | ✔ Compliant | Công Phú |
| P2 | No query logging or user accounts | ✔ Compliant | Bảo Phú |
| P3 | Correction/removal channel for authors (GitHub issue) | ✔ Compliant | Đông |
| P4 | Streamlit usage statistics disabled | ✔ Compliant | Kiên |
| S1 | `LICENSE` contains the full, unmodified GPLv3 text | ✔ Compliant | Bảo Phú |
| S2 | README states the licence and copyright holders | ✔ Compliant | Kiên |
| S3 | All dependency licences compatible with GPLv3 | ✔ Compliant | Bảo Phú |
| S4 | No vendored third-party code without its notices | ✔ Compliant | Bảo Phú |
| E1 | Bias and limitations disclosed in the About tab | ✔ Compliant | Kiên |
| E2 | Score meaning explained | ✔ Compliant | Kiên |
| E3 | Benchmark labelled before system inspection; results reported honestly | ◐ Partial: protocol defined; confirm adherence when the benchmark is frozen (W5) and in the final report | Đông |

## 11. Recommendations

1. **Record the licence of each paper.** Before any full-text feature is added, record each paper's licence (available from the arXiv listing and OAI-PMH `arXivRaw` metadata) and enforce licence-aware processing.
2. **Re-verify the 2025–2026 legislation.** Check Laws 131/2025/QH15, 134/2025/QH15 and 148/2025/QH15, and their implementing decrees, against official texts before any institutional deployment at the HCMUT library, and consult the university's legal office.
3. **Support Vietnamese-language search.** Add a multilingual embedding model so that Vietnamese-speaking users are not disadvantaged, and evaluate it on Vietnamese queries.
4. **Show score context.** Add the rank and a short "why this result" cue, such as matching keywords, next to each score, to reduce over-trust in raw scores.
5. **Keep the privacy-by-default posture.** If deployment adds analytics, obtain explicit consent, perform the impact assessment required by the PDPL, and anonymise queries.
6. **Publish a dataset card.** Document the provenance, licence, sampling design and known biases of `arxiv_sample_1000.json` (started in `docs/data_schema.md`).
7. **Repeat the audit at every major release.** Make it part of the release checklist.

## 12. Conclusion

HCMUT-AILib's design choices are local-first processing, metadata-only storage, linking instead of redistribution, attribution and citation by default, and permissive-licensed dependencies. Together they put the project on a sound legal and ethical footing. The principal open items concern Vietnam's fast-changing legal framework for digital technology, AI and IP. We flag these openly rather than overstate certainty, and we assign each one an owner.

<div class="refs" markdown="1">

## References

[1] arXiv, "License and copyright: Discussion of licenses." [Online]. Available: https://info.arxiv.org/help/license/index.html (accessed Oct. 2026).

[2] arXiv, "Terms of Use for arXiv APIs." [Online]. Available: https://info.arxiv.org/help/api/tou.html (accessed Oct. 2026).

[3] Creative Commons, "About CC licenses." [Online]. Available: https://creativecommons.org/share-your-work/cclicenses/ (accessed Oct. 2026).

[4] arXiv, "arXiv API Access." [Online]. Available: https://info.arxiv.org/help/api/index.html (accessed Oct. 2026).

[5] National Assembly of Vietnam, *Law on Digital Transformation*, No. 148/2025/QH15, Dec. 11, 2025 (effective Jul. 1, 2026). Summary: LuatVietnam, https://luatvietnam.vn/linh-vuc-khac/tai-file-luat-chuyen-doi-so-cua-quoc-hoi-so-148-2025-qh15-186-106067-article.html

[6] Can Tho Department of Justice, "Trách nhiệm của tổ chức, cá nhân trong chuyển đổi số" (on Law 148/2025/QH15 and repeal of Law 67/2006/QH11). [Online]. Available: https://pbgdpl.cantho.gov.vn/trach-nhiem-cua-to-chuc-ca-nhan-trong-chuyen-doi-so ; see also Tạp chí Công Thương, https://tapchicongthuong.vn/ban-hanh-ke-hoach-trien-khai-thi-hanh-luat-chuyen-doi-so-440961.htm

[7] National Assembly of Vietnam, *Law on Information Technology*, No. 67/2006/QH11, Jun. 29, 2006. Text: https://caselaw.vn/van-ban-phap-luat/115952-luat-cong-nghe-thong-tin-so-67-2006-qh11-ngay-29-06-2006-cua-quoc-hoi ; commentary on Art. 21–22: https://luatminhkhue.vn/quy-dinh-thu-thap-xu-ly-su-dung-thong-tin-ca-nhan-tren-moi-truong-mang.aspx

[8] National Assembly of Vietnam, *Law on Intellectual Property*, No. 50/2005/QH11, Nov. 29, 2005; amended by Laws No. 36/2009/QH12, 42/2019/QH14 and 07/2022/QH15 (Jun. 16, 2022).

[9] LawNet, "Cases of copyright exceptions in Vietnam from January 1, 2023." [Online]. Available: https://lawnet.vn/thong-tin-phap-luat/en/chinh-sach-moi/cases-of-copyright-exceptions-in-vietnam-from-january-1-2023-108346.html

[10] National Assembly of Vietnam, *Law amending and supplementing a number of articles of the Law on Intellectual Property*, No. 131/2025/QH15, Dec. 10, 2025 (effective Apr. 1, 2026). Index: https://thuvienphapluat.vn/van-ban/So-huu-tri-tue/Law-131-2025-QH15-amendments-to-the-Law-on-Intellectual-Property-700208.aspx

[11] Rajah & Tann Asia, "Vietnam's intellectual property framework enters a new era: advanced international standards, AI governance and specialised IP adjudication." [Online]. Available: https://www.rajahtannasia.com/viewpoints/vietnams-intellectual-property-framework-enters-a-new-era-advanced-international-standards-ai-governance-and-specialised-ip-adjudication/ ; Viet An Law, "Vietnam IP law 2025 update: copyright exceptions for AI model training," https://vietanlaw.com/vietnam-ip-law-2025-update-copyright-exceptions-for-ai-model-training

[12] National Assembly of Vietnam, *Law on Personal Data Protection*, No. 91/2025/QH15, Jun. 26, 2025 (effective Jan. 1, 2026). Text index: https://english.luatvietnam.vn/dan-su/law-on-personal-data-protection-law-no-91-2025-qh15-405135-d1.html

[13] DLA Piper, "Data protection laws of the world: Vietnam." [Online]. Available: https://www.dlapiperdataprotection.com/?c=VN&t=law ; Tilleke & Gibbins, "Vietnam's new Personal Data Protection Law: a closer look," https://tilleke.com/insights/vietnams-new-personal-data-protection-law-a-closer-look

[14] Apolat Legal, "'Public' personal data: Are businesses free to exploit it?" [Online]. Available: https://apolatlegal.com/public-personal-data-are-businesses-free-to-exploit-it/

[15] Government of Vietnam News, "First-ever law on artificial intelligence approved." [Online]. Available: https://en.baochinhphu.vn/first-ever-law-on-artificial-intelligence-approved-111251211093619398.htm ; LuatVietnam, "Six new laws take effect on March 1," https://luatvietnam.vn/legal-updates/six-new-laws-take-effect-on-march-1-892-107360-article.html

[16] Baker McKenzie, "Vietnam: Artificial Intelligence Law – foundation and outlook," Feb. 2026. [Online]. Available: https://www.bakermckenzie.com/en/insight/publications/2026/02/vietnam-artificial-intelligence-law-foundation-and-outlook

[17] National Assembly of Vietnam, *Law on Digital Technology Industry*, No. 71/2025/QH15, Jun. 14, 2025 (effective Jan. 1, 2026). Text: https://english.luatvietnam.vn/lawonthedigitaltechnologyindustryno71-2025-qh15datedjune142025ofthenationalassembly-405695-doc1.html

[18] Rahmat Lim & Partners, "Vietnam establishes digital technology framework and launches crypto-asset market pilot program." [Online]. Available: https://www.rahmatlim.com/publication/articles/31333/establishes-digital-technology-framework-and-launches-crypto-asset-market-pilot-program

[19] Free Software Foundation, "GNU General Public License, version 3," Jun. 29, 2007. [Online]. Available: https://www.gnu.org/licenses/gpl-3.0.html

[20] Free Software Foundation, "Various licenses and comments about them – Apache License, Version 2.0." [Online]. Available: https://www.gnu.org/licenses/license-list.html#apache2

[21] Hugging Face, "sentence-transformers/all-MiniLM-L6-v2 – model card." [Online]. Available: https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2 (accessed Oct. 2026).

[22] Python Package Index, project metadata for sentence-transformers, chromadb, streamlit, rank-bm25, scikit-learn, numpy, transformers, huggingface-hub, pytest. [Online]. Available: https://pypi.org/ (accessed Oct. 2026).

[23] E. Strubell, A. Ganesh, and A. McCallum, "Energy and policy considerations for deep learning in NLP," in *Proc. 57th Annu. Meeting Assoc. Computational Linguistics (ACL)*, Florence, Italy, 2019, pp. 3645–3650.

[24] Association for Computing Machinery, "ACM Code of Ethics and Professional Conduct," 2018. [Online]. Available: https://www.acm.org/code-of-ethics

</div>
