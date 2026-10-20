"""Ingestion tests: Atom parsing (offline) and integrity of the committed dataset."""

import re
from collections import Counter
from datetime import date

import pytest

from src import ingest

FEED = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:arxiv="http://arxiv.org/schemas/atom">
  <entry>
    <id>http://arxiv.org/abs/2401.01234v2</id>
    <published>2024-01-02T18:59:59Z</published>
    <title>Dense Retrieval
      for  Libraries</title>
    <summary>  We study
      semantic search.  </summary>
    <author><name>Nguyễn Văn An</name></author>
    <author><name>José  Müller-Lüdenscheidt</name></author>
    <arxiv:doi>10.1000/xyz123</arxiv:doi>
    <link href="http://arxiv.org/abs/2401.01234v2" rel="alternate" type="text/html"/>
    <link title="pdf" href="http://arxiv.org/pdf/2401.01234v2" rel="related" type="application/pdf"/>
    <arxiv:primary_category term="cs.IR"/>
    <category term="cs.IR"/>
    <category term="cs.CL"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/math/0601001v1</id>
    <published>2006-01-01T00:00:00Z</published>
    <title>Old-style identifier</title>
    <summary>No DOI and no pdf link.</summary>
    <author><name>A. Author</name></author>
    <category term="math.CO"/>
  </entry>
</feed>"""


def test_parse_feed_normalizes_fields():
    first, second = ingest.parse_feed(FEED)
    assert first == {
        "id": "2401.01234",
        "title": "Dense Retrieval for Libraries",
        "abstract": "We study semantic search.",
        "authors": ["Nguyễn Văn An", "José Müller-Lüdenscheidt"],
        "doi": "10.1000/xyz123",
        "categories": ["cs.IR", "cs.CL"],
        "primary_category": "cs.IR",
        "published_date": "2024-01-02",
        "pdf_url": "https://arxiv.org/pdf/2401.01234v2",
    }
    assert second["id"] == "math/0601001"
    assert second["doi"] is None
    assert second["primary_category"] == "math.CO"
    assert second["pdf_url"] == "https://arxiv.org/pdf/math/0601001"


def test_build_query_restricts_category_and_year():
    assert ingest.build_query("cs.CL", 2023) == \
        "cat:cs.CL AND submittedDate:[202301010000 TO 202312312359]"


def test_collect_skips_duplicates_and_respects_cell_size(monkeypatch):
    page = ingest.parse_feed(FEED)[:1]
    pages = iter([page, page + [dict(page[0], id="2401.99999")]])
    monkeypatch.setattr(ingest, "fetch_page", lambda *args: next(pages))
    records = ingest.collect(categories=("cs.IR",), years=(2024,), per_cell=2)
    assert [r["id"] for r in records] == ["2401.01234", "2401.99999"]


# --- dataset integrity -------------------------------------------------------

@pytest.fixture(scope="module")
def papers():
    if not ingest.OUTPUT_PATH.exists() or ingest.OUTPUT_PATH.stat().st_size == 0:
        pytest.skip("dataset not built; run `python -m src.ingest`")
    return ingest.load()


def test_dataset_has_1000_unique_records(papers):
    assert len(papers) == 1000
    assert len({p["id"] for p in papers}) == 1000


def test_dataset_schema(papers):
    for p in papers:
        assert set(p) == set(ingest.FIELDS)
        assert p["title"] and p["abstract"] and p["authors"]
        assert all(isinstance(a, str) and a for a in p["authors"])
        assert p["doi"] is None or (isinstance(p["doi"], str) and p["doi"].startswith("10."))
        assert p["categories"]
        assert re.fullmatch(r"\d{4}\.\d{4,5}", p["id"]), p["id"]
        assert p["pdf_url"].startswith("https://arxiv.org/pdf/")
        date.fromisoformat(p["published_date"])
        assert p["title"] == ingest.clean_text(p["title"])
        assert p["abstract"] == ingest.clean_text(p["abstract"])


def test_dataset_is_stratified(papers):
    years = Counter(int(p["published_date"][:4]) for p in papers)
    assert years == {y: 200 for y in ingest.YEARS}
    for category in ingest.CATEGORIES:
        assert sum(category in p["categories"] for p in papers) >= 250
