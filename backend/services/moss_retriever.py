"""Moss — semantic retrieval engine for creators.

This module wraps whatever vector / semantic search backend we use behind
a single ``MossRetriever`` class. In the MVP we ship two backends:

1. **Provider embeddings + in-memory cosine similarity** using
   ``EMBEDDING_PROVIDER`` (OpenAI default, Gemini optional). The class
   embeds every creator once on startup and keeps the matrix in memory —
   perfect for < 10k docs.
2. **TF-IDF fallback** — a pure-Python bag-of-words cosine similarity so
   the demo still works without any external API. Zero dependencies.

Swap this implementation for a real vector DB (Pinecone, Chroma,
Weaviate) without changing any caller — only the class internals need
to change.
"""

from __future__ import annotations

import json
import math
import re
from collections import Counter
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

from models.schemas import Creator, CreatorMetrics, Demographics
from services.embedding_client import (
    active_provider,
    embed_query,
    embed_texts,
)


# ---------------------------------------------------------------------------
# Dataset loading
# ---------------------------------------------------------------------------


def load_creators(path: Path) -> List[Creator]:
    """Load the creators dataset from disk into validated pydantic models."""
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    creators: List[Creator] = []
    for item in raw:
        try:
            metrics = item.get("metrics", {})
            demo = metrics.get("demographics", {}) or {}
            creators.append(
                Creator(
                    username=item["username"],
                    bio=item.get("bio", ""),
                    content_style_tags=item.get("content_style_tags", []),
                    projected_score=float(item.get("projected_score", 60.0)),
                    metrics=CreatorMetrics(
                        follower_count=int(metrics.get("follower_count", 0)),
                        total_gmv_30d=float(metrics.get("total_gmv_30d", 0.0)),
                        avg_views_30d=int(metrics.get("avg_views_30d", 0)),
                        engagement_rate=float(metrics.get("engagement_rate", 0.0)),
                        gpm=float(metrics.get("gpm", 0.0)),
                        demographics=Demographics(
                            major_gender=demo.get("major_gender", "FEMALE"),
                            gender_pct=float(demo.get("gender_pct", 0.0)),
                            age_ranges=demo.get("age_ranges", []),
                        ),
                    ),
                )
            )
        except Exception:
            # skip malformed rows rather than crash the whole index
            continue
    return creators


def _creator_document(c: Creator) -> str:
    """Build the text we feed into the embedding model for each creator.

    We include demographics in the text so queries like "women 25-34"
    retrieve semantically-relevant creators, not just bio matches.
    """
    demo = c.metrics.demographics
    gender_word = "women" if demo.major_gender == "FEMALE" else "men"
    ages = ", ".join(demo.age_ranges) if demo.age_ranges else "all ages"
    tags = ", ".join(c.content_style_tags) or "general"
    return (
        f"{c.bio} "
        f"Niches: {tags}. "
        f"Audience: primarily {gender_word}, ages {ages}."
    )


# ---------------------------------------------------------------------------
# Math helpers
# ---------------------------------------------------------------------------


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    dot = 0.0
    na = 0.0
    nb = 0.0
    for x, y in zip(a, b):
        dot += x * y
        na += x * x
        nb += y * y
    if na == 0 or nb == 0:
        return 0.0
    return dot / (math.sqrt(na) * math.sqrt(nb))


_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]{1,}")


def _tokenize(text: str) -> List[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


# ---------------------------------------------------------------------------
# The retriever
# ---------------------------------------------------------------------------


class MossRetriever:
    """Semantic index over creator documents.

    Call :meth:`build` once at startup, then :meth:`search` as many times
    as you like. Thread-safe for reads.
    """

    def __init__(self) -> None:
        self.creators: List[Creator] = []
        self._docs: List[str] = []

        # Embedding-backend state
        self._embeddings: Optional[List[List[float]]] = None

        # TF-IDF fallback state
        self._vocab: dict[str, int] = {}
        self._idf: List[float] = []
        self._doc_vecs: List[dict[int, float]] = []

        self._backend: str = "tfidf"

    # ------------------------------------------------------------------
    # Build
    # ------------------------------------------------------------------

    def build(self, creators: Iterable[Creator]) -> None:
        self.creators = list(creators)
        self._docs = [_creator_document(c) for c in self.creators]

        embeddings = embed_texts(self._docs)
        if embeddings is not None and len(embeddings) == len(self._docs):
            self._embeddings = embeddings
            self._backend = f"embedding:{active_provider()}"
            return

        # Fallback — always available
        self._build_tfidf()
        self._backend = "tfidf"

    def _build_tfidf(self) -> None:
        tokenised = [_tokenize(d) for d in self._docs]
        df: Counter[str] = Counter()
        for toks in tokenised:
            df.update(set(toks))

        self._vocab = {term: i for i, term in enumerate(sorted(df))}
        n_docs = max(1, len(tokenised))
        self._idf = [0.0] * len(self._vocab)
        for term, idx in self._vocab.items():
            self._idf[idx] = math.log((1 + n_docs) / (1 + df[term])) + 1.0

        self._doc_vecs = []
        for toks in tokenised:
            self._doc_vecs.append(self._vectorize(toks))

    def _vectorize(self, tokens: Sequence[str]) -> dict[int, float]:
        tf = Counter(tokens)
        vec: dict[int, float] = {}
        norm_sq = 0.0
        for term, count in tf.items():
            idx = self._vocab.get(term)
            if idx is None:
                continue
            w = count * self._idf[idx]
            vec[idx] = w
            norm_sq += w * w
        if norm_sq > 0:
            inv = 1.0 / math.sqrt(norm_sq)
            for k in vec:
                vec[k] *= inv
        return vec

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    @property
    def backend(self) -> str:
        """Which scoring backend is currently powering this index."""
        return self._backend

    def search(self, query: str, top_k: int = 50) -> List[Tuple[Creator, float]]:
        """Return ``top_k`` (creator, semantic_score) pairs, sorted by score."""
        if not self.creators:
            return []

        scores: List[Tuple[int, float]]
        if self._backend.startswith("embedding:") and self._embeddings is not None:
            q_vec = embed_query(query)
            if q_vec is None:
                scores = self._tfidf_scores(query)
            else:
                scores = [
                    (i, _cosine(q_vec, self._embeddings[i]))
                    for i in range(len(self.creators))
                ]
        else:
            scores = self._tfidf_scores(query)

        scores.sort(key=lambda t: t[1], reverse=True)
        top = scores[:top_k]
        # clamp scores to [0, 1] for downstream math
        return [(self.creators[i], max(0.0, min(1.0, s))) for i, s in top]

    def _tfidf_scores(self, query: str) -> List[Tuple[int, float]]:
        q_vec = self._vectorize(_tokenize(query))
        out: List[Tuple[int, float]] = []
        for i, dv in enumerate(self._doc_vecs):
            # sparse cosine (vectors are already L2-normalised)
            if len(q_vec) < len(dv):
                s = sum(w * dv.get(k, 0.0) for k, w in q_vec.items())
            else:
                s = sum(w * q_vec.get(k, 0.0) for k, w in dv.items())
            out.append((i, s))
        return out
