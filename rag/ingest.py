"""
rag/ingest.py

Run this ONCE (and again whenever your documents change).
It reads every .txt file in the knowledge folder, splits each into small
passages, turns each passage into an embedding, and stores them in ChromaDB.

Usage:
    python -m rag.ingest
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

# --- paths and settings ---
ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "rag" / "knowledge"      # put your .txt files here
CHROMA_DIR = ROOT / "rag" / "chroma_store"       # ChromaDB saves here
COLLECTION_NAME = "fitness_knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# How big each passage is, in characters, and how much neighbouring
# passages overlap (overlap keeps sentences from being cut awkwardly).
CHUNK_SIZE = 500
CHUNK_OVERLAP = 100


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    """
    Splits a long string into overlapping chunks of roughly chunk_size
    characters. Overlap means the end of one chunk repeats at the start
    of the next, so ideas that span a boundary aren't lost.
    """
    text = text.strip()
    if not text:
        return []

    chunks = []
    start = 0
    while start < len(text):
        end = start + chunk_size
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap   # step forward, leaving an overlap
    return chunks


def load_documents():
    """
    Reads every .txt file in the knowledge folder.
    Returns a list of (source_filename, text) pairs.
    """
    if not KNOWLEDGE_DIR.exists():
        KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created empty knowledge folder at: {KNOWLEDGE_DIR}")
        print("Put your .txt documents there, then run this again.")
        return []

    docs = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.txt")):
        text = path.read_text(encoding="utf-8", errors="ignore")
        if text.strip():
            docs.append((path.name, text))
    return docs


def ingest():
    docs = load_documents()
    if not docs:
        print("No documents found. Nothing to ingest.")
        return

    # Load the embedding model (downloads once, then cached locally).
    print(f"Loading embedding model: {EMBED_MODEL_NAME} ...")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    # Open (or create) the persistent ChromaDB store.
    client = chromadb.PersistentClient(path=str(CHROMA_DIR))

    # Start fresh each ingest so re-running doesn't create duplicates.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    # Build every chunk from every document.
    all_chunks = []
    all_ids = []
    all_metadatas = []

    for source_name, text in docs:
        chunks = chunk_text(text)
        for i, chunk in enumerate(chunks):
            all_chunks.append(chunk)
            all_ids.append(f"{source_name}::chunk_{i}")
            all_metadatas.append({"source": source_name})

    if not all_chunks:
        print("Documents were found but produced no chunks (empty files?).")
        return

    print(f"Embedding {len(all_chunks)} chunks from {len(docs)} document(s)...")
    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metadatas,
    )

    print(f"Done. Stored {len(all_chunks)} chunks in ChromaDB at {CHROMA_DIR}")


if __name__ == "__main__":
    ingest()
