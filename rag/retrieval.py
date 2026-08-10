
"""
rag/retrieval.py

Retrieves relevant fitness knowledge from ChromaDB.

The model and ChromaDB client are loaded once when this module is imported.
Retrieved knowledge is capped to prevent unnecessarily large LLM prompts.
"""

from pathlib import Path

import chromadb
from sentence_transformers import SentenceTransformer


ROOT = Path(__file__).resolve().parent.parent
CHROMA_DIR = ROOT / "rag" / "chroma_store"
COLLECTION_NAME = "fitness_knowledge"
EMBED_MODEL_NAME = "all-MiniLM-L6-v2"

# Number of passages to retrieve.
TOP_K = 2

# Maximum amount of retrieved text inserted into the LLM prompt.
MAX_KNOWLEDGE_CHARS = 3000


_model = None
_collection = None


def _load():
    global _model, _collection

    if _model is None:
        print("Loading SentenceTransformer...")
        _model = SentenceTransformer(EMBED_MODEL_NAME)
        print("SentenceTransformer loaded.")

    if _collection is None:
        print("Opening ChromaDB...")
        client = chromadb.PersistentClient(path=str(CHROMA_DIR))
        print("Getting collection...")
        _collection = client.get_collection(COLLECTION_NAME)
        print("Collection ready.")


def retrieve(query, top_k=TOP_K):
    """
    Retrieve relevant fitness knowledge.

    Returns a maximum of MAX_KNOWLEDGE_CHARS characters so that
    RAG does not unnecessarily inflate the LLM prompt.
    """

    if not query or not query.strip():
        return "No relevant knowledge found."

    try:
        _load()
    except Exception as e:
        return f"Knowledge base unavailable ({e})."

    try:
        query_embedding = _model.encode([query]).tolist()

        results = _collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
        )

    except Exception as e:
        return f"Knowledge lookup failed ({e})."

    documents = results.get("documents", [[]])
    passages = documents[0] if documents else []

    if not passages:
        return "No relevant knowledge found."

    # Add passages until the character budget is reached.
    selected = []
    total_chars = 0

    for passage in passages:
        if not passage:
            continue

        remaining = MAX_KNOWLEDGE_CHARS - total_chars

        if remaining <= 0:
            break

        if len(passage) > remaining:
            passage = passage[:remaining]

        selected.append(passage)
        total_chars += len(passage)

    if not selected:
        return "No relevant knowledge found."

    return "\n\n".join(selected)

