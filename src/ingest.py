"""Fetch open metadata for 1,000 arXiv papers and save it as normalized JSON.

The sample is stratified so that every (category, year) cell contributes the
same number of papers: 4 categories x 5 years x 50 papers = 1,000 records.
Requests are spaced at least 3 seconds apart, as required by the arXiv API
Terms of Use. Run with ``python -m src.ingest``.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

API_URL = "https://export.arxiv.org/api/query"
CATEGORIES = ("cs.AI", "cs.LG", "cs.CL", "cs.IR")
YEARS = (2021, 2022, 2023, 2024, 2025)
PER_CELL = 50
PAGE_SIZE = 100
REQUEST_INTERVAL_S = 3.0
OUTPUT_PATH = Path(__file__).resolve().parent.parent / "data" / "raw" / "arxiv_sample_1000.json"
USER_AGENT = "hcmut-ailib/1.0 (CO2001 student project; https://github.com/HCMUT-Fus/hcmut-ailib)"

NS = {
    "atom": "http://www.w3.org/2005/Atom",
    "arxiv": "http://arxiv.org/schemas/atom",
}
FIELDS = ("id", "title", "abstract", "authors", "doi", "categories",
          "primary_category", "published_date", "pdf_url")

_last_request = 0.0


def clean_text(text: str | None) -> str:
    """Collapse all whitespace (arXiv wraps titles/abstracts with newlines)."""
    return re.sub(r"\s+", " ", text or "").strip()


def parse_arxiv_id(entry_id: str) -> str:
    """'http://arxiv.org/abs/2401.01234v2' -> '2401.01234' (also old-style ids)."""
    raw = entry_id.split("/abs/", 1)[-1]
    return re.sub(r"v\d+$", "", raw)


def parse_entry(entry: ET.Element) -> dict:
    """Convert one Atom <entry> into a normalized record."""
    paper_id = parse_arxiv_id(entry.findtext("atom:id", "", NS))
    pdf_url = next(
        (link.get("href") for link in entry.findall("atom:link", NS)
         if link.get("title") == "pdf"),
        f"https://arxiv.org/pdf/{paper_id}",
    )
    primary = entry.find("arxiv:primary_category", NS)
    categories = [c.get("term") for c in entry.findall("atom:category", NS) if c.get("term")]
    doi = clean_text(entry.findtext("arxiv:doi", None, NS)) or None
    return {
        "id": paper_id,
        "title": clean_text(entry.findtext("atom:title", "", NS)),
        "abstract": clean_text(entry.findtext("atom:summary", "", NS)),
        "authors": [clean_text(a.findtext("atom:name", "", NS))
                    for a in entry.findall("atom:author", NS)],
        "doi": doi,
        "categories": categories,
        "primary_category": primary.get("term") if primary is not None else categories[0],
        # <published> is ISO 8601 (2024-01-02T18:59:59Z); keep the date part.
        "published_date": entry.findtext("atom:published", "", NS)[:10],
        "pdf_url": pdf_url.replace("http://", "https://", 1),
    }


def parse_feed(xml_text: str) -> list[dict]:
    root = ET.fromstring(xml_text)
    return [parse_entry(e) for e in root.findall("atom:entry", NS)]


def build_query(category: str, year: int) -> str:
    return f"cat:{category} AND submittedDate:[{year}01010000 TO {year}12312359]"


def fetch_page(search_query: str, start: int, max_results: int, retries: int = 3) -> list[dict]:
    """Fetch one result page, honouring the 3 s rate limit and retrying with backoff."""
    global _last_request
    params = urllib.parse.urlencode({
        "search_query": search_query,
        "start": start,
        "max_results": max_results,
        "sortBy": "submittedDate",
        "sortOrder": "ascending",
    })
    request = urllib.request.Request(f"{API_URL}?{params}", headers={"User-Agent": USER_AGENT})
    for attempt in range(retries):
        wait = REQUEST_INTERVAL_S - (time.monotonic() - _last_request)
        if wait > 0:
            time.sleep(wait)
        _last_request = time.monotonic()
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                entries = parse_feed(response.read().decode("utf-8"))
            # The API occasionally returns an empty page under load; retry it.
            if entries or attempt == retries - 1:
                return entries
        except OSError as exc:
            if attempt == retries - 1:
                raise
            print(f"  request failed ({exc}); retrying")
        time.sleep(REQUEST_INTERVAL_S * 2 ** (attempt + 1))
    return []


def is_valid(record: dict) -> bool:
    return bool(record["id"] and record["title"] and record["abstract"] and record["authors"])


def collect(categories=CATEGORIES, years=YEARS, per_cell=PER_CELL) -> list[dict]:
    """Collect ``per_cell`` unique papers for every (category, year) pair.

    Papers are cross-listed, so a paper already taken by an earlier cell is
    skipped and the next page is requested until the cell is full.
    """
    seen: set[str] = set()
    records: list[dict] = []
    for category in categories:
        for year in years:
            query = build_query(category, year)
            taken, start = 0, 0
            while taken < per_cell:
                page = fetch_page(query, start, PAGE_SIZE)
                if not page:
                    raise RuntimeError(f"arXiv returned no more results for {query!r}")
                start += len(page)
                for record in page:
                    if record["id"] in seen or not is_valid(record):
                        continue
                    seen.add(record["id"])
                    records.append(record)
                    taken += 1
                    if taken == per_cell:
                        break
            print(f"{category} {year}: {taken} papers")
    return records


def save(records: list[dict], path: Path = OUTPUT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(records, ensure_ascii=False, indent=1), encoding="utf-8")


def load(path: Path = OUTPUT_PATH) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--per-cell", type=int, default=PER_CELL,
                        help="papers per (category, year) pair (default: %(default)s)")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    args = parser.parse_args()
    records = collect(per_cell=args.per_cell)
    save(records, args.output)
    print(f"Saved {len(records)} records to {args.output}")


if __name__ == "__main__":
    main()
