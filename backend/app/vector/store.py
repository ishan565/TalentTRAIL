"""ChromaDB-backed vector store for semantic retrieval.

Wraps a persistent Chroma collection. Used to embed resume sections, skills,
projects, and job descriptions so the matching layer can do hybrid retrieval
(keyword + semantic). Falls back gracefully if Chroma is unavailable so the API
never hard-fails in a minimal environment.

Chunking strategy:
* Resume is split into logical sections (summary, skills, each project, each
  experience entry) rather than fixed-size windows — sections are already
  semantically coherent, which improves retrieval precision.
* Job descriptions are embedded whole (they are short) plus their skills list.
"""
from __future__ import annotations

from typing import Optional

from app.core.config import settings
from app.core.llm import get_embeddings
from app.core.logging import get_logger

logger = get_logger(__name__)


class VectorStore:
    def __init__(self) -> None:
        self._client = None
        self._embeddings = get_embeddings()

    def _collection(self, name: str):
        try:
            import chromadb

            if self._client is None:
                self._client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIR)
            return self._client.get_or_create_collection(name)
        except Exception as exc:  # pragma: no cover - optional dependency path
            logger.warning("vector.unavailable", error=str(exc))
            return None

    def upsert(self, collection: str, ids: list[str], documents: list[str], metadatas: list[dict]):
        col = self._collection(collection)
        if col is None:
            return
        vectors = self._embeddings.embed_documents(documents)
        col.upsert(ids=ids, documents=documents, embeddings=vectors, metadatas=metadatas)
        logger.info("vector.upsert", collection=collection, count=len(ids))

    def query(self, collection: str, text: str, n_results: int = 10) -> list[dict]:
        col = self._collection(collection)
        if col is None:
            return []
        vec = self._embeddings.embed_query(text)
        res = col.query(query_embeddings=[vec], n_results=n_results)
        out: list[dict] = []
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        for i, _id in enumerate(ids):
            out.append(
                {
                    "id": _id,
                    "document": docs[i] if i < len(docs) else None,
                    "metadata": metas[i] if i < len(metas) else {},
                    "distance": dists[i] if i < len(dists) else None,
                }
            )
        return out


_store: Optional[VectorStore] = None


def get_vector_store() -> VectorStore:
    global _store
    if _store is None:
        _store = VectorStore()
    return _store


def chunk_resume(parsed: dict) -> list[tuple[str, str, dict]]:
    """Return (id, text, metadata) chunks for a parsed resume."""
    chunks: list[tuple[str, str, dict]] = []
    if parsed.get("summary"):
        chunks.append(("summary", parsed["summary"], {"section": "summary"}))
    if parsed.get("skills"):
        chunks.append(("skills", ", ".join(map(str, parsed["skills"])), {"section": "skills"}))
    for i, proj in enumerate(parsed.get("projects") or []):
        text = f"{proj.get('name','')}: {proj.get('description','')} {' '.join(proj.get('tech_stack') or [])}"
        chunks.append((f"project-{i}", text, {"section": "project"}))
    for i, exp in enumerate(parsed.get("experience") or []):
        chunks.append((f"experience-{i}", str(exp), {"section": "experience"}))
    return chunks
