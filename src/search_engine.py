"""Semantic and Hybrid search over the ChromaDB index.

Dense retrieval: query is embedded with all-MiniLM-L6-v2 and ChromaDB's HNSW index
returns approximate nearest neighbours by cosine distance.
Scores are reported as ``(1 + cosine_similarity) / 2`` so they lie in [0, 1].

Hybrid retrieval: combines Dense Vector search and Sparse BM25 lexical search
using Reciprocal Rank Fusion (RRF) for enhanced precision on domain terms.

Scalable Author Filtering: uses an in-memory Inverted Index with Vietnamese
diacritic normalization (strip_accents) to eliminate full-collection scans.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from src import indexer
from src.text_utils import strip_accents


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
    def from_chroma(cls, paper_id: str, document: str, metadata: dict) -> Paper:
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


class AuthorIndex:
    """In-memory inverted index for diacritic-insensitive author matching."""

    def __init__(self, papers_metadata: list[tuple[str, str]]):
        # List of (paper_id, authors_string)
        self._token_to_ids: dict[str, set[str]] = defaultdict(set)
        self._id_to_norm_authors: dict[str, str] = {}
        for paper_id, authors_str in papers_metadata:
            norm = strip_accents(authors_str)
            self._id_to_norm_authors[paper_id] = norm
            for token in norm.replace(";", " ").replace(",", " ").split():
                if len(token) > 1:
                    self._token_to_ids[token].add(paper_id)

    def match(self, query: str) -> set[str]:
        """Find paper IDs whose authors match the query tokens (accent-insensitive)."""
        clean = strip_accents(query)
        tokens = [t for t in clean.replace(";", " ").replace(",", " ").split() if len(t) > 1]
        if not tokens:
            return set()
        matched: set[str] | None = None
        for t in tokens:
            ids_for_token = set()
            for indexed_token, ids in self._token_to_ids.items():
                if t in indexed_token:
                    ids_for_token.update(ids)
            if matched is None:
                matched = ids_for_token
            else:
                matched &= ids_for_token
        if not matched:
            return set()
        clean = clean.strip()
        return {pid for pid in matched if clean in self._id_to_norm_authors[pid]}


class SearchEngine:
    def __init__(self, index_dir: Path = indexer.INDEX_DIR, model=None):
        self.model = model or indexer.load_model()
        self.collection = indexer.open_client(index_dir).get_collection(
            indexer.COLLECTION, embedding_function=None)
        self._author_index: AuthorIndex | None = None
        self._bm25 = None
        self._cross_encoder = None

    def __len__(self) -> int:
        return self.collection.count()

    @property
    def author_index(self) -> AuthorIndex:
        if self._author_index is None:
            # Load metadata for author indexing
            data = self.collection.get(include=["metadatas"])
            pairs = [(pid, meta["authors"]) for pid, meta in zip(data["ids"], data["metadatas"])]
            self._author_index = AuthorIndex(pairs)
        return self._author_index

    @property
    def bm25(self):
        if self._bm25 is None:
            from src.lexical_baseline import BM25
            data = self.collection.get(include=["documents", "metadatas"])
            papers = [{
                "id": pid,
                "title": meta["title"],
                "abstract": doc,
            } for pid, doc, meta in zip(data["ids"], data["documents"], data["metadatas"])]
            self._bm25 = BM25(papers, title_weight=2)
        return self._bm25

    def embed(self, text: str) -> list[float]:
        return self.model.encode(text, normalize_embeddings=True).tolist()

    def search(self, query: str, top_k: int = 10,
               year_range: tuple[int, int] | None = None,
               categories: list[str] | None = None,
               author: str | None = None,
               rerank: bool = False) -> list[SearchResult]:
        """Return up to ``top_k`` papers ranked by semantic similarity to ``query``."""
        query = (query or "").strip()
        author = (author or "").strip() or None
        if not query or top_k < 1:
            return []
        fetch_k = max(top_k * 2, 15) if rerank else top_k
        results = self._query(self.embed(query), fetch_k, build_where(year_range, categories), author)
        if rerank and results:
            return self.rerank(query, results, top_k=top_k)
        return results

    def hybrid_search(self, query: str, top_k: int = 10,
                      year_range: tuple[int, int] | None = None,
                      categories: list[str] | None = None,
                      author: str | None = None,
                      rrf_k: int = 60,
                      weight_dense: float = 1.0,
                      weight_lexical: float = 0.5,
                      rerank: bool = False) -> list[SearchResult]:
        """Search combining dense semantic retrieval and BM25 using Reciprocal Rank Fusion."""
        query = (query or "").strip()
        if not query or top_k < 1:
            return []

        # Retrieve top candidates from dense search
        candidate_k = max(top_k * 3, 30)
        dense_results = self.search(query, top_k=candidate_k,
                                    year_range=year_range, categories=categories, author=author,
                                    rerank=False)

        # Retrieve candidate IDs from BM25
        bm25_ids = self.bm25.search(query, top_k=candidate_k)

        # Pre-filter BM25 candidates by author if needed
        author_clean = strip_accents(author) if author else None
        if author_clean:
            matched_author_ids = self.author_index.match(author_clean)
            bm25_ids = [pid for pid in bm25_ids if pid in matched_author_ids]

        # Collect all papers and assign ranks
        dense_ranks = {r.paper.id: r.rank for r in dense_results}
        papers_dict = {r.paper.id: r.paper for r in dense_results}

        # Batch-fetch metadata/documents for any BM25 candidates not in dense results
        missing_ids = [pid for pid in bm25_ids if pid not in papers_dict]
        if missing_ids:
            batch_found = self.collection.get(ids=missing_ids, include=["documents", "metadatas"])
            for pid, doc, meta in zip(batch_found["ids"], batch_found["documents"], batch_found["metadatas"]):
                try:
                    papers_dict[pid] = Paper.from_chroma(pid, doc, meta)
                except Exception:
                    continue

        bm25_ranks = {}
        for rank, pid in enumerate(bm25_ids, 1):
            paper = papers_dict.get(pid)
            if paper is None:
                continue
            if year_range and not (year_range[0] <= paper.year <= year_range[1]):
                continue
            if categories and not any(c in paper.categories for c in categories):
                continue
            bm25_ranks[pid] = rank

        all_ids = set(dense_ranks) | set(bm25_ranks)
        if not all_ids:
            return []

        # Compute RRF score
        rrf_scores: dict[str, float] = {}
        for pid in all_ids:
            score = 0.0
            if pid in dense_ranks:
                score += weight_dense / (rrf_k + dense_ranks[pid])
            if pid in bm25_ranks:
                score += weight_lexical / (rrf_k + bm25_ranks[pid])
            rrf_scores[pid] = score

        # Max theoretical RRF score for rank 1 in both
        max_possible = (weight_dense / (rrf_k + 1)) + (weight_lexical / (rrf_k + 1))
        ranked_ids = sorted(all_ids, key=lambda pid: rrf_scores[pid], reverse=True)

        if rerank:
            candidate_pool = ranked_ids[:max(top_k * 2, 15)]
            rrf_candidates = [
                SearchResult(papers_dict[pid], min(1.0, max(0.0, rrf_scores[pid] / max_possible)), i + 1)
                for i, pid in enumerate(candidate_pool)
            ]
            return self.rerank(query, rrf_candidates, top_k=top_k)

        results = []
        for rank, pid in enumerate(ranked_ids[:top_k], 1):
            normalized_score = min(1.0, max(0.0, rrf_scores[pid] / max_possible))
            results.append(SearchResult(papers_dict[pid], normalized_score, rank))
        return results

    def rerank(self, query: str, candidates: list[SearchResult], top_k: int = 10) -> list[SearchResult]:
        """Re-rank candidate SearchResults using a Cross-Encoder model.

        Cross-encoders evaluate query-document pairs jointly with full cross-attention,
        providing superior semantic precision over dual-encoder cosine similarity.
        """
        if not candidates or top_k < 1:
            return []
        if getattr(self, "_cross_encoder", None) is None:
            from sentence_transformers import CrossEncoder
            self._cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-2-v2")

        pairs = [(query, f"{c.paper.title}. {c.paper.abstract}") for c in candidates]
        scores = self._cross_encoder.predict(pairs)

        def sigmoid(x: float) -> float:
            return float(1.0 / (1.0 + np.exp(-x)))

        ranked = sorted(zip(scores, candidates), key=lambda x: float(x[0]), reverse=True)[:top_k]
        return [
            SearchResult(
                paper=cand.paper,
                score=sigmoid(float(s)),
                rank=i + 1
            )
            for i, (s, cand) in enumerate(ranked)
        ]

    def similar(self, paper_id: str, top_k: int = 5) -> list[SearchResult]:
        """Papers closest to an indexed paper, excluding the paper itself."""
        found = self.collection.get(ids=[paper_id], include=["embeddings"])
        if not found["ids"]:
            raise KeyError(paper_id)
        if top_k < 1:
            return []
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

        # Scalable Author Filtering using Inverted Index:
        # Instead of scanning the whole collection (n_results=total), match candidate IDs first.
        if author:
            matched_ids = self.author_index.match(author)
            if not matched_ids:
                return []

            # If matched candidate set is small (common for specific author queries),
            # compute cosine similarity directly via dot product on pre-fetched embeddings.
            if len(matched_ids) <= 200:
                candidates = self.collection.get(
                    ids=list(matched_ids), where=where,
                    include=["documents", "metadatas", "embeddings"])
                if not candidates["ids"]:
                    return []
                cand_embeddings = np.array(candidates["embeddings"], dtype=np.float32)
                q_emb = np.array(embedding, dtype=np.float32)
                # Both are normalized, so dot product = cosine similarity
                sims = np.dot(cand_embeddings, q_emb)
                ranked_indices = np.argsort(-sims)[:top_k]
                results = []
                for rank, idx in enumerate(ranked_indices, 1):
                    pid = candidates["ids"][idx]
                    doc = candidates["documents"][idx]
                    meta = candidates["metadatas"][idx]
                    score = min(1.0, max(0.0, float((1.0 + sims[idx]) / 2.0)))
                    paper = Paper.from_chroma(pid, doc, meta)
                    results.append(SearchResult(paper, score, rank))
                return results

        n_results = min(top_k * 5 if author else top_k, total)
        try:
            response = self.collection.query(
                query_embeddings=[embedding], n_results=n_results, where=where,
                include=["documents", "metadatas", "distances"])
        except ValueError:
            return []

        results = []
        for paper_id, document, metadata, distance in zip(
                response["ids"][0], response["documents"][0],
                response["metadatas"][0], response["distances"][0]):
            if author:
                norm_author_input = strip_accents(author)
                norm_meta_authors = strip_accents(metadata["authors"])
                if norm_author_input not in norm_meta_authors:
                    continue
            paper = Paper.from_chroma(paper_id, document, metadata)
            results.append(SearchResult(paper, normalize_score(distance), len(results) + 1))
            if len(results) == top_k:
                break
        return results
