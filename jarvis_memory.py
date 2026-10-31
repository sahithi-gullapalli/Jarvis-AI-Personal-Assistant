"""Local semantic memory using Sentence Transformers + Chroma.

Memory is optional and stored locally in ./data/jarvis_chroma by default.
Do not save passwords, API keys, authentication tokens, or other secrets here.
"""
from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

DB_PATH = os.getenv("JARVIS_CHROMA_PATH", str(Path(__file__).parent / "data" / "jarvis_chroma"))
_COLLECTION = "jarvis_notes"

def _collection():
    import chromadb
    from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
    embedder = SentenceTransformerEmbeddingFunction(
        model_name=os.getenv("JARVIS_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
    )
    client = chromadb.PersistentClient(path=DB_PATH)
    return client.get_or_create_collection(
        name=_COLLECTION,
        embedding_function=embedder,
        metadata={"hnsw:space": "cosine"},
    )

def remember_exchange(query: str, answer: str) -> None:
    """Store a short conversation exchange locally. Fail softly if memory is unavailable."""
    try:
        text = f"User: {query.strip()}\nJarvis: {answer.strip()}"
        if not query.strip() or not answer.strip():
            return
        import uuid
        _collection().upsert(
            ids=[uuid.uuid4().hex],
            documents=[text],
            metadatas=[{"kind": "conversation"}],
        )
    except Exception as exc:
        print(f"[Jarvis memory unavailable: {exc}]")

def add_note(note: str) -> bool:
    if not note or not note.strip():
        return False
    try:
        import uuid
        _collection().upsert(
            ids=[uuid.uuid4().hex],
            documents=[note.strip()],
            metadatas=[{"kind": "note"}],
        )
        return True
    except Exception as exc:
        print(f"[Jarvis memory unavailable: {exc}]")
        return False

def retrieve_context(query: str, n_results: int = 3) -> str:
    if not query or not query.strip():
        return ""
    try:
        result = _collection().query(query_texts=[query], n_results=max(1, min(n_results, 5)))
        docs = result.get("documents") or []
        if not docs or not docs[0]:
            return ""
        return "\n---\n".join(docs[0])
    except Exception as exc:
        print(f"[Jarvis memory unavailable: {exc}]")
        return ""

def clear_memory() -> bool:
    """Delete stored semantic memory from this collection."""
    try:
        import chromadb
        client = chromadb.PersistentClient(path=DB_PATH)
        try:
            client.delete_collection(_COLLECTION)
        except Exception:
            pass
        return True
    except Exception as exc:
        print(f"[Jarvis memory unavailable: {exc}]")
        return False
