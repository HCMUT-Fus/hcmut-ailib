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
from src.search_engine import Paper, SearchEngine, SearchResult  # noqa: E402

CATEGORY_NAMES = {
    "cs.AI": "Artificial Intelligence",
    "cs.LG": "Machine Learning",
    "cs.CL": "Computation and Language",
    "cs.IR": "Information Retrieval",
    "cs.CV": "Computer Vision",
    "cs.RO": "Robotics",
    "cs.HC": "Human-Computer Interaction",
    "cs.CR": "Cryptography and Security",
    "cs.CY": "Computers and Society",
    "cs.SD": "Sound",
    "cs.SI": "Social and Information Networks",
    "cs.SE": "Software Engineering",
    "cs.NE": "Neural and Evolutionary Computing",
    "cs.DB": "Databases",
    "stat.ML": "Machine Learning (Stats)",
    "eess.AS": "Audio and Speech Processing",
    "eess.IV": "Image and Video Processing",
}
CORE_CATEGORIES = ("cs.AI", "cs.LG", "cs.CL", "cs.IR")

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
    "Dense Semantic (mdbr-leaf-ir)",
    "Hybrid RRF (Semantic + BM25)",
    "Lexical Baseline (Okapi BM25)",
)
SORT_OPTIONS = ("Relevance", "Newest first", "Oldest first", "Title (A–Z)")
VIEW_MODES = ("Detailed Cards", "Cards + Comparison Matrix", "Compact Cards")
ABSTRACT_PREVIEW = 320

EVAL_JSON_PATH = REPO_ROOT / "reports" / "results" / "evaluation.json"
SCIFACT_JSON_PATH = REPO_ROOT / "reports" / "results" / "scifact_evaluation.json"
PCA_FIG_PATH = REPO_ROOT / "reports" / "figures" / "embedding_pca.png"
ARCH_FIG_PATH = REPO_ROOT / "docs" / "architecture.png"

st.set_page_config(page_title="HCMUT-AILib", page_icon="📚", layout="wide")


def inject_styles() -> None:
    """Apply vibrant multi-color dark-mode styling with keyframe animations and motion."""
    st.html("""
    <style>
        /* Keyframe Animations */
        @keyframes auroraBg {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes rainbowFlow {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseBeacon {
            0%, 100% { transform: scale(1); opacity: 1; box-shadow: 0 0 8px currentColor; }
            50%      { transform: scale(1.32); opacity: 0.78; box-shadow: 0 0 16px currentColor; }
        }
        @keyframes cardEntrance {
            0%   { opacity: 0; transform: translateY(12px) scale(0.992); }
            100% { opacity: 1; transform: translateY(0) scale(1); }
        }
        @keyframes floatBadge {
            0%, 100% { transform: translateY(0px); }
            50%      { transform: translateY(-3px); }
        }
        @keyframes streamPulse {
            0%   { opacity: 0.35; transform: translateX(-3px); }
            50%  { opacity: 1; transform: translateX(3px); }
            100% { opacity: 0.35; transform: translateX(-3px); }
        }

        /* Root & Animated Multi-Color Aurora Background */
        .stApp {
            background:
                radial-gradient(circle at 12% 8%, rgba(56, 189, 248, 0.14) 0%, transparent 38%),
                radial-gradient(circle at 88% 12%, rgba(168, 85, 247, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 50% 85%, rgba(16, 185, 129, 0.10) 0%, transparent 45%),
                linear-gradient(135deg, #070b14 0%, #0d1326 35%, #111827 70%, #090d18 100%);
            background-size: 200% 200%;
            animation: auroraBg 18s ease infinite;
            color: #f1f5f9;
        }
        header[data-testid="stHeader"] {
            background: rgba(9, 13, 24, 0.72) !important;
            backdrop-filter: blur(10px);
            border-bottom: 1px solid rgba(139, 92, 246, 0.22);
        }
        .block-container {
            padding-top: 3.75rem !important;
            padding-bottom: 3.5rem !important;
            max-width: 1280px !important;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0b1120 0%, #11162b 55%, #090d1a 100%);
            border-right: 1px solid rgba(139, 92, 246, 0.28);
            box-shadow: 4px 0 24px rgba(0, 0, 0, 0.35);
        }

        /* Crisp h1 title that preserves full-color emoji rendering */
        h1 {
            font-size: 2.15rem !important;
            font-weight: 800 !important;
            letter-spacing: -0.02em !important;
            line-height: 1.2 !important;
            margin-top: 0 !important;
            margin-bottom: 0.2rem !important;
            padding-top: 0 !important;
            color: #f8fafc !important;
            text-shadow: 0 0 24px rgba(56, 189, 248, 0.28);
        }

        /* Animated Rainbow Shimmer Ribbon at top of Hero Header */
        .ailib-rainbow-bar {
            height: 4px;
            width: 100%;
            border-radius: 999px;
            background: linear-gradient(
                90deg,
                #06b6d4,
                #3b82f6,
                #8b5cf6,
                #ec4899,
                #f59e0b,
                #10b981,
                #06b6d4
            );
            background-size: 300% 100%;
            animation: rainbowFlow 6s linear infinite;
            margin-bottom: 0.75rem;
            box-shadow: 0 0 14px rgba(139, 92, 246, 0.45);
        }

        /* Top institutional status strip inside header container */
        .ailib-topbar {
            display: flex;
            flex-wrap: wrap;
            justify-content: space-between;
            align-items: center;
            gap: 0.65rem;
            padding-bottom: 0.7rem;
            margin-bottom: 0.65rem;
            border-bottom: 1px solid rgba(148, 163, 184, 0.18);
        }
        .ailib-inst-tag {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            font-size: 0.74rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            color: #e0e7ff;
            background: linear-gradient(90deg, rgba(37, 99, 235, 0.42), rgba(124, 58, 237, 0.42));
            border: 1px solid rgba(129, 140, 248, 0.48);
            padding: 0.28rem 0.82rem;
            border-radius: 999px;
            box-shadow: 0 0 16px rgba(99, 102, 241, 0.25);
        }
        .ailib-status-strip {
            display: flex;
            flex-wrap: wrap;
            gap: 0.48rem;
            align-items: center;
        }
        .ailib-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            font-size: 0.72rem;
            font-weight: 600;
            padding: 0.24rem 0.68rem;
            border-radius: 999px;
            background: rgba(15, 23, 42, 0.85);
            border: 1px solid rgba(148, 163, 184, 0.28);
            color: #e2e8f0;
            white-space: nowrap;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .ailib-pill:hover {
            transform: translateY(-2px);
        }
        .ailib-pill-online {
            border-color: rgba(52, 211, 153, 0.55);
            color: #6ee7b7;
            background: linear-gradient(135deg, rgba(6, 78, 59, 0.50), rgba(16, 185, 129, 0.18));
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.20);
        }
        .ailib-pill-cyan {
            border-color: rgba(56, 189, 248, 0.55);
            color: #7dd3fc;
            background: linear-gradient(135deg, rgba(12, 74, 110, 0.52), rgba(56, 189, 248, 0.18));
            box-shadow: 0 0 12px rgba(56, 189, 248, 0.20);
        }
        .ailib-pill-violet {
            border-color: rgba(192, 132, 252, 0.55);
            color: #e9d5ff;
            background: linear-gradient(135deg, rgba(88, 28, 135, 0.50), rgba(168, 85, 247, 0.20));
            box-shadow: 0 0 12px rgba(168, 85, 247, 0.20);
        }
        .ailib-pill-amber {
            border-color: rgba(251, 191, 36, 0.55);
            color: #fde68a;
            background: linear-gradient(135deg, rgba(120, 53, 15, 0.50), rgba(245, 158, 11, 0.20));
            box-shadow: 0 0 12px rgba(245, 158, 11, 0.18);
        }
        .ailib-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #10b981;
            color: #10b981;
            display: inline-block;
            animation: pulseBeacon 2s ease-in-out infinite;
        }

        /* Multi-Color KPI Boxes in Header */
        .ailib-kpi-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 0.65rem;
        }
        .ailib-stat-box {
            background: rgba(15, 23, 42, 0.80);
            border-radius: 12px;
            padding: 0.58rem 0.78rem;
            position: relative;
            overflow: hidden;
            transition: transform 0.22s ease, box-shadow 0.22s ease;
        }
        .ailib-stat-box:hover {
            transform: translateY(-3px);
        }
        .ailib-stat-cyan {
            border: 1px solid rgba(56, 189, 248, 0.42);
            border-top: 3px solid #38bdf8;
            box-shadow: 0 6px 18px rgba(56, 189, 248, 0.12);
        }
        .ailib-stat-violet {
            border: 1px solid rgba(168, 85, 247, 0.42);
            border-top: 3px solid #a855f7;
            box-shadow: 0 6px 18px rgba(168, 85, 247, 0.14);
        }
        .ailib-stat-emerald {
            border: 1px solid rgba(16, 185, 129, 0.42);
            border-top: 3px solid #10b981;
            box-shadow: 0 6px 18px rgba(16, 185, 129, 0.12);
        }
        .ailib-stat-label {
            font-size: 0.68rem;
            text-transform: uppercase;
            letter-spacing: 0.06em;
            color: #cbd5e1;
            margin-bottom: 0.1rem;
        }
        .ailib-stat-val {
            font-size: 1.08rem;
            font-weight: 800;
            color: #ffffff;
            line-height: 1.25;
        }
        .ailib-stat-sub-cyan {
            font-size: 0.7rem;
            color: #38bdf8;
            font-weight: 600;
            margin-top: 0.1rem;
        }
        .ailib-stat-sub-violet {
            font-size: 0.7rem;
            color: #c084fc;
            font-weight: 600;
            margin-top: 0.1rem;
        }
        .ailib-stat-sub-emerald {
            font-size: 0.7rem;
            color: #34d399;
            font-weight: 600;
            margin-top: 0.1rem;
        }

        /* Animated Live Neural Pipeline Strip */
        .ailib-pipeline {
            display: flex;
            flex-wrap: wrap;
            align-items: center;
            justify-content: space-between;
            gap: 0.45rem;
            margin-top: 0.7rem;
            padding: 0.55rem 0.85rem;
            border-radius: 10px;
            background: linear-gradient(90deg, rgba(15, 23, 42, 0.9), rgba(30, 27, 75, 0.75), rgba(15, 23, 42, 0.9));
            border: 1px solid rgba(129, 140, 248, 0.25);
        }
        .ailib-stage {
            display: inline-flex;
            align-items: center;
            gap: 0.38rem;
            font-size: 0.73rem;
            font-weight: 600;
            padding: 0.22rem 0.62rem;
            border-radius: 8px;
            background: rgba(30, 41, 59, 0.65);
            color: #94a3b8;
            border: 1px solid rgba(148, 163, 184, 0.2);
            transition: all 0.25s ease;
        }
        .ailib-stage-active-cyan {
            background: rgba(6, 182, 212, 0.18);
            color: #67e8f9;
            border-color: rgba(34, 211, 238, 0.5);
            box-shadow: 0 0 12px rgba(6, 182, 212, 0.22);
        }
        .ailib-stage-active-violet {
            background: rgba(139, 92, 246, 0.20);
            color: #ddd6fe;
            border-color: rgba(167, 139, 250, 0.55);
            box-shadow: 0 0 12px rgba(139, 92, 246, 0.25);
        }
        .ailib-stage-active-pink {
            background: rgba(236, 72, 153, 0.20);
            color: #fbcfe8;
            border-color: rgba(244, 114, 182, 0.55);
            box-shadow: 0 0 12px rgba(236, 72, 153, 0.25);
        }
        .ailib-stage-active-emerald {
            background: rgba(16, 185, 129, 0.20);
            color: #a7f3d0;
            border-color: rgba(52, 211, 153, 0.55);
            box-shadow: 0 0 12px rgba(16, 185, 129, 0.25);
        }
        .ailib-arrow {
            color: #818cf8;
            font-size: 0.85rem;
            font-weight: 700;
            animation: streamPulse 1.6s ease-in-out infinite;
        }

        /* Bordered Containers / Cards with Entrance Motion & Multi-Color Glow */
        div[data-testid="stVerticalBlockBorderWrapper"] {
            background: linear-gradient(145deg, rgba(17, 24, 39, 0.88) 0%, rgba(15, 23, 42, 0.92) 100%);
            border: 1px solid rgba(56, 189, 248, 0.24) !important;
            border-radius: 14px !important;
            animation: cardEntrance 0.38s cubic-bezier(0.22, 1, 0.36, 1) both;
            transition: transform 0.22s cubic-bezier(0.22, 1, 0.36, 1),
                        border-color 0.22s ease,
                        box-shadow 0.22s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            transform: translateY(-3px);
            border-color: rgba(168, 85, 247, 0.55) !important;
            box-shadow:
                0 10px 26px -6px rgba(56, 189, 248, 0.20),
                0 6px 18px -4px rgba(168, 85, 247, 0.18);
        }

        /* Animated Multi-Color Progress Bars for Match Scores */
        div[data-testid="stProgress"] > div > div > div > div {
            background: linear-gradient(
                90deg,
                #06b6d4 0%,
                #8b5cf6 45%,
                #ec4899 75%,
                #10b981 100%
            ) !important;
            background-size: 200% 100% !important;
            animation: rainbowFlow 4s linear infinite !important;
            border-radius: 999px !important;
        }

        /* Metrics with Colorful Borders & Hover Lift */
        div[data-testid="stMetric"] {
            background: linear-gradient(135deg, rgba(15, 23, 42, 0.85), rgba(30, 27, 75, 0.45));
            border: 1px solid rgba(99, 102, 241, 0.32);
            border-radius: 12px;
            padding: 0.5rem 0.72rem;
            transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
        }
        div[data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(56, 189, 248, 0.6);
            box-shadow: 0 6px 18px rgba(56, 189, 248, 0.16);
        }
        div[data-testid="stMetricValue"] {
            background: linear-gradient(90deg, #38bdf8, #a855f7, #ec4899);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: 800 !important;
        }

        /* Interactive Buttons & Link Buttons */
        .stButton > button, .stLinkButton > a, .stDownloadButton > button {
            border-radius: 10px !important;
            border: 1px solid rgba(99, 102, 241, 0.32) !important;
            background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.92)) !important;
            transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease !important;
        }
        .stButton > button:hover, .stLinkButton > a:hover, .stDownloadButton > button:hover {
            transform: translateY(-2px) !important;
            border-color: rgba(56, 189, 248, 0.68) !important;
            box-shadow: 0 6px 16px rgba(56, 189, 248, 0.22), 0 0 10px rgba(168, 85, 247, 0.16) !important;
        }

        /* Tabs bar with Gradient Active Indicator */
        div[data-baseweb="tab-list"] {
            gap: 0.4rem;
            background: rgba(15, 23, 42, 0.85);
            padding: 0.4rem;
            border-radius: 12px;
            border: 1px solid rgba(139, 92, 246, 0.28);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.28);
        }
        button[data-baseweb="tab"] {
            font-weight: 600 !important;
            font-size: 0.9rem !important;
            padding: 0.5rem 1rem !important;
            border-radius: 9px !important;
            color: #94a3b8 !important;
            transition: all 0.2s ease !important;
        }
        button[data-baseweb="tab"]:hover {
            color: #e2e8f0 !important;
            background: rgba(99, 102, 241, 0.12) !important;
        }
        button[data-baseweb="tab"][aria-selected="true"] {
            background: linear-gradient(135deg, rgba(6, 182, 212, 0.24), rgba(139, 92, 246, 0.28)) !important;
            color: #f8fafc !important;
            border: 1px solid rgba(56, 189, 248, 0.45) !important;
            box-shadow: 0 0 16px rgba(56, 189, 248, 0.22) !important;
        }

        /* Sidebar section header chips */
        .sidebar-section-title {
            font-size: 0.72rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.08em;
            background: linear-gradient(90deg, #38bdf8, #c084fc);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-top: 0.55rem;
            margin-bottom: 0.28rem;
            display: inline-block;
        }
    </style>
    """)


@st.cache_resource(show_spinner="Loading embedding model and vector index…")
def get_engine() -> SearchEngine:
    return SearchEngine()


@st.cache_resource
def get_keyword_extractor() -> KeywordExtractor:
    return KeywordExtractor([p["abstract"] for p in ingest.load()])


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
def load_scifact_data() -> dict | None:
    if SCIFACT_JSON_PATH.exists():
        try:
            return json.loads(SCIFACT_JSON_PATH.read_text(encoding="utf-8"))
        except Exception:
            return None
    return None


@st.cache_data
def corpus_statistics() -> dict:
    records = load_raw_corpus()
    by_year = Counter(int(r["published_date"][:4]) for r in records)
    by_primary = Counter(r["primary_category"] for r in records)
    by_sampled_cat = Counter(
        cat for r in records for cat in r["categories"] if cat in CORE_CATEGORIES
    )
    doi_count = sum(1 for r in records if r.get("doi"))
    word_counts = [len(r["abstract"].split()) for r in records]
    author_counts = [len(r["authors"]) for r in records]
    return {
        "total": len(records),
        "by_year": dict(sorted(by_year.items())),
        "by_primary": dict(by_primary.most_common(10)),
        "by_sampled_cat": {c: by_sampled_cat[c] for c in CORE_CATEGORIES},
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
    st.session_state.use_rerank = False
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


CATEGORY_BADGE_COLORS = {
    "cs.AI": "violet",
    "cs.LG": "blue",
    "cs.CL": "green",
    "cs.IR": "orange",
    "cs.CV": "red",
    "cs.RO": "violet",
    "cs.HC": "green",
    "cs.CR": "red",
    "stat.ML": "blue",
}


def format_category_badges(paper: Paper) -> str:
    badges = []
    for idx, cat in enumerate(paper.categories):
        color = CATEGORY_BADGE_COLORS.get(cat, "blue" if cat in CATEGORY_NAMES else "gray")
        if cat in CATEGORY_NAMES:
            label = f"{cat} · {CATEGORY_NAMES[cat]}" if idx == 0 else cat
            badges.append(f":{color}-badge[{label}]")
        else:
            badges.append(f":gray-badge[{cat}]")
    return " ".join(badges)


def confidence_badge(score: float) -> str:
    if score >= 0.78:
        return ":green-badge[High Match]"
    if score >= 0.68:
        return ":blue-badge[Moderate Match]"
    return ":orange-badge[Exploratory]"


def format_active_filters(
    years: tuple[int, int],
    bounds: tuple[int, int],
    categories: list[str],
    author: str,
    min_score_pct: int = 0,
    only_doi: bool = False,
    retrieval_mode: str = RETRIEVAL_MODES[0],
    use_rerank: bool = False,
) -> list[str]:
    summary: list[str] = []
    if retrieval_mode != RETRIEVAL_MODES[0]:
        summary.append(f"Mode: {retrieval_mode.split(' (')[0]}")
    if use_rerank:
        summary.append("Cross-Encoder Rerank")
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
    engine: SearchEngine | None = None,
) -> bool:
    if year_range and not (year_range[0] <= paper.year <= year_range[1]):
        return False
    if categories and not any(c in paper.categories for c in categories):
        return False
    if author:
        if engine is not None:
            return paper.id in engine.author_index.match(author)
        if author.strip().lower() not in "; ".join(paper.authors).lower():
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
    rerank: bool = False,
) -> list[SearchResult]:
    """Run semantic, hybrid RRF, or Okapi BM25 retrieval via SearchEngine."""
    if retrieval_mode.startswith("Dense Semantic"):
        return engine.search(
            query,
            top_k=top_k,
            year_range=year_range,
            categories=categories,
            author=author,
            rerank=rerank,
        )

    if retrieval_mode.startswith("Hybrid RRF"):
        return engine.hybrid_search(
            query,
            top_k=top_k,
            year_range=year_range,
            categories=categories,
            author=author,
            rerank=rerank,
        )

    # Lexical Baseline (Okapi BM25)
    bm25 = engine.bm25
    raw_scores = bm25.scores(query)
    max_bm25 = max(raw_scores) if raw_scores else 0.0
    ranked = sorted(zip(raw_scores, bm25.ids), key=lambda x: -x[0])
    fetch_k = max(top_k * 2, 15) if rerank else top_k
    results: list[SearchResult] = []
    for sc, pid in ranked:
        if sc <= 0:
            break
        paper = engine.get(pid)
        if not paper_matches_filters(paper, year_range, categories, author, engine=engine):
            continue
        norm_sc = min(0.99, max(0.05, sc / max_bm25)) if max_bm25 > 0 else 0.0
        results.append(SearchResult(paper=paper, score=norm_sc, rank=len(results) + 1))
        if len(results) == fetch_k:
            break
    if rerank and results:
        return engine.rerank(query, results, top_k=top_k)
    return results[:top_k]


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
    """Render a unified, vibrant, animated dark-mode institutional header card."""
    stats = corpus_statistics()
    saved_count = len(st.session_state.get("saved_papers", []))
    mode = st.session_state.get("retrieval_mode", RETRIEVAL_MODES[0])
    rerank_on = bool(st.session_state.get("use_rerank", False))

    is_dense = mode.startswith("Dense") or mode.startswith("Hybrid")
    is_hybrid = mode.startswith("Hybrid") or mode.startswith("Lexical")
    s1_cls = "ailib-stage ailib-stage-active-cyan" if is_dense else "ailib-stage"
    s2_cls = "ailib-stage ailib-stage-active-violet" if is_hybrid else "ailib-stage ailib-stage-active-cyan"
    s3_cls = "ailib-stage ailib-stage-active-pink" if rerank_on else "ailib-stage"
    s4_cls = "ailib-stage ailib-stage-active-emerald"

    with st.container(border=True):
        st.html(f"""
        <div class="ailib-rainbow-bar"></div>
        <div class="ailib-topbar">
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
                <span class="ailib-pill ailib-pill-violet">
                    ⚡ ChromaDB HNSW · Cosine
                </span>
                <span class="ailib-pill ailib-pill-amber">
                    🔒 Air-Gapped Local
                </span>
            </div>
        </div>
        """)

        title_col, status_col = st.columns([1.32, 1.68], vertical_alignment="center")
        with title_col:
            st.title("📚 HCMUT-AILib")
            st.caption(
                "Semantic search & research assistant for open-access academic papers · "
                "Dense Vector + Hybrid RRF + Cross-Encoder Workbench"
            )
        with status_col:
            st.html(f"""
            <div class="ailib-kpi-row">
                <div class="ailib-stat-box ailib-stat-cyan">
                    <div class="ailib-stat-label">Indexed Corpus</div>
                    <div class="ailib-stat-val">{len(engine):,} Papers</div>
                    <div class="ailib-stat-sub-cyan">arXiv 2021–2025 · Stratified</div>
                </div>
                <div class="ailib-stat-box ailib-stat-violet">
                    <div class="ailib-stat-label">Benchmark MRR</div>
                    <div class="ailib-stat-val">0.911</div>
                    <div class="ailib-stat-sub-violet">+31.5% vs Okapi BM25</div>
                </div>
                <div class="ailib-stat-box ailib-stat-emerald">
                    <div class="ailib-stat-label">Reading List</div>
                    <div class="ailib-stat-val">{saved_count} Saved</div>
                    <div class="ailib-stat-sub-emerald">{stats['doi_pct']:.1f}% Publisher DOIs</div>
                </div>
            </div>
            """)

        st.html(f"""
        <div class="ailib-pipeline">
            <span class="{s1_cls}">1 · 🧬 384-D Neural Embedder</span>
            <span class="ailib-arrow">━━▶</span>
            <span class="{s2_cls}">2 · 🧭 {'Hybrid RRF (HNSW + BM25)' if is_hybrid else 'ChromaDB HNSW Cosine'}</span>
            <span class="ailib-arrow">━━▶</span>
            <span class="{s3_cls}">3 · 🎯 Cross-Encoder Rerank {'(ON)' if rerank_on else '(Ready)'}</span>
            <span class="ailib-arrow">━━▶</span>
            <span class="{s4_cls}">4 · ✨ TF-IDF Key Terms &amp; Citations</span>
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
        head, score = st.columns([4.8, 1.2], vertical_alignment="top")
        head.markdown(f"#### {result.rank}. {paper.title}")
        score.metric(
            "Match",
            f"{result.score:.0%}",
            help="Semantic Similarity Score: Cosine similarity rescaled to 0–1; compare within this query only.",
        )
        score.progress(result.score)

        authors = ", ".join(paper.authors[:6]) + (
            f" et al. (+{len(paper.authors) - 6} more)" if len(paper.authors) > 6 else ""
        )
        badges = format_category_badges(paper)
        tier = confidence_badge(result.score)
        doi_badge = f" :green-badge[DOI: {paper.doi}]" if paper.doi else ""
        head.markdown(
            f"**{authors}** · 📅 `{paper.published_date}` · `arXiv:{paper.id}`  \n"
            f"{tier} {badges}{doi_badge}"
        )

        keywords = get_keyword_extractor().extract(paper.abstract, k=5)
        if keywords:
            kw_colors = ("violet", "blue", "green", "orange", "red")
            kw_pills = " ".join(
                f":{kw_colors[i % len(kw_colors)]}-badge[✦ {kw}]"
                for i, kw in enumerate(keywords)
            )
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
    k1.metric("Stratified Corpus", f"{stats['total']:,} Papers", "4 CS domains · 2021–2025")
    k2.metric("Mean Abstract Length", f"{stats['avg_words']:.0f} Words", "Title + Abstract embedded")
    k3.metric("Mean Query Latency", "13.6 ms", "p95: 17.1 ms (CPU)")
    k4.metric("Top-1 Accuracy", "83.3%", "25 / 30 benchmark queries")

    cols = st.columns(3)
    with cols[0]:
        with st.container(border=True):
            st.markdown(
                "### 🎯 Semantic, Hybrid & Rerank\n"
                f"Switch between **Dense Semantic** (`{indexer.MODEL_NAME}`), "
                "**Hybrid RRF** (Reciprocal Rank Fusion), and **Okapi BM25**, plus optional "
                "**Cross-Encoder Neural Re-ranking** in the sidebar."
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
    use_rerank: bool,
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
            rerank=use_rerank,
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
    stats = corpus_statistics()
    eval_data = load_evaluation_data()
    scifact_data = load_scifact_data()

    st.markdown(
        f"Quantitative overview of the **{stats['total']:,}-paper** stratified arXiv corpus and "
        "head-to-head evaluation benchmarks (`Dense Semantic`, `Hybrid RRF`, and `Okapi BM25`)."
    )

    c1, c2 = st.columns(2)
    with c1:
        with st.container(border=True):
            st.markdown("##### 📅 Stratified Sampling by Publication Year (2021–2025)")
            st.bar_chart(stats["by_year"], color="#38BDF8")
            per_year = stats["total"] // max(len(stats["by_year"]), 1)
            st.caption(
                f"{per_year:,} unique papers sampled per year across 4 core CS categories "
                f"(`cs.AI`, `cs.LG`, `cs.CL`, `cs.IR`; {stats['total']:,} total records)."
            )
    with c2:
        with st.container(border=True):
            st.markdown("##### 🏷️ Coverage Across Core arXiv Categories (inc. Cross-Lists)")
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

        st.markdown("##### 🏆 HCMUT-AILib 30-Query Benchmark (500 Pooled Candidates)")
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

    if scifact_data:
        st.markdown(
            f"##### 🧪 Standard BEIR-SciFact Benchmark ({scifact_data.get('n_documents', 5183):,} Docs · "
            f"{scifact_data.get('n_queries', 300)} Queries)"
        )
        m_ailib = scifact_data.get("metrics_ailib", {})
        m_beir = scifact_data.get("metrics_beir", {})
        scifact_rows = []
        for key, label in [
            ("bm25", "Okapi BM25 (Lexical Baseline)"),
            ("semantic", f"Dense Semantic ({indexer.MODEL_NAME})"),
            ("hybrid", "Hybrid RRF (Dense + BM25)"),
        ]:
            a_row = m_ailib.get(key, {})
            b_row = m_beir.get(key, {})
            scifact_rows.append({
                "Retrieval System": label,
                "MRR": round(a_row.get("mrr", 0.0), 4),
                "NDCG@10": round(b_row.get("ndcg", {}).get("NDCG@10", 0.0), 4),
                "MAP@10": round(b_row.get("map", {}).get("MAP@10", 0.0), 4),
                "Recall@10": round(b_row.get("recall", {}).get("Recall@10", 0.0), 4),
                "Recall@100": round(b_row.get("recall", {}).get("Recall@100", 0.0), 4),
                "P@5": round(a_row.get("p@5", 0.0), 4),
            })
        st.dataframe(scifact_rows, width="stretch", hide_index=True)

    if eval_data:
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
                    f"- **Index build time:** `{eval_data.get('index_build_s', 51.5):.1f} s` (target < 180 s)\n"
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

* **Collection:** {len(engine):,} open-access arXiv papers ({", ".join(CORE_CATEGORIES)}).
* **Model:** `{indexer.MODEL_NAME}` (384-dimensional sentence embeddings, CPU only).
* **Index:** ChromaDB, cosine distance, stored locally in `data/processed/vector_index/`.
* **Score:** "Match" is (1 + cosine similarity) / 2. It ranks papers; it is not a
  measure of quality or truth — always read the paper before citing it.
* **Privacy:** queries never leave your computer and are not logged.
* **Limitations:** the model is English-only; the collection is a stratified arXiv sample,
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
            list(CORE_CATEGORIES),
            key="filter_categories",
            format_func=lambda c: f"{c} — {CATEGORY_NAMES[c]}",
        )
        author = st.text_input(
            "Author contains",
            key="filter_author",
            placeholder="e.g. Nguyen / Nguyễn",
        )

        st.html('<div class="sidebar-section-title">2 · Engine &amp; Display Settings</div>')
        retrieval_mode = st.selectbox(
            "Retrieval engine mode",
            RETRIEVAL_MODES,
            key="retrieval_mode",
            help="Compare Dense Semantic embeddings against Hybrid RRF or Okapi BM25 lexical search.",
        )
        use_rerank = st.toggle(
            "⚡ Cross-Encoder neural re-rank",
            value=False,
            key="use_rerank",
            help="Re-rank top candidates jointly with cross-encoder/ms-marco-MiniLM-L-2-v2.",
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
            use_rerank=use_rerank,
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
            use_rerank=use_rerank,
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
