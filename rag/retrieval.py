"""
rag/retrieval.py

Provides retrieve(query): given the user's message, finds the most
relevant passages from the fitness knowledge base and returns them as text.

This is called on EVERY turn (Pattern 1), so the model always has trusted
knowledge in front of it before it answers.

The model and ChromaDB client are loaded ONCE when this module is imported,
not on every call, so retrieval stays fast.
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer

ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / "rag" / "chroma_store"
COLLECTION_NAME = "fitness_knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# How many passages to return each turn.
TOP_K = 3

# --- load once at import time ---
_model = None
_collection = None


def _load():
    """Lazily load the model and collection the first time we need them."""
    global _model, _collection
    if _model is None:
        _model = SentenceTransformer(EMBED_MODEL_NAME)
    if _collection is None:
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        _collection = client.get_collection(COLLECTION_NAME)


def retrieve(query, top_k=TOP_K):
    """
    Returns the most relevant knowledge passages for `query`, joined into
    one string. Returns a safe message if the knowledge base is empty or
    unavailable (so the caller never crashes).
    """
    if not query or not query.strip():
        return "No relevant knowledge found."

    try:
        _load()
    except Exception as e:
        # e.g. the collection doesn't exist yet (ingest not run).
        return f"Knowledge base unavailable ({e})."

    try:
        query_embedding = _model.encode([query]).tolist()
        results = _collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )
    except Exception as e:
        return f"Knowledge lookup failed ({e})."

    # results["documents"] is a list-of-lists (one list per query).
    documents = results.get("documents", [[]])
    passages = documents[0] if documents else []

    if not passages:
        return "No relevant knowledge found."

    # Join the passages into one readable block.
    return "\n\n".join(passages)
