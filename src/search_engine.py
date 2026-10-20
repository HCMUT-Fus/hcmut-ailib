"""Semantic search over the ChromaDB index.

A query is embedded with the same model used at indexing time, and ChromaDB's
HNSW index returns the approximate nearest neighbours by cosine distance.
Scores are reported as ``(1 + cosine_similarity) / 2`` so they lie in [0, 1].
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src import indexer


@dataclass(frozen=True)
class Paper:
    id: str
    title: str
    abstract: str
    authors: list[str]
    doi: str | None
    categories: list[str]
    primary_category: str
    published_date: str
    pdf_url: str

    @property
    def year(self) -> int:
        return int(self.published_date[:4])

    @property
    def abs_url(self) -> str:
        return f"https://arxiv.org/abs/{self.id}"

    @classmethod
    def from_chroma(cls, paper_id: str, document: str, metadata: dict) -> "Paper":
        return cls(
            id=paper_id,
            title=metadata["title"],
            abstract=document,
            authors=metadata["authors"].split("; ") if metadata["authors"] else [],
            doi=metadata["doi"] or None,
            categories=metadata["categories"].split(),
            primary_category=metadata["primary_category"],
            published_date=metadata["published_date"],
            pdf_url=metadata["pdf_url"],
        )


@dataclass(frozen=True)
class SearchResult:
    paper: Paper
    score: float  # normalized relevance in [0, 1]
    rank: int


def normalize_score(cosine_distance: float) -> float:
    """Map a cosine distance in [0, 2] to a relevance score in [0, 1]."""
    similarity = 1.0 - cosine_distance
    return min(1.0, max(0.0, (1.0 + similarity) / 2.0))


def build_where(year_range: tuple[int, int] | None = None,
                categories: list[str] | None = None) -> dict | None:
    """Translate UI filters into a ChromaDB ``where`` clause.

    Several categories are OR-ed: a paper matches if it is listed in any of them.
    """
    clauses = []
    if year_range:
        clauses += [{"year": {"$gte": int(year_range[0])}}, {"year": {"$lte": int(year_range[1])}}]
    if categories:
        options = [{indexer.category_key(c): True} for c in categories]
        clauses.append(options[0] if len(options) == 1 else {"$or": options})
    if not clauses:
        return None
    return clauses[0] if len(clauses) == 1 else {"$and": clauses}


class SearchEngine:
    def __init__(self, index_dir: Path = indexer.INDEX_DIR, model=None):
        self.model = model or indexer.load_model()
        self.collection = indexer.open_client(index_dir).get_collection(
            indexer.COLLECTION, embedding_function=None)

    def __len__(self) -> int:
        return self.collection.count()

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def search(self, query: str, top_k: int = 10,
               year_range: tuple[int, int] | None = None,
               categories: list[str] | None = None,
               author: str | None = None) -> list[SearchResult]:
        """Return up to ``top_k`` papers ranked by semantic similarity to ``query``."""
        query = (query or "").strip()
        if not query or top_k < 1:
            return []
        return self._query(self.embed(query), top_k, build_where(year_range, categories), author)

    def similar(self, paper_id: str, top_k: int = 5) -> list[SearchResult]:
        """Papers closest to an indexed paper, excluding the paper itself."""
        found = self.collection.get(ids=[paper_id], include=["embeddings"])
        if not found["ids"]:
            raise KeyError(paper_id)
        results = self._query(list(found["embeddings"][0]), top_k + 1, None, None)
        others = [r for r in results if r.paper.id != paper_id][:top_k]
        return [SearchResult(r.paper, r.score, i) for i, r in enumerate(others, 1)]

    def get(self, paper_id: str) -> Paper:
        found = self.collection.get(ids=[paper_id], include=["documents", "metadatas"])
        if not found["ids"]:
            raise KeyError(paper_id)
        return Paper.from_chroma(paper_id, found["documents"][0], found["metadatas"][0])

    def _query(self, embedding, top_k, where, author) -> list[SearchResult]:
        total = len(self)
        if total == 0:
            return []
        # Author names are not indexable as a Chroma filter, so match them
        # after retrieval over the whole (small) collection.
        n_results = total if author else min(top_k, total)
        try:
            response = self.collection.query(
                query_embeddings=[embedding], n_results=n_results, where=where,
                include=["documents", "metadatas", "distances"])
        except ValueError:
            # Raised by some Chroma versions when the filter matches nothing.
            return []
        results = []
        for paper_id, document, metadata, distance in zip(
                response["ids"][0], response["documents"][0],
                response["metadatas"][0], response["distances"][0]):
            if author and author.strip().lower() not in metadata["authors"].lower():
                continue
            paper = Paper.from_chroma(paper_id, document, metadata)
            results.append(SearchResult(paper, normalize_score(distance), len(results) + 1))
            if len(results) == top_k:
                break
        return results
