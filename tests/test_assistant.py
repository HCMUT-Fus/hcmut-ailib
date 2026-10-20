"""Research-assistant helpers: citations, keywords and the BM25 baseline."""

from src.citations import initials, split_name, to_apa, to_bibtex, to_ieee
from src.keywords import KeywordExtractor
from src.lexical_baseline import BM25
from src.search_engine import Paper


def make_paper(authors, doi=None):
    return Paper(id="2401.01234", title="Dense Retrieval & Libraries", abstract="...",
                 authors=authors, doi=doi, categories=["cs.IR"], primary_category="cs.IR",
                 published_date="2024-01-02", pdf_url="https://arxiv.org/pdf/2401.01234v1")


def test_name_helpers():
    assert split_name("Nguyen Van An") == ("An", ["Nguyen", "Van"])
    assert split_name("Plato") == ("Plato", [])
    assert initials(["Jean-Pierre", "K."]) == "J.-P. K."


def test_bibtex():
    bib = to_bibtex(make_paper(["Ada Lovelace", "Alan Turing"]))
    assert bib.startswith("@misc{lovelace2024dense,")
    assert "author = {Ada Lovelace and Alan Turing}" in bib
    assert r"title = {{Dense Retrieval \& Libraries}}" in bib
    assert "doi = {10.48550/arXiv.2401.01234}" in bib
    assert bib.endswith("}")


def test_apa():
    assert to_apa(make_paper(["Ada Lovelace", "Alan Mathison Turing"], doi="10.1/x")) == (
        "Lovelace, A., & Turing, A. M. (2024). Dense Retrieval & Libraries "
        "(arXiv:2401.01234). arXiv. https://doi.org/10.1/x")
    many = to_apa(make_paper([f"Given Family{i}" for i in range(25)]))
    assert ", . . . Family24, G." in many and "Family19" not in many


def test_ieee():
    assert to_ieee(make_paper(["Ada Lovelace"])).startswith('A. Lovelace, "Dense')
    assert to_ieee(make_paper(["Ada Lovelace", "Alan Turing"])).startswith(
        "A. Lovelace and A. Turing,")
    assert to_ieee(make_paper(["A B", "C D", "E F"])).startswith("A. B, C. D, and E. F,")
    assert to_ieee(make_paper([f"X Y{i}" for i in range(7)])).startswith("X. Y0 et al.,")


def test_keywords_prefer_distinctive_phrases():
    text = "graph neural networks predict traffic flow in cities"
    corpus = ["deep learning for images", "deep learning for text",
              "graph neural networks for molecules", "graph neural networks for traffic",
              "forecasting traffic flow with sensors", text]  # as in the app, text is in the corpus
    extractor = KeywordExtractor(corpus)
    keywords = extractor.extract(text, k=3)
    assert "traffic flow" in keywords
    # "predict traffic" occurs in no other document, so it is not treated as a phrase.
    assert "predict traffic" not in keywords
    assert all(k not in {"for", "in"} for k in keywords)


def test_bm25_matches_terms():
    papers = [{"id": "1", "title": "Graph neural networks", "abstract": "message passing"},
              {"id": "2", "title": "Machine translation", "abstract": "low resource languages"},
              {"id": "3", "title": "Translation memory", "abstract": "industry tools"}]
    bm25 = BM25(papers)
    assert bm25.search("low resource translation")[0] == "2"
    assert bm25.search("quantum chemistry") == []
