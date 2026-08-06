"""
rag/ingest.py

Reads every .txt file in ALL category subfolders under rag/ (e.g.
rag/nutrition/, rag/strength_training/, ...), skips block-page junk,
chunks the text, embeds it, and stores it in ChromaDB.

Run from the project root:
    python -m rag.ingest
"""

import re
from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
RAG_DIR = ROOT / "rag"                         # scans ALL subfolders under here
CHROMA_DIR = ROOT / "rag" / "chroma_store"
COLLECTION_NAME = "fitness_knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

CHUNK_SIZE = 500
CHUNK_OVERLAP = 100
MIN_DOC_LENGTH = 200

# Folders to NOT treat as knowledge (the vector store itself, etc.)
SKIP_DIRS = {"chroma_store"}

# If any of these appear, the file is a bot-block / CAPTCHA page.
BLOCK_MARKERS = (
    "checking your browser",
    "recaptcha",
    "enable javascript",
    "are you a robot",
    "access denied",
)


def clean_document(text):
    """Drop obvious menu/ad junk lines and collapse blank lines."""
    kept = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        low = line.lower()
        if low in ("advertisement", "login", "search", "menu", "home",
                   "privacy", "terms"):
            continue
        if len(line.split()) < 4 and len(line) < 40 and not line.endswith(
            (".", "!", "?", ":")
        ):
            continue
        kept.append(line)
    cleaned = "\n".join(kept)
    return re.sub(r"\n{3,}", "\n\n", cleaned).strip()


def chunk_text(text, chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP):
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        chunk = text[start:start + chunk_size].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap
    return chunks


def load_documents():
    """Reads every .txt under rag/ (recursively), skipping junk + store dir."""
    docs = []
    for path in sorted(RAG_DIR.rglob("*.txt")):
        # skip anything inside chroma_store etc.
        if any(part in SKIP_DIRS for part in path.parts):
            continue

        text = path.read_text(encoding="utf-8", errors="ignore")
        if not text.strip():
            continue

        low = text.lower()
        if any(marker in low for marker in BLOCK_MARKERS):
            print(f"  SKIP {path.name}: block/CAPTCHA page.")
            continue

        cleaned = clean_document(text)
        if len(cleaned) < MIN_DOC_LENGTH:
            print(f"  SKIP {path.name}: too short after cleaning "
                  f"({len(cleaned)} chars).")
            continue

        # use category/filename as the source label
        source = f"{path.parent.name}/{path.name}"
        docs.append((source, cleaned))

    return docs


def ingest():
    docs = load_documents()
    if not docs:
        print("No usable documents found under rag/.")
        return

    # Per-category summary so you can confirm every category was picked up.
    from collections import Counter
    cat_counts = Counter(source.split("/")[0] for source, _ in docs)
    print("Documents found per category:")
    for cat, n in sorted(cat_counts.items()):
        print(f"  {cat}: {n} file(s)")
    print(f"Total: {len(docs)} document(s)\n")

    print(f"Loading embedding model: {EMBED_MODEL_NAME} ...")
    model = SentenceTransformer(EMBED_MODEL_NAME)

    client = chromadb.PersistentClient(path=str(CHROMA_DIR))
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.create_collection(COLLECTION_NAME)

    all_chunks, all_ids, all_metas = [], [], []
    for source, text in docs:
        for i, chunk in enumerate(chunk_text(text)):
            all_chunks.append(chunk)
            all_ids.append(f"{source}::chunk_{i}")
            all_metas.append({"source": source})

    if not all_chunks:
        print("Documents found but no chunks produced.")
        return

    print(f"Embedding {len(all_chunks)} chunks from {len(docs)} document(s)...")
    embeddings = model.encode(all_chunks, show_progress_bar=True).tolist()

    collection.add(
        ids=all_ids,
        documents=all_chunks,
        embeddings=embeddings,
        metadatas=all_metas,
    )
    print(f"Done. Stored {len(all_chunks)} chunks in ChromaDB at {CHROMA_DIR}")


if __name__ == "__main__":
    ingest()