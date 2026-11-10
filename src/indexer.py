"""Embed the arXiv sample with all-MiniLM-L6-v2 and store it in ChromaDB.

Each paper is embedded from ``"<title>. <abstract>"`` into a 384-dimensional,
L2-normalized vector and written to a persistent ChromaDB collection that uses
cosine distance. Run with ``python -m src.indexer``.

Supports decoupling Neural Embedding and Vector Indexing via precomputed .npz cache.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

import numpy as np

from src import ingest

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data" / "processed" / "vector_index"
COLLECTION = "arxiv_papers"
MODEL_NAME = "MongoDB/mdbr-leaf-ir"
BATCH_SIZE = 128


def document_text(paper: dict) -> str:
    return f"{paper['title']}. {paper['abstract']}"


def category_key(category: str) -> str:
    """Metadata key flagging membership in a category, e.g. 'cat:cs.CL'."""
    return f"cat:{category}"


def to_metadata(paper: dict) -> dict:
    """Flatten a record into ChromaDB metadata (scalar values only)."""
    metadata = {
        "id": paper["id"],
        "title": paper["title"],
        "authors": "; ".join(paper["authors"]),
        "doi": paper["doi"] or "",
        "categories": " ".join(paper["categories"]),
        "primary_category": paper["primary_category"],
        "published_date": paper["published_date"],
        "year": int(paper["published_date"][:4]),
        "pdf_url": paper["pdf_url"],
    }
    metadata.update({category_key(c): True for c in paper["categories"]})
    return metadata


def load_model(name: str = MODEL_NAME, dim: int = 384):
    """Load embedding model, supporting 384D extraction for models like mdbr-leaf-ir."""
    from sentence_transformers import SentenceTransformer
    try:
        from sentence_transformers.sentence_transformer.modules import Normalize
    except ImportError:
        from sentence_transformers.models import Normalize

    model = SentenceTransformer(name, device="cpu")
    if "mdbr-leaf-ir" in name and dim == 384 and len(model) >= 3:
        model = SentenceTransformer(modules=[model[0], model[1], Normalize()])
    model.max_seq_length = 256
    return model


def open_client(index_dir: Path = INDEX_DIR):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(index_dir), settings=Settings(anonymized_telemetry=False))


def get_embeddings_cache_path(data_path: Path, model_name: str = MODEL_NAME) -> Path:
    suffix = "_leaf384" if "mdbr-leaf-ir" in model_name else ""
    stem = data_path.stem.replace("sample", "embeddings") + suffix
    return data_path.parent / f"{stem}.npz"


def get_or_compute_embeddings(papers: list[dict], cache_path: Path | None = None,
                              model=None, force_recompute: bool = False,
                              batch_size: int = BATCH_SIZE) -> np.ndarray:
    """Load precomputed embeddings from .npz cache, or compute and save them."""
    if cache_path and cache_path.exists() and not force_recompute:
        data = np.load(cache_path, allow_pickle=False)
        cached_ids = data["ids"].tolist()
        paper_ids = [p["id"] for p in papers]
        if cached_ids == paper_ids:
            return data["embeddings"]
        print(f"Cache {cache_path} ID mismatch ({len(cached_ids)} vs {len(papers)}), recomputing...")

    model = model or load_model()
    embeddings = model.encode([document_text(p) for p in papers], batch_size=batch_size,
                              normalize_embeddings=True, show_progress_bar=True)
    if cache_path:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(cache_path, ids=np.array([p["id"] for p in papers]), embeddings=embeddings)
        print(f"Saved {len(embeddings)} precomputed embeddings to {cache_path}")
    return embeddings


def build_index(papers: list[dict], index_dir: Path = INDEX_DIR, model=None,
                cache_path: Path | None = None, force_recompute: bool = False,
                batch_size: int = BATCH_SIZE):
    """(Re)build the collection from scratch and return it."""
    client = open_client(index_dir)
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    collection = client.create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"}, embedding_function=None)

    embeddings = get_or_compute_embeddings(
        papers, cache_path=cache_path, model=model, force_recompute=force_recompute,
        batch_size=batch_size)

    # ChromaDB caps the number of records per add() call.
    step = 500
    for i in range(0, len(papers), step):
        chunk = papers[i:i + step]
        chunk_embeddings = embeddings[i:i + step]
        collection.add(
            ids=[p["id"] for p in chunk],
            embeddings=chunk_embeddings.tolist() if hasattr(chunk_embeddings, "tolist") else chunk_embeddings,
            documents=[p["abstract"] for p in chunk],
            metadatas=[to_metadata(p) for p in chunk],
        )
    return collection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=ingest.OUTPUT_PATH)
    parser.add_argument("--index-dir", type=Path, default=INDEX_DIR)
    parser.add_argument("--cache", type=Path, default=None)
    parser.add_argument("--model", type=str, default=MODEL_NAME, help="Embedding model name or HF ID")
    parser.add_argument("--dim", type=int, default=384, help="Embedding dimension (default: 384)")
    parser.add_argument("--recompute", action="store_true", help="Force recomputing embeddings")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()

    papers = ingest.load(args.data)
    cache_path = args.cache or get_embeddings_cache_path(args.data, model_name=args.model)
    model = load_model(args.model, dim=args.dim)
    start = time.perf_counter()
    collection = build_index(papers, args.index_dir, model=model, cache_path=cache_path,
                             force_recompute=args.recompute, batch_size=args.batch_size)
    print(f"Indexed {collection.count()} papers into {args.index_dir} "
          f"in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
