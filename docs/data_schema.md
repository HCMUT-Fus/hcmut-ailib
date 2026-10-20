# Data Schema – `data/raw/arxiv_sample_1000.json`

**Owner:** Từ Công Phú (Data & Retrieval Engineer) · **Producer:** `src/ingest.py` · **Consumers:** `src/indexer.py`, `src/lexical_baseline.py`, tests

## 1. File format

- UTF-8 encoded JSON. The top level is an **array** of 1,000 record objects.
- Source: arXiv API Atom feed (`https://export.arxiv.org/api/query`), queried per category (`cat:<category>`, which also matches cross-listed papers) and submission-year window (`submittedDate:[YYYY01010000 TO YYYY12312359]`), with at most one request every 3 seconds. A paper already taken by an earlier cell is skipped, so every `id` appears only once.
- Sampling design: 4 categories (cs.AI, cs.LG, cs.CL, cs.IR) × 5 submission years (2021–2025) × 50 papers = 1,000 records.
- Licence: arXiv metadata is released under CC0 1.0. Full texts are **not** included; `pdf_url` links to arXiv.

## 2. Fields

| Field | Type | Nullable | Description | Normalisation / constraints |
| :--- | :--- | :---: | :--- | :--- |
| `id` | string | No | arXiv identifier **without version** | Taken from the Atom `<id>` URL (`http://arxiv.org/abs/2401.01234v2`), stripping the URL prefix and the `vN` suffix → `"2401.01234"`. Unique across the file. New-style IDs follow `^\d{4}\.\d{4,5}$` |
| `title` | string | No | Paper title | Whitespace collapsed: newlines, tabs and repeated spaces become a single space; trimmed; non-empty |
| `abstract` | string | No | Author-written abstract (arXiv `<summary>`) | Whitespace collapsed; trimmed; non-empty. LaTeX markup is kept as written |
| `authors` | array of string | No | Author names in published order | Each name trimmed with whitespace collapsed; at least 1 element; Unicode preserved (e.g., `"Nguyễn Văn A"`, `"Jürgen Müller"`) |
| `doi` | string \| null | **Yes** | DOI registered for the paper (from `<arxiv:doi>`) | `null` when absent (never `""`); bare DOI without the `https://doi.org/` prefix |
| `categories` | array of string | No | All arXiv categories of the paper | Order as returned by the API; at least 1 element; contains at least one of the four sampled categories |
| `primary_category` | string | No | Primary arXiv category as declared by the authors | Any valid arXiv category. Because sampling uses `cat:`, a cross-listed paper may have a primary category outside the four sampled ones (e.g., `cs.CV`, `stat.ML`) |
| `published_date` | string (date) | No | Date of first version (`<published>`) | ISO 8601 calendar date `YYYY-MM-DD` (time and zone dropped); year within 2021–2025 |
| `pdf_url` | string (URL) | No | Link to the PDF on arXiv | Taken from the `<link title="pdf">` element (may carry a version suffix, e.g. `https://arxiv.org/pdf/2401.01234v1`), scheme forced to `https`; fallback `https://arxiv.org/pdf/<id>` |

## 3. Example record

The following example is illustrative of the format (values shortened):

```json
{
  "id": "2401.01234",
  "title": "An Example Title About Retrieval-Augmented Generation",
  "abstract": "We study how retrieval-augmented generation ... and show consistent gains on three benchmarks.",
  "authors": ["Nguyễn Văn A", "Jane Doe", "John Smith"],
  "doi": null,
  "categories": ["cs.CL", "cs.IR"],
  "primary_category": "cs.CL",
  "published_date": "2024-01-03",
  "pdf_url": "https://arxiv.org/pdf/2401.01234"
}
```

## 4. Validation rules (enforced by `tests/test_ingest.py`)

1. Exactly 1,000 records; no duplicate `id`.
2. All nine fields are present in every record; there are no extra required fields.
3. Types match Section 2, and `doi` is either a non-empty string or `null`.
4. `published_date` parses as `YYYY-MM-DD`, with the year in 2021–2025.
5. Every record's `categories` contains at least one of `cs.AI`, `cs.LG`, `cs.CL`, `cs.IR`.
6. For every year 2021–2025 there are 200 records (4 cells × 50); the per-category cell is a property of the sampling run, not a stored field.
7. `title` and `abstract` contain no newline characters or double spaces.

## 5. Derived representations

| Representation | Where | Content |
| :--- | :--- | :--- |
| Embedding input | `src/indexer.py` | `f"{title}. {abstract}"` |
| Vector | ChromaDB collection at `data/processed/vector_index/` | 384-d float vector from `all-MiniLM-L6-v2`; cosine space |
| Chroma document ID | ChromaDB | `id` |
| Chroma metadata | ChromaDB | Scalar values only (Chroma metadata cannot hold nulls or, in older versions, lists): e.g. `year` (int), `published_date`, `primary_category`, `categories` and `authors` serialised as strings, `doi` as an empty string when null, `pdf_url`, `title`. The exact keys are defined in `src/indexer.py` |

## 6. Known data limitations

- Abstracts may contain LaTeX (`$\alpha$`), which is left as is.
- Author name forms are inconsistent across papers (initials vs. full names), so the author filter is a case-insensitive substring match.
- `doi` is often absent for preprints that have not been formally published.
- The sample is stratified rather than random within each cell, so it does not represent the true category volumes on arXiv.
