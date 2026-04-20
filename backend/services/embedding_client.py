"""Configurable embedding provider for Moss retrieval.

Supported providers:
- openai (default)
- gemini

If the selected provider is unavailable or API calls fail, callers receive
``None`` and can gracefully fall back to TF-IDF.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

from services.cache_store import get_cache_store
from services.gemini_client import embed_query as gemini_embed_query
from services.gemini_client import embed_text as gemini_embed_text

try:
    from openai import OpenAI  # type: ignore
except Exception:  # pragma: no cover - optional import
    OpenAI = None  # type: ignore


EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai").strip().lower()
OPENAI_EMBED_MODEL = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")


@lru_cache(maxsize=1)
def _openai_client() -> Optional[OpenAI]:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key or OpenAI is None:
        return None
    return OpenAI(api_key=api_key)


def embed_text(text: str) -> Optional[list[float]]:
    """Embed a document string using the configured provider."""
    provider = EMBEDDING_PROVIDER
    if provider == "gemini":
        cache = get_cache_store()
        cached = cache.get_embedding("gemini", "gemini-embed", text)
        if cached is not None:
            return cached
        vec = gemini_embed_text(text)
        if vec is not None:
            cache.set_embedding("gemini", "gemini-embed", text, vec)
        return vec
    if provider == "openai":
        cache = get_cache_store()
        cached = cache.get_embedding("openai", OPENAI_EMBED_MODEL, text)
        if cached is not None:
            return cached
        client = _openai_client()
        if client is None:
            return None
        try:
            result = client.embeddings.create(model=OPENAI_EMBED_MODEL, input=text)
            vector = list(result.data[0].embedding)
            cache.set_embedding("openai", OPENAI_EMBED_MODEL, text, vector)
            return vector
        except Exception:
            return None
    return None


def embed_query(text: str) -> Optional[list[float]]:
    """Embed a query string using the configured provider."""
    # OpenAI uses the same endpoint for docs and queries.
    return embed_text(text)


def embed_texts(texts: list[str], batch_size: int = 100) -> Optional[list[list[float]]]:
    """Batch-embed many documents at once.

    Returns a list of vectors in the same order as ``texts``. Uses the
    persistent cache so repeated startups are effectively free. Returns
    ``None`` only if the underlying provider is unavailable for an
    un-cached document (caller should fall back to TF-IDF).
    """
    if not texts:
        return []

    provider = EMBEDDING_PROVIDER
    cache = get_cache_store()

    if provider == "gemini":
        # Gemini SDK has no efficient batch endpoint here — call one-by-one.
        out: list[list[float]] = []
        for text in texts:
            cached = cache.get_embedding("gemini", "gemini-embed", text)
            if cached is not None:
                out.append(cached)
                continue
            vec = gemini_embed_text(text)
            if vec is None:
                return None
            cache.set_embedding("gemini", "gemini-embed", text, vec)
            out.append(vec)
        return out

    if provider == "openai":
        results: list[Optional[list[float]]] = [None] * len(texts)
        pending_idx: list[int] = []
        pending_text: list[str] = []
        for i, text in enumerate(texts):
            cached = cache.get_embedding("openai", OPENAI_EMBED_MODEL, text)
            if cached is not None:
                results[i] = cached
            else:
                pending_idx.append(i)
                pending_text.append(text)

        if pending_text:
            client = _openai_client()
            if client is None:
                return None
            for start in range(0, len(pending_text), batch_size):
                chunk_texts = pending_text[start : start + batch_size]
                chunk_idx = pending_idx[start : start + batch_size]
                try:
                    resp = client.embeddings.create(
                        model=OPENAI_EMBED_MODEL, input=chunk_texts
                    )
                except Exception:
                    return None
                for item, global_i, original in zip(resp.data, chunk_idx, chunk_texts):
                    vec = list(item.embedding)
                    cache.set_embedding("openai", OPENAI_EMBED_MODEL, original, vec)
                    results[global_i] = vec

        if any(r is None for r in results):
            return None
        return results  # type: ignore[return-value]

    return None


def active_provider() -> str:
    """Return the selected embedding provider."""
    return EMBEDDING_PROVIDER
