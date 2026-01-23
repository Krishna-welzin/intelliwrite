import os
from typing import Optional

from agno.vectordb.qdrant import Qdrant
from agno.knowledge.embedder.google import GeminiEmbedder
from aeo_blog_engine.config.settings import Config


class _InMemoryKnowledge:
    """Very small in-memory fallback to keep the pipeline running without Qdrant."""

    def __init__(self):
        docs = []
        kb_path = os.path.join(os.path.dirname(__file__), "docs")
        for root, _, files in os.walk(kb_path):
            for file_name in files:
                if file_name.endswith((".md", ".txt")):
                    file_path = os.path.join(root, file_name)
                    with open(file_path, "r", encoding="utf-8") as handle:
                        docs.append(handle.read())
        self._documents = docs

    def exists(self):
        return True

    def search(self, query: str, limit: int = 3, **_):
        # The pipeline expects objects with `.content`; emulate that interface
        class _Doc:
            def __init__(self, text: str):
                self.content = text

        return [_Doc(text) for text in self._documents[:limit]]


_cached_vector_db: Optional[object] = None


def _use_in_memory_fallback(reason: str):
    print(f"[fallback] Falling back to in-memory knowledge base ({reason})")
    return _InMemoryKnowledge()


def get_knowledge_base():
    """
    Initializes and returns the vector DB instance.
    Falls back to an in-memory KB when Qdrant cannot be reached.
    """
    global _cached_vector_db
    if _cached_vector_db:
        return _cached_vector_db

    if not Config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY must be configured")

    if Config.QDRANT_URL == ":memory:":
        _cached_vector_db = _use_in_memory_fallback("QDRANT_URL=:memory:")
        return _cached_vector_db

    try:
        _cached_vector_db = Qdrant(
            collection=Config.COLLECTION_NAME,
            url=Config.QDRANT_URL,
            api_key=Config.QDRANT_API_KEY,
            embedder=GeminiEmbedder(api_key=Config.GEMINI_API_KEY),
        )
        # Monkey-patch _build_search_results to tolerate payloads that use
        # 'brand' or 'file_name' instead of 'name'. Some collections were
        # indexed without a 'name' field; the agno client expects 'name'.
        try:
            orig_build = getattr(_cached_vector_db, "_build_search_results", None)
            if orig_build:
                def _patched_build_search_results(results, query):
                    # Normalize payloads so the agno client can find expected keys
                    for r in results:
                        try:
                            payload = getattr(r, 'payload', None) or (r.get('payload') if isinstance(r, dict) else None)
                            if payload is None:
                                continue

                            # Ensure a 'name' is present (some ingests use 'brand' or 'file_name')
                            if 'name' not in payload:
                                payload['name'] = payload.get('brand') or payload.get('file_name') or 'unknown'

                            # Ensure a 'meta_data' dict exists; populate with sensible fallbacks
                            if 'meta_data' not in payload or not isinstance(payload.get('meta_data'), dict):
                                payload['meta_data'] = {
                                    'name': payload.get('name'),
                                    'brand': payload.get('brand'),
                                    'file_name': payload.get('file_name'),
                                    'source': payload.get('source'),
                                    'industry': payload.get('industry')
                                }
                        except Exception:
                            # Don't let payload normalization break the search
                            continue
                    return orig_build(results, query)

                # Bind the patched function to the instance
                setattr(_cached_vector_db, "_build_search_results", _patched_build_search_results)
        except Exception:
            # If monkey-patching fails, continue and rely on fallback behavior
            pass
        # Trigger a lightweight call to surface connection issues early
        if hasattr(_cached_vector_db, "client"):
            _cached_vector_db.client.get_collections()
        return _cached_vector_db
    except Exception as exc:
        _cached_vector_db = _use_in_memory_fallback(str(exc))
        return _cached_vector_db
