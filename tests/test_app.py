"""Headless UI tests for the Streamlit dashboard (streamlit.testing.AppTest)."""

from pathlib import Path

import pytest

from src import indexer

APP = str(Path(__file__).resolve().parent.parent / "src" / "app.py")

pytestmark = pytest.mark.skipif(not (indexer.INDEX_DIR / "chroma.sqlite3").exists(),
                                reason="vector index not built; run `python -m src.indexer`")


@pytest.fixture
def app():
    from streamlit.testing.v1 import AppTest
    at = AppTest.from_file(APP, default_timeout=120)
    at.run()
    assert not at.exception
    return at


def card_titles(at):
    return [m.value for m in at.markdown if m.value.startswith("#### ")]


def test_initial_page_prompts_for_query(app):
    assert app.title[0].value.endswith("HCMUT-AILib")
    assert any("Type a research question" in i.value for i in app.info)
    assert card_titles(app) == []


def test_search_renders_top_k_cards(app):
    app.sidebar.slider[0].set_value(5)
    app.text_input(key="query").input("detecting misinformation on social media").run()
    assert not app.exception
    titles = card_titles(app)
    assert len(titles) == 5
    assert titles[0].startswith("#### 1. ")


def test_find_similar_fills_similar_tab(app):
    app.sidebar.slider[0].set_value(3)
    app.text_input(key="query").input("graph neural networks").run()
    find_similar = next(b for b in app.button if b.label.endswith("Find similar"))
    find_similar.click().run()
    assert not app.exception
    assert any(m.value.startswith("Papers most similar to") for m in app.markdown)
    assert len(card_titles(app)) == 6  # 3 search results + 3 similar papers


def test_filters_without_matches_show_warning(app):
    app.sidebar.text_input[0].input("zzzz-no-such-author").run()
    app.text_input(key="query").input("graph neural networks").run()
    assert card_titles(app) == []
    assert any("No papers match" in w.value for w in app.warning)
