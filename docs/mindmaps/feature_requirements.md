# Concept Map – Features and User Requirements

**Owner:** Nguyễn Vi Kiên · **Design steps:** 3–4 · **Related:** `reports/src/outline_report.md` Section 8, `docs/ui_wireframes.md`

This concept map organises the features and user requirements of HCMUT-AILib by user need. It is a synthesis artefact. It summarises the requirement space that informed the outline report, and is not a transcript of any particular session. It renders on GitHub, or in any Mermaid ≥ 9.3 viewer.

```mermaid
mindmap
  root((HCMUT-AILib<br/>user needs))
    Find papers by meaning
      Natural-language query box
      Semantic ranking, cosine similarity
      Top-K slider 1–20
      Example queries for first-time users
      Empty-query and no-result messages
    Narrow the search
      Year range 2021–2025
      arXiv categories
        cs.AI
        cs.LG
        cs.CL
        cs.IR
      Author filter
      Reset filters
    Judge relevance quickly
      Match score 0–100%
      Category badges
      Truncated abstract with expander
      Extractive TF-IDF keywords
      Authors and publication date
    Go deeper
      Find similar papers
      Similar-papers tab
      Open PDF on arXiv
      DOI link when available
    Cite correctly
      BibTeX
      APA
      IEEE
      One-click copy
    Trust and transparency
      About tab
      Meaning of the score
      Dataset composition and limits
      English-only model notice
      arXiv acknowledgement
      Licences, GPLv3
    Non-functional
      Under 1.5 s per query
      Runs on 8 GB RAM laptop, no GPU
      Offline and private, no query logging
      Chrome, Firefox, Edge
      Light and dark theme
```

## Notes

- **Prioritisation (MoSCoW).** *Must:* query, ranking, Top-K, filters, result card, links, citations, About tab, feedback messages. *Should:* find similar, keywords, example queries. *Could:* light/dark theme polish, result export. *Won't (v1.0):* user accounts, full-text search, generated summaries, multilingual queries.
- **Traceability.** Each leaf maps to a functional requirement (FR1–FR10) or a non-functional requirement (NFR1–NFR6) in the outline report, Section 8.3–8.4. It is verified by the manual E2E checklist in `docs/test_plan.md`.
- **Validation.** The Week 7 usability study (`docs/usability/sus_survey.md`) checks whether these needs are actually met for HCMUT students.
