"""HCMUT-AILib Streamlit dashboard. Run with ``streamlit run src/app.py``."""

from __future__ import annotations

import csv
import io
import json
import sys
import time
from collections import Counter
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from src import indexer, ingest  # noqa: E402
from src.citations import FORMATS, bibtex_key  # noqa: E402
from src.keywords import KeywordExtractor  # noqa: E402
from src.lexical_baseline import BM25  # noqa: E402
from src.search_engine import Paper, SearchEngine, SearchResult  # noqa: E402

CATEGORY_NAMES = {
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.CL": "Computation and Language",
    "cs.IR": "Information Retrieval",
}
EXAMPLE_QUERIES = [
    "detecting fake news on social media",
    "making transformers cheaper for long documents",
    "recommendation systems that explain their suggestions",
    "translation for languages with little training data",
    "attacks that hide triggers inside neural networks",
    "mixing two languages within one conversation",
    "blurring sensitive objects in real-time video broadcasts",
]
RETRIEVAL_MODES = (
    "Dense Semantic (MiniLM-L6)",
    "Hybrid RRF (Semantic + BM25)",
    "Lexical Baseline (Okapi BM25)",
)
SORT_OPTIONS = ("Relevance", "Newest first", "Oldest first", "Title (A–Z)")
VIEW_MODES = ("Detailed Cards", "Cards + Comparison Matrix", "Compact Cards")
ABSTRACT_PREVIEW = 300
EVAL_JSON_PATH = REPO_ROOT / "reports" / "results" / "evaluation.json"
PCA_FIG_PATH = REPO_ROOT / "reports" / "figures" / "embedding_pca.png"
ARCH_FIG_PATH = REPO_ROOT / "docs" / "architecture.png"

st.set_page_config(page_title="HCMUT-AILib", page_icon="📚", layout="wide")


def inject_styles() -> None:
    """Apply dark-mode research workbench styling for header, cards, badges, and panels."""
    st.html("""
    <style>
        /* Root & container layout */
        .stApp {
            background: radial-gradient(circle at 15% 0%, #111c35 0%, #0b0f19 55%, #070a12 100%);
            color: #f1f5f9;
        }
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 3.5rem;
            max-width: 1280px;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f172a 0%, #0b1120 100%);
            border-right: 1px solid rgba(56, 189, 248, 0.16);
        }

        /* Hide the raw default h1 spacing & integrate with custom hero banner */
        h1 {
            font-size: 2.05rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.025em !important;
            margin-top: -0.35rem !important;
            margin-bottom: 0.15rem !important;
            background: linear-gradient(90deg, #f8fafc 0%, #7dd3fc 55%, #38bdf8 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }

        /* Professional Institutional Header Banner */
        .ailib-hero {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.95) 0%, rgba(30, 27, 75, 0.88) 55%, rgba(12, 74, 110, 0.85) 100%);
            border: 1px solid rgba(56, 189, 248, 0.28);
            border-radius: 16px;
            padding: 1.15rem 1.45rem 1.05rem 1.45rem;
            margin-bottom: 0.75rem;
            box-shadow: 0 12px 32px rgba(0, 0, 0, 0.42), inset 0 1px 0 rgba(255, 255, 255, 0.08);
            position: relative;
            overflow: hidden;
        }
        .ailib-hero::before {
            content: "";
            position: absolute;
            top: -60px;
            right: -60px;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(56, 189, 248, 0.18) 0%, transparent 70%);
            pointer-events: none;
        }
        .ailib-eyebrow-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 0.6rem;
            margin-bottom: 0.45rem;
        }
        .ailib-inst-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.73rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            color: #93c5fd;
            background: rgba(30, 58, 138, 0.45);
            border: 1px solid rgba(96, 165, 250, 0.35);
            padding: 0.24rem 0.68rem;
            border-radius: 999px;
        }
        .ailib-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            align-items: center;
        }
        .ailib-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.22rem 0.62rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.75);
            border: 1px solid rgba(148, 163, 184, 0.25);
            color: #e2e8f0;
        }
        .ailib-pill-online {
            border-color: rgba(52, 211, 153, 0.45);
            color: #6ee7b7;
            background: rgba(6, 78, 59, 0.35);
        }
        .ailib-pill-cyan {
            border-color: rgba(56, 189, 248, 0.45);
            color: #7dd3fc;
            background: rgba(12, 74, 110, 0.35);
        }
        .ailib-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #10b981;
            box-shadow: 0 0 8px #10b981;
            display: inline-block;
        }
        .ailib-hero-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 0.65rem;
            margin-top: 0.75rem;
            padding-top: 0.75rem;
            border-top: 1px solid rgba(148, 163, 184, 0.16);
        }
        .ailib-stat-box {
            background: rgba(15, 23, 42, 0.62);
            border: 1px solid rgba(148, 163, 184, 0.16);
            border-radius: 10px;
            padding: 0.48rem 0.72rem;
        }
        .ailib-stat-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #94a3b8;
            margin-bottom: 0.12rem;
        }
        .ailib-stat-val {
            font-size: 0.98rem;
            font-weight: 700;
            color: #f8fafc;
        }
        .ailib-stat-sub {
            font-size: 0.7rem;
            color: #38bdf8;
            font-weight: 500;
        }

        /* Bordered Containers / Cards */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: rgba(17, 24, 39, 0.78);
            border: 1px solid rgba(56, 189, 248, 0.18) !important;
            border-radius: 14px !important;
            transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.15s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(56, 189, 248, 0.48) !important;
            box-shadow: 0 8px 24px rgba(2, 132, 199, 0.14);
        }

        /* Metrics */
        div[data-testid="stMetric"] {
            background: rgba(15, 23, 42, 0.65);
            border: 1px solid rgba(56, 189, 248, 0.2);
            border-radius: 10px;
            padding: 0.45rem 0.65rem;
        }
        div[data-testid="stMetricValue"] {
            color: #38bdf8 !important;
            font-weight: 700 !important;
        }

        /* Tabs bar */
        div[data-baseweb="tab-list"] {
            gap: 0.35rem;
            background: rgba(15, 23, 42, 0.75);
            padding: 0.35rem;
            border-radius: 12px;
            border: 1px solid rgba(148, 163, 184, 0.16);
        }
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 1rem !important;
            border-radius: 8px !important;
            color: #94a3b8 !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: rgba(56, 189, 248, 0.15) !important;
            color: #38bdf8 !important;
        }

        /* Sidebar section header chips */
        .sidebar-section-title {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            color: #38bdf8;
            margin-top: 0.6rem;
            margin-bottom: 0.3rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }
        .tier-chip {
            display: inline-block;
            font-size: 0.7rem;
            font-weight: 700;
            padding: 0.14rem 0.52rem;
            border-radius: 999px;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }
        .tier-high {
            background: rgba(16, 185, 129, 0.18);
            color: #34d399;
            border: 1px solid rgba(52, 211, 153, 0.4);
        }
        .tier-med {
            background: rgba(56, 189, 248, 0.18);
            color: #38bdf8;
            border: 1px solid rgba(56, 189, 248, 0.4);
        }
        .tier-low {
            background: rgba(245, 158, 11, 0.18);
            color: #fbbf24;
            border: 1px solid rgba(251, 191, 36, 0.4);
        }
    </style>
    """)


@st.cache_resource(show_spinner="Loading embedding model and vector index…")
def get_engine() -> SearchEngine:
    return SearchEngine()


@st.cache_resource
def get_keyword_extractor() -> KeywordExtractor:
    return KeywordExtractor([p["abstract"] for p in ingest.load()])


@st.cache_resource
def get_bm25_engine() -> BM25:
    return BM25(ingest.load())


@st.cache_data
def load_raw_corpus() -> list[dict]:
    return ingest.load()


@st.cache_data
def year_bounds() -> tuple[int, int]:
    years = [int(p["published_date"][:4]) for p in load_raw_corpus()]
    return min(years), max(years)


@st.cache_data
def paper_catalog() -> dict[str, str]:
    """Map paper IDs to human-readable 'ID — Title (Year)' labels for seed selection."""
    return {
        p["id"]: f"{p['id']} — {p['title']} ({p['published_date'][:4]})"
        for p in load_raw_corpus()
    }


@st.cache_data
def load_evaluation_data() -> dict | None:
    if EVAL_JSON_PATH.exists():
        try:
            return json.loads(EVAL_JSON_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


@st.cache_data
def corpus_statistics() -> dict:
    records = load_raw_corpus()
    by_year = Counter(int(r["published_date"][:4]) for r in records)
    by_primary = Counter(r["primary_category"] for r in records)
    by_sampled_cat = Counter(
        cat for r in records for cat in r["categories"] if cat in CATEGORY_NAMES
    )
    doi_count = sum(1 for r in records if r.get("doi"))
    word_counts = [len(r["abstract"].split()) for r in records]
    author_counts = [len(r["authors"]) for r in records]
    return {
        "total": len(records),
        "by_year": dict(sorted(by_year.items())),
        "by_primary": dict(by_primary.most_common(8)),
        "by_sampled_cat": {c: by_sampled_cat[c] for c in CATEGORY_NAMES},
        "doi_count": doi_count,
        "doi_pct": (doi_count / len(records) * 100.0) if records else 0.0,
        "avg_words": sum(word_counts) / len(word_counts) if word_counts else 0.0,
        "avg_authors": sum(author_counts) / len(author_counts) if author_counts else 0.0,
    }


def init_session_state() -> None:
    if "query" not in st.session_state:
        st.session_state.query = ""
    if "similar_to" not in st.session_state:
        st.session_state.similar_to = ""
    if "saved_papers" not in st.session_state:
        st.session_state.saved_papers = []
    if "query_history" not in st.session_state:
        st.session_state.query_history = []


def _select_similar(paper_id: str) -> None:
    st.session_state.similar_to = paper_id
    st.session_state.seed_picker = paper_id
    st.session_state._switch_to_similar = True


def _toggle_saved_paper(paper_id: str) -> None:
    saved: list[str] = list(st.session_state.get("saved_papers", []))
    if paper_id in saved:
        saved.remove(paper_id)
    else:
        saved.append(paper_id)
    st.session_state.saved_papers = saved


def _clear_saved_papers() -> None:
    st.session_state.saved_papers = []


def _on_seed_picker_change() -> None:
    picked = st.session_state.get("seed_picker")
    if picked:
        st.session_state.similar_to = picked


def _on_similar_input_change() -> None:
    raw = (st.session_state.get("similar_to") or "").strip()
    if not raw:
        st.session_state.seed_picker = None
        return
    clean = ingest.parse_arxiv_id(
        raw[6:].strip() if raw.lower().startswith("arxiv:") else raw
    )
    st.session_state.seed_picker = clean if clean in paper_catalog() else None


def _on_example_change() -> None:
    st.session_state.query = st.session_state.get("example") or ""


def _on_query_change() -> None:
    if st.session_state.get("example") != st.session_state.get("query"):
        st.session_state.example = None


def _set_query(q: str) -> None:
    st.session_state.query = q
    st.session_state.example = q if q in EXAMPLE_QUERIES else None


def _clear_query() -> None:
    st.session_state.query = ""
    st.session_state.example = None


def _reset_filters(lo: int, hi: int) -> None:
    st.session_state.filter_top_k = 10
    st.session_state.filter_years = (lo, hi)
    st.session_state.filter_categories = []
    st.session_state.filter_author = ""
    st.session_state.retrieval_mode = RETRIEVAL_MODES[0]
    st.session_state.min_score_pct = 0
    st.session_state.sort_by = SORT_OPTIONS[0]
    st.session_state.view_mode = VIEW_MODES[0]
    st.session_state.only_doi = False


def record_query_history(query: str) -> None:
    q = query.strip()
    if not q:
        return
    hist: list[str] = list(st.session_state.get("query_history", []))
    if q in hist:
        hist.remove(q)
    hist.insert(0, q)
    st.session_state.query_history = hist[:8]


def format_category_badges(paper: Paper) -> str:
    badges = []
    for idx, cat in enumerate(paper.categories):
        if cat in CATEGORY_NAMES:
            label = f"{cat} · {CATEGORY_NAMES[cat]}" if idx == 0 else cat
            badges.append(f":blue-badge[{label}]")
        else:
            badges.append(f":gray-badge[{cat}]")
    return " ".join(badges)


def confidence_tier_html(score: float) -> str:
    if score >= 0.78:
        return '<span class="tier-chip tier-high">● High Match</span>'
    if score >= 0.68:
        return '<span class="tier-chip tier-med">● Moderate Match</span>'
    return '<span class="tier-chip tier-low">● Exploratory</span>'


def format_active_filters(
    years: tuple[int, int],
    bounds: tuple[int, int],
    categories: list[str],
    author: str,
    min_score_pct: int = 0,
    only_doi: bool = False,
    retrieval_mode: str = RETRIEVAL_MODES[0],
) -> list[str]:
    summary: list[str] = []
    if retrieval_mode != RETRIEVAL_MODES[0]:
        summary.append(f"Mode: {retrieval_mode.split(' (')[0]}")
    if years != bounds:
        summary.append(
            f"Year: {years[0]}" if years[0] == years[1] else f"Years: {years[0]}–{years[1]}"
        )
    if categories:
        summary.append("Categories: " + ", ".join(categories))
    if author.strip():
        summary.append(f"Author: “{author.strip()}”")
    if min_score_pct > 0:
        summary.append(f"Min Match: ≥{min_score_pct}%")
    if only_doi:
        summary.append("DOI Required")
    return summary


def paper_matches_filters(
    paper: Paper,
    year_range: tuple[int, int] | None,
    categories: list[str] | None,
    author: str | None,
) -> bool:
    if year_range and not (year_range[0] <= paper.year <= year_range[1]):
        return False
    if categories and not any(c in paper.categories for c in categories):
        return False
    if author and author.strip().lower() not in "; ".join(paper.authors).lower():
        return False
    return True


def execute_retrieval(
    engine: SearchEngine,
    query: str,
    retrieval_mode: str,
    top_k: int,
    year_range: tuple[int, int] | None,
    categories: list[str] | None,
    author: str | None,
) -> list[SearchResult]:
    """Run semantic, BM25, or Reciprocal Rank Fusion (RRF) hybrid retrieval."""
    if retrieval_mode == "Dense Semantic (MiniLM-L6)":
        return engine.search(
            query,
            top_k=top_k,
            year_range=year_range,
            categories=categories,
            author=author,
        )

    bm25 = get_bm25_engine()
    raw_scores = bm25.scores(query)
    max_bm25 = max(raw_scores) if raw_scores else 0.0

    if retrieval_mode == "Lexical Baseline (Okapi BM25)":
        ranked = sorted(zip(raw_scores, bm25.ids), key=lambda x: -x[0])
        results: list[SearchResult] = []
        for sc, pid in ranked:
            if sc <= 0:
                break
            paper = engine.get(pid)
            if not paper_matches_filters(paper, year_range, categories, author):
                continue
            norm_sc = min(0.99, max(0.05, sc / max_bm25)) if max_bm25 > 0 else 0.0
            results.append(SearchResult(paper=paper, score=norm_sc, rank=len(results) + 1))
            if len(results) == top_k:
                break
        return results

    # Hybrid RRF (Semantic + BM25)
    pool_k = max(top_k * 4, 40)
    sem_results = engine.search(
        query,
        top_k=pool_k,
        year_range=year_range,
        categories=categories,
        author=author,
    )
    sem_map = {r.paper.id: (r.rank, r.score, r.paper) for r in sem_results}

    bm25_ranked = [
        (pid, sc) for sc, pid in sorted(zip(raw_scores, bm25.ids), key=lambda x: -x[0]) if sc > 0
    ]
    bm25_rank_map = {pid: idx + 1 for idx, (pid, _) in enumerate(bm25_ranked[:pool_k])}

    candidate_ids = list(dict.fromkeys(list(sem_map) + list(bm25_rank_map)))
    rrf_scored: list[tuple[float, float, Paper]] = []
    rrf_k = 60.0
    for pid in candidate_ids:
        if pid in sem_map:
            s_rank, s_score, paper = sem_map[pid]
        else:
            paper = engine.get(pid)
            if not paper_matches_filters(paper, year_range, categories, author):
                continue
            s_rank, s_score = pool_k + 50, 0.50
        b_rank = bm25_rank_map.get(pid, pool_k + 50)
        rrf = (1.0 / (rrf_k + s_rank)) + (1.0 / (rrf_k + b_rank))
        # Rescale display score blending semantic similarity with lexical boost
        boost = 0.04 if pid in bm25_rank_map else 0.0
        display_score = min(0.99, s_score + boost)
        rrf_scored.append((rrf, display_score, paper))

    rrf_scored.sort(key=lambda item: (-item[0], -item[1]))
    return [
        SearchResult(paper=paper, score=disp_score, rank=idx + 1)
        for idx, (_, disp_score, paper) in enumerate(rrf_scored[:top_k])
    ]


def results_to_csv(results: list[SearchResult]) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        ["Rank", "arXiv ID", "Title", "Year", "Published Date", "Primary Category",
         "Categories", "Match Score", "Authors", "DOI", "PDF URL", "arXiv URL"]
    )
    for r in results:
        p = r.paper
        writer.writerow([
            r.rank,
            p.id,
            p.title,
            p.year,
            p.published_date,
            p.primary_category,
            " ".join(p.categories),
            f"{r.score:.4f}",
            "; ".join(p.authors),
            p.doi or "",
            p.pdf_url,
            p.abs_url,
        ])
    return buf.getvalue()


def render_professional_header(engine: SearchEngine) -> None:
    """Render a multi-layered institutional dark-mode header with live telemetry."""
    stats = corpus_statistics()
    saved_count = len(st.session_state.get("saved_papers", []))

    st.html(f"""
    <div class="ailib-hero">
        <div class="ailib-eyebrow-row">
            <span class="ailib-inst-tag">
                🏛️ HCMUT · Faculty of Computer Science &amp; Engineering · CO2001
            </span>
            <div class="ailib-status-strip">
                <span class="ailib-pill ailib-pill-online">
                    <span class="ailib-dot"></span> Engine Online
                </span>
                <span class="ailib-pill ailib-pill-cyan">
                    🧠 {indexer.MODEL_NAME} · 384-D
                </span>
                <span class="ailib-pill">
                    ⚡ ChromaDB HNSW · Cosine
                </span>
                <span class="ailib-pill">
                    🔒 Air-Gapped Local Execution
                </span>
            </div>
        </div>
    </div>
    """)

    title_col, status_col = st.columns([3, 2])
    with title_col:
        st.title("📚 HCMUT-AILib")
        st.caption(
            "Semantic search & research assistant for open-access academic papers · "
            "Dense Vector Retrieval Workbench (v1.0.0)"
        )
    with status_col:
        st.html(f"""
        <div class="ailib-hero-grid" style="margin-top: 0.15rem; padding-top: 0; border-top: none;">
            <div class="ailib-stat-box">
                <div class="ailib-stat-label">Indexed Corpus</div>
                <div class="ailib-stat-val">{len(engine):,} Papers</div>
                <div class="ailib-stat-sub">arXiv 2021–2025 · 4 CS Domains</div>
            </div>
            <div class="ailib-stat-box">
                <div class="ailib-stat-label">Benchmark MRR</div>
                <div class="ailib-stat-val">0.911</div>
                <div class="ailib-stat-sub">+31.5% vs Okapi BM25 (0.693)</div>
            </div>
            <div class="ailib-stat-box">
                <div class="ailib-stat-label">Session Reading List</div>
                <div class="ailib-stat-val">{saved_count} Saved</div>
                <div class="ailib-stat-sub">{stats['doi_pct']:.1f}% Publisher DOI Coverage</div>
            </div>
        </div>
        """)


def render_card(
    result: SearchResult,
    key_prefix: str,
    compact: bool = False,
) -> None:
    paper = result.paper
    is_saved = paper.id in st.session_state.get("saved_papers", [])
    with st.container(border=True):
        head, score = st.columns([5.8, 1.2])
        head.markdown(f"#### {result.rank}. {paper.title}")
        score.metric(
            "Match",
            f"{result.score:.0%}",
            help="Cosine similarity rescaled to 0–1; compare within this query only.",
        )
        score.progress(result.score)

        authors = ", ".join(paper.authors[:6]) + (
            f" et al. (+{len(paper.authors) - 6} more)" if len(paper.authors) > 6 else ""
        )
        badges = format_category_badges(paper)
        doi_badge = f" :green-badge[DOI: {paper.doi}]" if paper.doi else ""
        head.markdown(
            f"**{authors}** · 📅 `{paper.published_date}` · `arXiv:{paper.id}`  \n"
            f"{badges}{doi_badge}"
        )
        score.html(
            f"<div style='text-align:right; margin-top:2px;'>{confidence_tier_html(result.score)}</div>"
        )

        keywords = get_keyword_extractor().extract(paper.abstract, k=5)
        if keywords:
            kw_pills = " ".join(f":violet-badge[{kw}]" for kw in keywords)
            st.markdown(f"**Key terms:** {kw_pills}")

        if not compact:
            preview = (
                paper.abstract
                if len(paper.abstract) <= ABSTRACT_PREVIEW
                else paper.abstract[:ABSTRACT_PREVIEW].rsplit(" ", 1)[0] + " …"
            )
            st.write(preview)

        with st.expander("Full abstract & metadata"):
            st.write(paper.abstract)
            meta_c1, meta_c2, meta_c3 = st.columns(3)
            meta_c1.caption(f"**Primary category:** `{paper.primary_category}`")
            meta_c2.caption(f"**Abstract length:** {len(paper.abstract.split())} words")
            meta_c3.caption(f"**BibTeX key:** `{bibtex_key(paper)}`")
            if len(paper.authors) > 6:
                st.caption("**All authors:** " + ", ".join(paper.authors))

        n_cols = 5 if paper.doi else 4
        links = st.columns(n_cols)
        links[0].link_button("📄 PDF", paper.pdf_url, width="stretch")
        links[1].link_button("🔗 arXiv page", paper.abs_url, width="stretch")
        if paper.doi:
            links[2].link_button("🏷️ DOI", f"https://doi.org/{paper.doi}", width="stretch")
            sim_col = links[3]
            save_col = links[4]
        else:
            sim_col = links[2]
            save_col = links[3]

        if sim_col.button(
            "🔍 Find similar",
            key=f"{key_prefix}-sim-{paper.id}",
            on_click=_select_similar,
            args=(paper.id,),
            width="stretch",
        ):
            st.toast(f"Loaded neighbours for arXiv:{paper.id} in the “Similar papers” tab.")

        save_label = "🔖 Saved" if is_saved else "🔖 Save paper"
        if save_col.button(
            save_label,
            key=f"{key_prefix}-save-{paper.id}",
            on_click=_toggle_saved_paper,
            args=(paper.id,),
            width="stretch",
        ):
            action = "Removed from" if is_saved else "Added to"
            st.toast(f"{action} your Reading List ({paper.id}).")

        with st.expander("Cite this paper"):
            c_top_left, c_top_right = st.columns([3, 1])
            style = c_top_left.radio(
                "Format",
                list(FORMATS),
                horizontal=True,
                key=f"{key_prefix}-cite-{paper.id}",
                label_visibility="collapsed",
            )
            citation_text = FORMATS[style](paper)
            c_top_right.download_button(
                "⬇️ Download .bib" if style == "BibTeX" else "⬇️ Download .txt",
                data=citation_text,
                file_name=f"{paper.id}.bib" if style == "BibTeX" else f"{paper.id}_{style.lower()}.txt",
                mime="text/plain",
                key=f"{key_prefix}-dl-{paper.id}",
                width="stretch",
            )
            st.code(
                citation_text,
                language="bibtex" if style == "BibTeX" else None,
                wrap_lines=True,
            )


def render_onboarding() -> None:
    st.info("Type a research question above, or pick one of the examples.")

    stats = corpus_statistics()
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Stratified Corpus", f"{stats['total']:,} Papers", "50 / category / year")
    k2.metric("Mean Abstract Length", f"{stats['avg_words']:.0f} Words", "Title + Abstract embedded")
    k3.metric("Mean Query Latency", "13.6 ms", "p95: 17.1 ms (CPU)")
    k4.metric("Top-1 Accuracy", "83.3%", "25 / 30 benchmark queries")

    cols = st.columns(3)
    with cols[0]:
        with st.container(border=True):
            st.markdown(
                "### 🎯 Semantic & Hybrid Modes\n"
                "Switch seamlessly between **Dense Semantic** (`all-MiniLM-L6-v2`), "
                "**Hybrid RRF** (Reciprocal Rank Fusion), and **Okapi BM25** keyword search "
                "from the sidebar to see how meaning-based search overcomes vocabulary mismatch."
            )
    with cols[1]:
        with st.container(border=True):
            st.markdown(
                "### 🧭 Graph-Like Neighbourhoods\n"
                "Click **🔍 Find similar** on any paper card to jump directly into its "
                "384-dimensional embedding neighbourhood and inspect topically related papers."
            )
    with cols[2]:
        with st.container(border=True):
            st.markdown(
                "### 🔖 Reading List & Batch Export\n"
                "Bookmark relevant papers with **🔖 Save paper**, compare them side-by-side "
                "in the **Reading List** tab, and export formatted **BibTeX / APA 7 / IEEE** "
                "citations or CSV summaries."
            )

    with st.expander("💡 Why Semantic Search? Vocabulary Mismatch Showcase (Live Examples)", expanded=True):
        showcase_rows = [
            {
                "Natural-Language Query": "mixing two languages within one conversation",
                "BM25 Keyword Top Hit": "No relevant match (0 lexical overlap)",
                "HCMUT-AILib Top Hit (Rank 1)": "A Survey of Code-switching (cs.CL)",
            },
            {
                "Natural-Language Query": "how humans learn to decide when to stop deliberating and act",
                "BM25 Keyword Top Hit": "Impact of Stop Sets on Active Learning (false match on 'stop')",
                "HCMUT-AILib Top Hit (Rank 1)": "Have I done enough planning or should I plan more? (cs.AI)",
            },
            {
                "Natural-Language Query": "jointly grouping documents and discovering their topics without supervision",
                "BM25 Keyword Top Hit": "No relevant match in top 10",
                "HCMUT-AILib Top Hit (Rank 1)": "ClusTop: Unsupervised Text Clustering & Topic Extraction (cs.IR)",
            },
        ]
        st.dataframe(showcase_rows, width="stretch", hide_index=True)


def render_results_analytics_bar(
    results: list[SearchResult],
    elapsed: float,
    retrieval_mode: str,
) -> None:
    scores = [r.score for r in results]
    top_score = max(scores) if scores else 0.0
    mean_score = sum(scores) / len(scores) if scores else 0.0
    years = [r.paper.year for r in results]
    cat_counts = Counter(r.paper.primary_category for r in results)
    top_cat, top_cat_n = cat_counts.most_common(1)[0] if cat_counts else ("–", 0)

    m1, m2, m3, m4 = st.columns(4)
    m1.metric(
        "Retrieved Papers",
        f"{len(results)}",
        retrieval_mode.split(" (")[0],
    )
    m2.metric(
        "Search Latency",
        f"{elapsed * 1000:.1f} ms",
        "Target < 1,500 ms",
    )
    m3.metric(
        "Top Match Score",
        f"{top_score:.0%}",
        f"Mean: {mean_score:.0%}",
    )
    m4.metric(
        "Dominant Category",
        f"{top_cat} ({top_cat_n})",
        f"Span: {min(years)}–{max(years)}" if years else "–",
    )


def render_results_comparison_matrix(results: list[SearchResult]) -> None:
    rows = [
        {
            "Rank": r.rank,
            "Match": round(r.score * 100, 1),
            "arXiv ID": r.paper.id,
            "Year": r.paper.year,
            "Category": r.paper.primary_category,
            "Title": r.paper.title,
            "First Author": r.paper.authors[0] if r.paper.authors else "Unknown",
            "Authors": len(r.paper.authors),
            "Has DOI": "✔" if r.paper.doi else "–",
        }
        for r in results
    ]
    st.dataframe(
        rows,
        width="stretch",
        hide_index=True,
        column_config={
            "Match": st.column_config.ProgressColumn(
                "Match %",
                min_value=0,
                max_value=100,
                format="%.1f%%",
            ),
            "Title": st.column_config.TextColumn("Paper Title", width="large"),
        },
    )


def search_tab(
    engine: SearchEngine,
    filters: dict,
    active_filter_tags: list[str],
    retrieval_mode: str,
    min_score_pct: int,
    sort_by: str,
    view_mode: str,
    only_doi: bool,
) -> None:
    st.markdown(
        "Describe what you are looking for in plain English — the engine matches "
        "**meaning**, not exact words."
    )

    if st.session_state.query.strip():
        input_col, clear_col = st.columns([11, 1])
        input_col.text_input(
            "Search query",
            key="query",
            label_visibility="collapsed",
            placeholder="e.g. transfer learning for low-resource machine translation",
            on_change=_on_query_change,
        )
        clear_col.button(
            "✕",
            key="clear_query_btn",
            help="Clear search query",
            on_click=_clear_query,
            width="stretch",
        )
    else:
        st.text_input(
            "Search query",
            key="query",
            label_visibility="collapsed",
            placeholder="e.g. transfer learning for low-resource machine translation",
            on_change=_on_query_change,
        )

    suggestion = st.pills(
        "Try an example",
        EXAMPLE_QUERIES,
        key="example",
        on_change=_on_example_change,
    )
    query = st.session_state.query.strip() or (suggestion or "")

    if not query:
        render_onboarding()
        return

    record_query_history(query)

    with st.spinner("Searching…"):
        start = time.perf_counter()
        results = execute_retrieval(
            engine,
            query=query,
            retrieval_mode=retrieval_mode,
            **filters,
        )
        elapsed = time.perf_counter() - start

    if min_score_pct > 0:
        threshold = min_score_pct / 100.0
        results = [r for r in results if r.score >= threshold]
    if only_doi:
        results = [r for r in results if r.paper.doi]

    if not results:
        st.warning(
            "No papers match this query with the current filters. "
            "Try widening the year range or removing category/author filters."
        )
        return

    if sort_by == "Newest first":
        results = sorted(results, key=lambda r: r.paper.published_date, reverse=True)
    elif sort_by == "Oldest first":
        results = sorted(results, key=lambda r: r.paper.published_date)
    elif sort_by == "Title (A–Z)":
        results = sorted(results, key=lambda r: r.paper.title.lower())

    filter_note = " · ".join(active_filter_tags) if active_filter_tags else "All years & categories"
    st.caption(f"{len(results)} results for “{query}” in {elapsed:.2f} s · {filter_note}")

    render_results_analytics_bar(results, elapsed, retrieval_mode)

    if view_mode == "Cards + Comparison Matrix":
        with st.container(border=True):
            st.markdown("##### 📊 Results Comparison Matrix")
            render_results_comparison_matrix(results)
    else:
        with st.expander("📊 Inspect results in tabular comparison matrix"):
            render_results_comparison_matrix(results)

    compact_cards = view_mode == "Compact Cards"
    for result in results:
        render_card(result, "search", compact=compact_cards)

    with st.expander(f"📋 Batch Export & Citations for all {len(results)} displayed results"):
        exp_c1, exp_c2, exp_c3 = st.columns([2, 1, 1])
        batch_style = exp_c1.radio(
            "Batch citation format",
            list(FORMATS),
            horizontal=True,
            key="batch_cite_style",
            label_visibility="collapsed",
        )
        combined_citations = "\n\n".join(FORMATS[batch_style](r.paper) for r in results)
        exp_c2.download_button(
            f"⬇️ Download All ({batch_style})",
            data=combined_citations,
            file_name="hcmut_ailib_results.bib" if batch_style == "BibTeX" else "hcmut_ailib_citations.txt",
            mime="text/plain",
            key="dl_batch_citations",
            width="stretch",
        )
        exp_c3.download_button(
            "⬇️ Export Results CSV",
            data=results_to_csv(results),
            file_name="hcmut_ailib_results.csv",
            mime="text/csv",
            key="dl_batch_csv",
            width="stretch",
        )
        st.code(
            combined_citations,
            language="bibtex" if batch_style == "BibTeX" else None,
            wrap_lines=True,
        )


def similar_tab(engine: SearchEngine, top_k: int) -> None:
    st.markdown(
        "Explore the 384-dimensional vector neighbourhood around any seed paper in the index."
    )
    catalog = paper_catalog()
    col_id, col_pick = st.columns([1, 2.2])
    paper_id = col_id.text_input(
        "arXiv id",
        key="similar_to",
        placeholder="e.g. 2401.01076",
        help="Click “Find similar” on any search result, or paste an arXiv ID.",
        on_change=_on_similar_input_change,
    )
    col_pick.selectbox(
        "Or browse a seed paper by title",
        options=list(catalog),
        index=None,
        key="seed_picker",
        format_func=lambda pid: catalog.get(pid, pid),
        placeholder="Type to search paper titles in the corpus…",
        on_change=_on_seed_picker_change,
    )

    raw_id = paper_id.strip()
    if not raw_id:
        st.info(
            "Pick a paper with the “Find similar” button in the Search tab, "
            "paste an arXiv ID, or select a title above."
        )
        return
    clean_id = ingest.parse_arxiv_id(
        raw_id[6:].strip() if raw_id.lower().startswith("arxiv:") else raw_id
    )
    try:
        source = engine.get(clean_id)
    except KeyError:
        st.error(f"Paper {raw_id} is not in the index.")
        return

    neighbours = engine.similar(source.id, top_k)
    mean_sim = sum(r.score for r in neighbours) / len(neighbours) if neighbours else 0.0
    same_cat = sum(
        1 for r in neighbours if source.primary_category in r.paper.categories
    )

    with st.container(border=True):
        top_left, top_right = st.columns([4, 1.5])
        top_left.caption("🎯 SEED PAPER SPOTLIGHT")
        top_left.markdown(f"### {source.title}")
        seed_authors = ", ".join(source.authors[:6]) + (
            f" et al. (+{len(source.authors) - 6} more)" if len(source.authors) > 6 else ""
        )
        top_left.markdown(
            f"**{seed_authors}** · 📅 `{source.published_date}` · `arXiv:{source.id}`  \n"
            f"{format_category_badges(source)}"
        )
        top_right.metric("Mean Neighbour Sim", f"{mean_sim:.0%}")
        top_right.caption(
            f"Category overlap (`{source.primary_category}`): **{same_cat}/{len(neighbours)}** papers"
        )

        with st.expander("Read seed paper abstract"):
            st.write(source.abstract)

        seed_cols = st.columns(4 if source.doi else 3)
        seed_cols[0].link_button("📄 Seed PDF", source.pdf_url, width="stretch")
        seed_cols[1].link_button("🔗 Seed arXiv page", source.abs_url, width="stretch")
        if source.doi:
            seed_cols[2].link_button(
                "🏷️ Seed DOI", f"https://doi.org/{source.doi}", width="stretch"
            )
            save_seed_col = seed_cols[3]
        else:
            save_seed_col = seed_cols[2]

        is_seed_saved = source.id in st.session_state.get("saved_papers", [])
        save_seed_col.button(
            "🔖 Saved" if is_seed_saved else "🔖 Save seed paper",
            key=f"seed-save-{source.id}",
            on_click=_toggle_saved_paper,
            args=(source.id,),
            width="stretch",
        )

    st.markdown(f"Papers most similar to **{source.title}** ({source.id})")
    for result in neighbours:
        render_card(result, "similar")


def reading_list_tab(engine: SearchEngine) -> None:
    st.markdown(
        "Curate your session reading list, compare papers side-by-side, and export a "
        "unified bibliography for your literature review."
    )
    catalog = paper_catalog()
    add_col, btn_col, clear_col = st.columns([3, 1, 1])
    chosen_to_add = add_col.selectbox(
        "Quick-add a paper from the index",
        options=list(catalog),
        index=None,
        key="reading_list_picker",
        format_func=lambda pid: catalog.get(pid, pid),
        placeholder="Search by arXiv ID or paper title to bookmark…",
        label_visibility="collapsed",
    )
    if btn_col.button("➕ Add to Reading List", width="stretch") and chosen_to_add:
        if chosen_to_add not in st.session_state.saved_papers:
            st.session_state.saved_papers.append(chosen_to_add)
            st.toast(f"Added arXiv:{chosen_to_add} to Reading List.")

    saved_ids: list[str] = list(st.session_state.get("saved_papers", []))
    clear_col.button(
        "🗑️ Clear All",
        on_click=_clear_saved_papers,
        disabled=not saved_ids,
        width="stretch",
    )

    if not saved_ids:
        st.info(
            "Your Reading List is currently empty. Click **🔖 Save paper** on any search "
            "result card, or pick a paper from the dropdown above."
        )
        return

    papers: list[Paper] = []
    for pid in saved_ids:
        try:
            papers.append(engine.get(pid))
        except KeyError:
            continue

    m1, m2, m3, m4 = st.columns(4)
    years = [p.year for p in papers]
    m1.metric("Saved Papers", f"{len(papers)}")
    m2.metric("Year Range", f"{min(years)}–{max(years)}" if years else "–")
    m3.metric("Distinct Categories", f"{len({c for p in papers for c in p.categories})}")
    m4.metric("With Publisher DOI", f"{sum(1 for p in papers if p.doi)} / {len(papers)}")

    st.markdown("##### 🔬 Side-by-Side Comparison Matrix")
    extractor = get_keyword_extractor()
    matrix_rows = [
        {
            "arXiv ID": p.id,
            "Year": p.year,
            "Primary Cat": p.primary_category,
            "Title": p.title,
            "Authors": ", ".join(p.authors[:3]) + (" et al." if len(p.authors) > 3 else ""),
            "Key Terms (TF-IDF)": " · ".join(extractor.extract(p.abstract, k=4)),
            "Words": len(p.abstract.split()),
            "DOI": p.doi or "arXiv DataCite",
        }
        for p in papers
    ]
    st.dataframe(matrix_rows, width="stretch", hide_index=True)

    st.markdown("##### 📚 Unified Bibliography Generator")
    bib_c1, bib_c2 = st.columns([3, 1])
    rl_style = bib_c1.radio(
        "Bibliography style",
        list(FORMATS),
        horizontal=True,
        key="rl_cite_style",
        label_visibility="collapsed",
    )
    all_cites = "\n\n".join(FORMATS[rl_style](p) for p in papers)
    bib_c2.download_button(
        f"⬇️ Download Reading List ({rl_style})",
        data=all_cites,
        file_name="reading_list.bib" if rl_style == "BibTeX" else "reading_list_citations.txt",
        mime="text/plain",
        key="dl_reading_list",
        width="stretch",
    )
    st.code(all_cites, language="bibtex" if rl_style == "BibTeX" else None, wrap_lines=True)

    st.markdown("##### 🗂️ Saved Paper Details")
    for idx, p in enumerate(papers, 1):
        with st.container(border=True):
            c_info, c_act = st.columns([5, 2])
            c_info.markdown(f"**{idx}. {p.title}** (`arXiv:{p.id}` · {p.published_date})")
            c_info.caption(", ".join(p.authors) + " · " + " ".join(p.categories))
            act1, act2, act3 = c_act.columns(3)
            act1.link_button("📄 PDF", p.pdf_url, width="stretch")
            act2.button(
                "🧭 Similar",
                key=f"rl-sim-{p.id}",
                on_click=_select_similar,
                args=(p.id,),
                width="stretch",
            )
            act3.button(
                "✕ Remove",
                key=f"rl-rm-{p.id}",
                on_click=_toggle_saved_paper,
                args=(p.id,),
                width="stretch",
            )


def analytics_tab() -> None:
    st.markdown(
        "Quantitative overview of the 1,000-paper stratified arXiv corpus and head-to-head "
        "evaluation benchmarks (`HCMUT-AILib Dense Semantic` vs `Okapi BM25`)."
    )
    stats = corpus_statistics()
    eval_data = load_evaluation_data()

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### 📅 Stratified Sampling by Publication Year (2021–2025)")
            st.bar_chart(stats["by_year"], color="#38BDF8")
            st.caption(
                "200 unique papers sampled per year across 4 arXiv Computer Science categories "
                "(50 papers × 4 categories × 5 years = 1,000 records)."
            )
    with c2:
        with st.container(border=True):
            st.markdown("##### 🏷️ Coverage Across Sampled arXiv Categories (inc. Cross-Lists)")
            st.bar_chart(stats["by_sampled_cat"], color="#818CF8")
            st.caption(
                "Papers frequently cross-list across multiple CS subcategories (e.g. a cs.CL paper "
                "also tagged with cs.AI and cs.LG)."
            )

    if eval_data:
        sem = eval_data.get("semantic", {})
        bm25 = eval_data.get("bm25", {})
        lat = eval_data.get("latency", {})
        rss = eval_data.get("rss_mb", {})

        st.markdown("##### 🏆 Benchmark Evaluation Summary (30 Queries · 500 Pooled Candidates)")
        b1, b2, b3, b4 = st.columns(4)
        b1.metric(
            "Mean Reciprocal Rank (MRR)",
            f"{sem.get('mrr', 0):.3f}",
            f"+{sem.get('mrr', 0) - bm25.get('mrr', 0):.3f} vs BM25 ({bm25.get('mrr', 0):.3f})",
        )
        b2.metric(
            "Precision@5 (Ceiling 0.367)",
            f"{sem.get('p@5', 0):.3f}",
            f"+{sem.get('p@5', 0) - bm25.get('p@5', 0):.3f} vs BM25 ({bm25.get('p@5', 0):.3f})",
        )
        b3.metric(
            "Pool Recall@10",
            f"{sem.get('recall@10', 0):.1%}",
            f"BM25: {bm25.get('recall@10', 0):.1%}",
        )
        b4.metric(
            "Query Latency (Mean / p95)",
            f"{lat.get('mean_s', 0) * 1000:.1f} ms",
            f"p95: {lat.get('p95_s', 0) * 1000:.1f} ms · Max: {lat.get('max_s', 0) * 1000:.1f} ms",
        )

        per_query = eval_data.get("per_query", [])
        if per_query:
            with st.container(border=True):
                st.markdown("##### 🔬 Interactive 30-Query Benchmark Explorer")
                q_options = {
                    f"{row['qid']} — {row['query']} (Semantic RR={row['rr_semantic']:.2f}, BM25 RR={row['rr_bm25']:.2f})": row["query"]
                    for row in per_query
                }
                q_col, run_col = st.columns([4, 1])
                picked_q_label = q_col.selectbox(
                    "Select a benchmark query to test live in the Search tab",
                    options=list(q_options),
                    label_visibility="collapsed",
                )
                if run_col.button(
                    "🚀 Test in Search",
                    on_click=_set_query,
                    args=(q_options[picked_q_label],),
                    width="stretch",
                ):
                    st.toast("Loaded benchmark query into the Search tab!")

                table_rows = [
                    {
                        "ID": r["qid"],
                        "Natural-Language Benchmark Query": r["query"],
                        "Relevant in Pool": r["n_relevant"],
                        "Semantic RR": round(r["rr_semantic"], 3),
                        "BM25 RR": round(r["rr_bm25"], 3),
                        "Outcome": (
                            "🟢 Semantic Win"
                            if r["rr_semantic"] > r["rr_bm25"]
                            else ("🟡 Tie" if r["rr_semantic"] == r["rr_bm25"] else "🔴 BM25 Win")
                        ),
                    }
                    for r in per_query
                ]
                st.dataframe(table_rows, width="stretch", hide_index=True)

        sys_c1, sys_c2 = st.columns([1.3, 1])
        with sys_c1:
            if PCA_FIG_PATH.exists():
                with st.container(border=True):
                    st.markdown("##### 🌌 384-D Embedding Space Projection (PCA)")
                    st.image(str(PCA_FIG_PATH), width="stretch")
        with sys_c2:
            with st.container(border=True):
                st.markdown("##### ⚙️ Runtime & Resource Profile")
                st.markdown(
                    f"- **Index build time (1,000 papers):** `{eval_data.get('index_build_s', 51.5):.1f} s` (target < 180 s)\n"
                    f"- **Cold start (model + ChromaDB):** `{eval_data.get('startup_s', 15.3):.1f} s` (cached per server)\n"
                    f"- **Memory footprint (RSS):** `{rss.get('after_queries', 577.1):.0f} MB` (baseline `{rss.get('before_load', 28.5):.0f} MB`)\n"
                    f"- **Evaluated trials:** `{lat.get('n', 150)}` timed queries (30 queries × 5 rounds)\n"
                    f"- **Platform:** `{eval_data.get('environment', {}).get('platform', 'Windows 11')}`"
                )


def about_tab(engine: SearchEngine) -> None:
    lo, hi = year_bounds()
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Indexed Papers", f"{len(engine):,}")
    m2.metric("Publication Window", f"{lo}–{hi}")
    m3.metric("Embedding Dimension", "384-d (CPU)")
    m4.metric("Privacy Mode", "100% Local")

    st.markdown(f"""
**HCMUT-AILib** is a zero-cost, local-first semantic search engine for academic papers,
built for CO2001 – Professional Skills for Engineers (HCMUT).

* **Collection:** {len(engine):,} open-access arXiv papers ({", ".join(CATEGORY_NAMES)}).
* **Model:** `{indexer.MODEL_NAME}` (384-dimensional sentence embeddings, CPU only).
* **Index:** ChromaDB, cosine distance, stored locally in `data/processed/vector_index/`.
* **Score:** "Match" is (1 + cosine similarity) / 2. It ranks papers; it is not a
  measure of quality or truth — always read the paper before citing it.
* **Privacy:** queries never leave your computer and are not logged.
* **Limitations:** the model is English-only; the collection is a 1,000-paper sample,
  so missing results do not mean the literature does not exist.
""")

    col_left, col_right = st.columns(2)
    with col_left:
        with st.container(border=True):
            st.markdown(
                "### 🎯 Understanding the Match Score\n"
                "Each paper's **Match %** is computed from the cosine similarity between your "
                "query embedding and the paper's `title + abstract` embedding, rescaled to "
                "`[0, 1]` via `(1 + cos) / 2`.\n\n"
                "- Compare scores **only within the same query**.\n"
                "- A high percentage indicates strong topical overlap, not peer-reviewed truth."
            )
    with col_right:
        with st.container(border=True):
            st.markdown(
                "### 👥 CO2001 Project Team (Group 13)\n"
                "| Member | Role |\n"
                "| :--- | :--- |\n"
                "| **Nguyễn Phước Bảo Phú** | Project Lead & System Architect |\n"
                "| **Từ Công Phú** | Data & Retrieval Engineer |\n"
                "| **Nguyễn Vi Kiên** | Frontend & Integration Engineer |\n"
                "| **Trần Kiện Đông** | QA, Ethics & Compliance Lead |"
            )

    if ARCH_FIG_PATH.exists():
        with st.expander("🏗️ View Four-Layer System Architecture Diagram"):
            st.image(str(ARCH_FIG_PATH), width="stretch")

    st.caption(
        "Metadata courtesy of arXiv. Thank you to arXiv for use of its open access "
        "interoperability. HCMUT-AILib is not affiliated with or endorsed by arXiv. "
        "Source code: [github.com/HCMUT-Fus/hcmut-ailib](https://github.com/HCMUT-Fus/hcmut-ailib) "
        "(GNU GPLv3)."
    )


def main() -> None:
    init_session_state()
    inject_styles()

    try:
        engine = get_engine()
    except Exception as exc:  # missing index is the common first-run error
        st.title("📚 HCMUT-AILib")
        st.error(
            f"Could not open the vector index ({exc}). Build it first with "
            "`python -m src.indexer`."
        )
        st.stop()

    render_professional_header(engine)

    lo, hi = year_bounds()
    with st.sidebar:
        st.header("🎛️ Workbench Controls")

        st.html('<div class="sidebar-section-title">1 · Retrieval &amp; Scope Filters</div>')
        # Keep slider[0], slider[1], multiselect[0], text_input[0] order for tests/test_app.py
        top_k = st.slider("Number of results (Top-K)", 1, 20, 10, key="filter_top_k")
        years = st.slider("Publication year", lo, hi, (lo, hi), key="filter_years")
        categories = st.multiselect(
            "arXiv categories",
            list(CATEGORY_NAMES),
            key="filter_categories",
            format_func=lambda c: f"{c} — {CATEGORY_NAMES[c]}",
        )
        author = st.text_input(
            "Author contains",
            key="filter_author",
            placeholder="e.g. Nguyen",
        )

        st.html('<div class="sidebar-section-title">2 · Engine &amp; Display Settings</div>')
        retrieval_mode = st.selectbox(
            "Retrieval engine mode",
            RETRIEVAL_MODES,
            key="retrieval_mode",
            help="Compare Dense Semantic embeddings against Hybrid RRF or Okapi BM25 lexical search.",
        )
        min_score_pct = st.slider(
            "Minimum match score (%)",
            0,
            85,
            0,
            step=5,
            key="min_score_pct",
            help="Hide results whose normalized score falls below this threshold.",
        )
        sort_by = st.selectbox("Sort results by", SORT_OPTIONS, key="sort_by")
        view_mode = st.selectbox("Result layout mode", VIEW_MODES, key="view_mode")
        only_doi = st.toggle("Require publisher DOI", value=False, key="only_doi")

        active_filter_tags = format_active_filters(
            years,
            (lo, hi),
            categories,
            author,
            min_score_pct=min_score_pct,
            only_doi=only_doi,
            retrieval_mode=retrieval_mode,
        )
        has_custom_state = bool(
            active_filter_tags
            or top_k != 10
            or sort_by != SORT_OPTIONS[0]
            or view_mode != VIEW_MODES[0]
        )
        st.button(
            "🔄 Reset filters",
            on_click=_reset_filters,
            args=(lo, hi),
            disabled=not has_custom_state,
            width="stretch",
        )

        if st.session_state.get("query_history"):
            with st.expander("🕘 Recent Session Queries", expanded=False):
                for idx, past_q in enumerate(st.session_state.query_history):
                    st.button(
                        f"↩ {past_q[:34]}{'…' if len(past_q) > 34 else ''}",
                        key=f"hist-q-{idx}",
                        on_click=_set_query,
                        args=(past_q,),
                        width="stretch",
                    )

        st.divider()
        st.caption(
            f"📊 **{len(engine):,} papers indexed** ({lo}–{hi})  \n"
            f"🧠 **Model:** `{indexer.MODEL_NAME}`  \n"
            f"🔖 **Reading List:** `{len(st.session_state.saved_papers)}` saved  \n"
            "🔒 **Local-first:** zero telemetry"
        )

    filters = {
        "top_k": top_k,
        "year_range": None if years == (lo, hi) else years,
        "categories": categories or None,
        "author": author.strip() or None,
    }
    search, similar, reading_list, analytics, about = st.tabs([
        "🔎 Semantic Search",
        "🧭 Similar Papers",
        f"🔖 Reading List ({len(st.session_state.saved_papers)})",
        "📊 Corpus & Benchmark",
        "ℹ️ System & About",
    ])
    with search:
        search_tab(
            engine,
            filters=filters,
            active_filter_tags=active_filter_tags,
            retrieval_mode=retrieval_mode,
            min_score_pct=min_score_pct,
            sort_by=sort_by,
            view_mode=view_mode,
            only_doi=only_doi,
        )
    with similar:
        similar_tab(engine, top_k)
    with reading_list:
        reading_list_tab(engine)
    with analytics:
        analytics_tab()
    with about:
        about_tab(engine)

    if st.session_state.pop("_switch_to_similar", False):
        components.html(
            """
            <script>
            const tabs = window.parent.document.querySelectorAll('button[data-baseweb="tab"]');
            if (tabs.length > 1) {
                tabs[1].click();
                window.parent.scrollTo({ top: 0, behavior: 'smooth' });
            }
            </script>
            """,
            height=0,
        )


main()
