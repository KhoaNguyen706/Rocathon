"""Caching layer for embedding and search results.

Goals:
- reduce paid embedding calls (OpenAI / Gemini)
- avoid recomputing parse + retrieve + rerank + insights for repeated queries

Backends:
- sqlite (default, persistent)
- memory (in-process only)
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Optional


def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class CacheStore:
    def __init__(self) -> None:
        self.backend = os.getenv("CACHE_BACKEND", "sqlite").strip().lower()
        self.search_ttl_seconds = int(os.getenv("SEARCH_CACHE_TTL_SECONDS", "1800"))
        self.search_cache_version = os.getenv("SEARCH_CACHE_VERSION", "v4")

        self._memory_embeddings: dict[str, list[float]] = {}
        self._memory_search: dict[str, tuple[float, dict[str, Any]]] = {}
        self._lock = threading.Lock()

        self._sqlite_path = Path(
            os.getenv("CACHE_SQLITE_PATH", Path(__file__).parents[1] / "data" / "cache.db")
        )
        self._conn: Optional[sqlite3.Connection] = None

        if self.backend == "sqlite":
            self._init_sqlite()

    # ------------------------------------------------------------------
    # SQLite init
    # ------------------------------------------------------------------

    def _init_sqlite(self) -> None:
        self._sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self._sqlite_path, check_same_thread=False)
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS embedding_cache (
                cache_key TEXT PRIMARY KEY,
                vector_json TEXT NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS search_cache (
                cache_key TEXT PRIMARY KEY,
                response_json TEXT NOT NULL,
                expires_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            )
            """
        )
        self._conn.commit()

    # ------------------------------------------------------------------
    # Key builders
    # ------------------------------------------------------------------

    def _embedding_key(self, provider: str, model: str, text: str) -> str:
        return f"emb::{provider}::{model}::{_hash_text(text)}"

    def _search_key(self, provider: str, query: str, top_k: int) -> str:
        return (
            f"search::{self.search_cache_version}::{provider}::{top_k}::"
            f"{_hash_text(query.strip().lower())}"
        )

    # ------------------------------------------------------------------
    # Embedding cache API
    # ------------------------------------------------------------------

    def get_embedding(self, provider: str, model: str, text: str) -> Optional[list[float]]:
        key = self._embedding_key(provider, model, text)
        if self.backend == "memory":
            with self._lock:
                return self._memory_embeddings.get(key)

        if self.backend == "sqlite" and self._conn is not None:
            row = self._conn.execute(
                "SELECT vector_json FROM embedding_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row:
                return None
            return list(json.loads(row[0]))
        return None

    def set_embedding(self, provider: str, model: str, text: str, vector: list[float]) -> None:
        key = self._embedding_key(provider, model, text)
        now = int(time.time())
        if self.backend == "memory":
            with self._lock:
                self._memory_embeddings[key] = vector
            return

        if self.backend == "sqlite" and self._conn is not None:
            self._conn.execute(
                """
                INSERT INTO embedding_cache(cache_key, vector_json, updated_at)
                VALUES(?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    vector_json = excluded.vector_json,
                    updated_at = excluded.updated_at
                """,
                (key, json.dumps(vector), now),
            )
            self._conn.commit()

    # ------------------------------------------------------------------
    # Search cache API
    # ------------------------------------------------------------------

    def get_search(self, provider: str, query: str, top_k: int) -> Optional[dict[str, Any]]:
        key = self._search_key(provider, query, top_k)
        now = int(time.time())
        if self.backend == "memory":
            with self._lock:
                item = self._memory_search.get(key)
                if not item:
                    return None
                expires_at, payload = item
                if expires_at < now:
                    self._memory_search.pop(key, None)
                    return None
                return payload

        if self.backend == "sqlite" and self._conn is not None:
            row = self._conn.execute(
                "SELECT response_json, expires_at FROM search_cache WHERE cache_key = ?",
                (key,),
            ).fetchone()
            if not row:
                return None
            response_json, expires_at = row
            if int(expires_at) < now:
                self._conn.execute("DELETE FROM search_cache WHERE cache_key = ?", (key,))
                self._conn.commit()
                return None
            return dict(json.loads(response_json))
        return None

    def set_search(self, provider: str, query: str, top_k: int, payload: dict[str, Any]) -> None:
        key = self._search_key(provider, query, top_k)
        now = int(time.time())
        expires_at = now + self.search_ttl_seconds
        if self.backend == "memory":
            with self._lock:
                self._memory_search[key] = (expires_at, payload)
            return

        if self.backend == "sqlite" and self._conn is not None:
            self._conn.execute(
                """
                INSERT INTO search_cache(cache_key, response_json, expires_at, updated_at)
                VALUES(?, ?, ?, ?)
                ON CONFLICT(cache_key) DO UPDATE SET
                    response_json = excluded.response_json,
                    expires_at = excluded.expires_at,
                    updated_at = excluded.updated_at
                """,
                (key, json.dumps(payload), expires_at, now),
            )
            self._conn.commit()


_CACHE: Optional[CacheStore] = None


def get_cache_store() -> CacheStore:
    global _CACHE
    if _CACHE is None:
        _CACHE = CacheStore()
    return _CACHE
