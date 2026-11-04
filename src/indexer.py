"""Embed the arXiv sample with all-MiniLM-L6-v2 and store it in ChromaDB.

Each paper is embedded from ``"<title>. <abstract>"`` into a 384-dimensional,
L2-normalized vector and written to a persistent ChromaDB collection that uses
cosine distance. Run with ``python -m src.indexer``.
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from src import ingest

ROOT = Path(__file__).resolve().parent.parent
INDEX_DIR = ROOT / "data" / "processed" / "vector_index"
COLLECTION = "arxiv_papers"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
BATCH_SIZE = 64


def document_text(paper: dict) -> str:
    return f"{paper['title']}. {paper['abstract']}"


def category_key(category: str) -> str:
    """Metadata key flagging membership in a category, e.g. 'cat:cs.CL'."""
    return f"cat:{category}"


def to_metadata(paper: dict) -> dict:
    """Flatten a record into ChromaDB metadata (scalar values only)."""
    metadata = {
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


def load_model(name: str = MODEL_NAME):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(name, device="cpu")


def open_client(index_dir: Path = INDEX_DIR):
    import chromadb
    from chromadb.config import Settings
    return chromadb.PersistentClient(path=str(index_dir), settings=Settings(anonymized_telemetry=False))


def build_index(papers: list[dict], index_dir: Path = INDEX_DIR, model=None,
                batch_size: int = BATCH_SIZE):
    """(Re)build the collection from scratch and return it."""
    model = model or load_model()
    client = open_client(index_dir)
    if COLLECTION in [c.name for c in client.list_collections()]:
        client.delete_collection(COLLECTION)
    collection = client.create_collection(
        COLLECTION, metadata={"hnsw:space": "cosine"}, embedding_function=None)
    embeddings = model.encode([document_text(p) for p in papers], batch_size=batch_size,
                              normalize_embeddings=True, show_progress_bar=True)
    # ChromaDB caps the number of records per add() call.
    step = 500
    for i in range(0, len(papers), step):
        chunk = papers[i:i + step]
        collection.add(
            ids=[p["id"] for p in chunk],
            embeddings=embeddings[i:i + step].tolist(),
            documents=[p["abstract"] for p in chunk],
            metadatas=[to_metadata(p) for p in chunk],
        )
    return collection


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data", type=Path, default=ingest.OUTPUT_PATH)
    parser.add_argument("--index-dir", type=Path, default=INDEX_DIR)
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE)
    args = parser.parse_args()
    papers = ingest.load(args.data)
    start = time.perf_counter()
    collection = build_index(papers, args.index_dir, batch_size=args.batch_size)
    print(f"Indexed {collection.count()} papers into {args.index_dir} "
          f"in {time.perf_counter() - start:.1f} s")


if __name__ == "__main__":
    main()
