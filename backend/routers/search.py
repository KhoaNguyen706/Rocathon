"""POST /search — the single entrypoint used by the frontend."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request

from models.schemas import SearchRequest, SearchResponse
from services.orchestrator import run_search


router = APIRouter()


@router.post("/search", response_model=SearchResponse)
def search(payload: SearchRequest, request: Request) -> SearchResponse:
    retriever = request.app.state.retriever
    if retriever is None or not retriever.creators:
        raise HTTPException(status_code=503, detail="Retriever not ready.")
    try:
        return run_search(retriever, payload.query, top_k=payload.top_k)
    except Exception as exc:  # keep the API robust for a hackathon demo
        raise HTTPException(status_code=500, detail=str(exc)) from exc
