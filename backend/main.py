"""FastAPI entrypoint — AI Creator Discovery Copilot.

Boots a ``MossRetriever`` with the bundled creators dataset on startup so
the first request is fast. The frontend talks to a single ``/search``
endpoint; see ``routers/search.py``.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.search import router as search_router
from services.cache_store import get_cache_store
from services.creator_store import load_creators_from_store
from services.embedding_client import active_provider
from services.gemini_client import is_enabled as gemini_enabled
from services.moss_retriever import MossRetriever


log = logging.getLogger("copilot")
logging.basicConfig(level=logging.INFO)


DATA_PATH = Path(os.getenv("CREATORS_PATH", Path(__file__).parent / "data" / "creators.json"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    retriever = MossRetriever()
    cache = get_cache_store()
    try:
        creators = load_creators_from_store(DATA_PATH)
        retriever.build(creators)
        log.info("Moss index ready (backend=%s)", retriever.backend)
    except FileNotFoundError:
        log.warning("Creators dataset not found at %s — serving empty index.", DATA_PATH)
    app.state.retriever = retriever
    app.state.cache = cache
    yield


app = FastAPI(
    title="AI Creator Discovery Copilot",
    description="Natural-language creator search powered by Gemini + Moss.",
    version="0.1.0",
    lifespan=lifespan,
)


# Allow the Next.js dev server (and docker-compose network) to call us.
_origins = [o.strip() for o in os.getenv("CORS_ORIGINS", "*").split(",") if o.strip()]
_allow_credentials = _origins != ["*"]  # credentials + wildcard is rejected by browsers

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=_allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health() -> dict:
    retriever: MossRetriever | None = getattr(app.state, "retriever", None)
    cache = getattr(app.state, "cache", None)
    return {
        "status": "ok",
        "gemini_enabled": gemini_enabled(),
        "embedding_provider": active_provider(),
        "cache_backend": cache.backend if cache else None,
        "retriever_backend": retriever.backend if retriever else None,
        "creators_indexed": len(retriever.creators) if retriever else 0,
    }


app.include_router(search_router)
