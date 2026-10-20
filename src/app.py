"""HCMUT-AILib Streamlit dashboard. Run with ``streamlit run src/app.py``."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src import ingest, indexer  # noqa: E402
from src.citations import FORMATS  # noqa: E402
from src.keywords import KeywordExtractor  # noqa: E402
from src.search_engine import SearchEngine, SearchResult  # noqa: E402

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
]
ABSTRACT_PREVIEW = 300

st.set_page_config(page_title="HCMUT-AILib", page_icon="📚", layout="wide")


@st.cache_resource(show_spinner="Loading embedding model and vector index…")
def get_engine() -> SearchEngine:
    return SearchEngine()


@st.cache_resource
def get_keyword_extractor() -> KeywordExtractor:
    return KeywordExtractor([p["abstract"] for p in ingest.load()])


@st.cache_data
def year_bounds() -> tuple[int, int]:
    years = [int(p["published_date"][:4]) for p in ingest.load()]
    return min(years), max(years)


def render_card(result: SearchResult, key_prefix: str) -> None:
    paper = result.paper
    with st.container(border=True):
        head, score = st.columns([6, 1])
        head.markdown(f"#### {result.rank}. {paper.title}")
        score.metric("Match", f"{result.score:.0%}")

        authors = ", ".join(paper.authors[:6]) + (" et al." if len(paper.authors) > 6 else "")
        badges = " ".join(f":blue-badge[{c}]" if c in CATEGORY_NAMES else f":gray-badge[{c}]"
                          for c in paper.categories)
        st.markdown(f"**{authors}** · {paper.published_date} · arXiv:{paper.id}  \n{badges}")

        keywords = get_keyword_extractor().extract(paper.abstract, k=5)
        if keywords:
            st.caption("Key terms: " + " · ".join(keywords))

        preview = paper.abstract if len(paper.abstract) <= ABSTRACT_PREVIEW \
            else paper.abstract[:ABSTRACT_PREVIEW].rsplit(" ", 1)[0] + " …"
        st.write(preview)
        with st.expander("Full abstract"):
            st.write(paper.abstract)

        links = st.columns(4)
        links[0].link_button("📄 PDF", paper.pdf_url, use_container_width=True)
        links[1].link_button("🔗 arXiv page", paper.abs_url, use_container_width=True)
        if paper.doi:
            links[2].link_button("DOI", f"https://doi.org/{paper.doi}", use_container_width=True)
        if links[3].button("🔍 Find similar", key=f"{key_prefix}-sim-{paper.id}",
                           use_container_width=True):
            st.session_state.similar_to = paper.id
            st.toast("Open the “Similar papers” tab to see the results.")

        with st.expander("Cite this paper"):
            style = st.radio("Format", list(FORMATS), horizontal=True,
                             key=f"{key_prefix}-cite-{paper.id}", label_visibility="collapsed")
            # st.code renders a built-in copy-to-clipboard button.
            st.code(FORMATS[style](paper),
                    language="bibtex" if style == "BibTeX" else None, wrap_lines=True)


def search_tab(engine: SearchEngine, filters: dict) -> None:
    st.markdown("Describe what you are looking for in plain English — the engine matches "
                "**meaning**, not exact words.")
    if "query" not in st.session_state:
        st.session_state.query = ""
    st.text_input("Search query", key="query", label_visibility="collapsed",
                  placeholder="e.g. transfer learning for low-resource machine translation")
    suggestion = st.pills("Try an example", EXAMPLE_QUERIES, key="example")
    query = st.session_state.query.strip() or (suggestion or "")

    if not query:
        st.info("Type a research question above, or pick one of the examples.")
        return

    with st.spinner("Searching…"):
        start = time.perf_counter()
        results = engine.search(query, **filters)
        elapsed = time.perf_counter() - start

    if not results:
        st.warning("No papers match this query with the current filters. "
                   "Try widening the year range or removing category/author filters.")
        return
    st.caption(f"{len(results)} results for “{query}” in {elapsed:.2f} s")
    for result in results:
        render_card(result, "search")


def similar_tab(engine: SearchEngine, top_k: int) -> None:
    paper_id = st.text_input("arXiv id", value=st.session_state.get("similar_to", ""),
                             placeholder="e.g. 2401.01076",
                             help="Click “Find similar” on any search result, or paste an id.")
    if not paper_id:
        st.info("Pick a paper with the “Find similar” button in the Search tab.")
        return
    try:
        source = engine.get(paper_id.strip())
    except KeyError:
        st.error(f"Paper {paper_id} is not in the index.")
        return
    st.markdown(f"Papers most similar to **{source.title}** ({source.id})")
    for result in engine.similar(source.id, top_k):
        render_card(result, "similar")


def about_tab(engine: SearchEngine) -> None:
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

Metadata courtesy of arXiv. Thank you to arXiv for use of its open access interoperability.
HCMUT-AILib is not affiliated with or endorsed by arXiv.
Source code: [github.com/HCMUT-Fus/hcmut-ailib](https://github.com/HCMUT-Fus/hcmut-ailib) (GNU GPLv3).
""")


def main() -> None:
    st.title("📚 HCMUT-AILib")
    st.caption("Semantic search & research assistant for open-access academic papers")

    try:
        engine = get_engine()
    except Exception as exc:  # missing index is the common first-run error
        st.error(f"Could not open the vector index ({exc}). Build it first with "
                 "`python -m src.indexer`.")
        st.stop()

    lo, hi = year_bounds()
    with st.sidebar:
        st.header("Filters")
        top_k = st.slider("Number of results (Top-K)", 1, 20, 10)
        years = st.slider("Publication year", lo, hi, (lo, hi))
        categories = st.multiselect("arXiv categories", list(CATEGORY_NAMES),
                                    format_func=lambda c: f"{c} — {CATEGORY_NAMES[c]}")
        author = st.text_input("Author contains", placeholder="e.g. Nguyen")

    filters = {
        "top_k": top_k,
        "year_range": None if years == (lo, hi) else years,
        "categories": categories or None,
        "author": author.strip() or None,
    }
    search, similar, about = st.tabs(["🔎 Search", "🧭 Similar papers", "ℹ️ About"])
    with search:
        search_tab(engine, filters)
    with similar:
        similar_tab(engine, top_k)
    with about:
        about_tab(engine)


main()
