"""Thin wrapper around the Google Gemini API.

We centralise model configuration here so the rest of the codebase can
import a single, memoised client. If ``GEMINI_API_KEY`` is missing the
wrapper returns ``None`` for the model and every caller falls back to a
deterministic heuristic. That keeps the app fully runnable in demo mode
without any paid credentials.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Optional

try:
    import google.generativeai as genai  # type: ignore
except Exception:  # pragma: no cover - optional import
    genai = None  # type: ignore


GEMINI_CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-1.5-flash")
GEMINI_EMBED_MODEL = os.getenv("GEMINI_EMBED_MODEL", "text-embedding-004")


@lru_cache(maxsize=1)
def _configure() -> bool:
    """Configure the SDK once per process. Returns True on success."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or genai is None:
        return False
    genai.configure(api_key=api_key)
    return True


def get_chat_model():
    """Return a configured Gemini generative model, or ``None`` if unavailable."""
    if not _configure():
        return None
    return genai.GenerativeModel(GEMINI_CHAT_MODEL)


def embed_text(text: str) -> Optional[list[float]]:
    """Embed a single string. Returns ``None`` when the SDK is not configured."""
    if not _configure():
        return None
    try:
        result = genai.embed_content(
            model=GEMINI_EMBED_MODEL,
            content=text,
            task_type="RETRIEVAL_DOCUMENT",
        )
        return list(result["embedding"])
    except Exception:
        return None


def embed_query(text: str) -> Optional[list[float]]:
    """Embed a query string (uses the RETRIEVAL_QUERY task type)."""
    if not _configure():
        return None
    try:
        result = genai.embed_content(
            model=GEMINI_EMBED_MODEL,
            content=text,
            task_type="RETRIEVAL_QUERY",
        )
        return list(result["embedding"])
    except Exception:
        return None


def is_enabled() -> bool:
    """Public helper: is the real Gemini API wired up?"""
    return _configure()
