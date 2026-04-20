"""Pipeline orchestration (light LangChain usage).

The search endpoint is a short, linear DAG:

    parse_brief  →  moss.search  →  rerank  →  insights

We express it using LangChain's ``RunnableLambda`` / ``RunnablePassthrough``
primitives so additional steps (tool calls, retries, tracing) can be added
later without rewriting the pipeline. If LangChain isn't installed we fall
back to plain function composition — behaviour is identical.
"""

from __future__ import annotations

from typing import Any, Dict

from models.schemas import (
    ParsedQuery,
    RankedCreator,
    SearchResponse,
)
from services.cache_store import get_cache_store
from services.embedding_client import active_provider
from services.insights import generate_insights
from services.moss_retriever import MossRetriever
from services.parse_brief import parse_brief
from services.reranker import rerank

try:
    from langchain_core.runnables import RunnableLambda, RunnablePassthrough  # type: ignore
    _LANGCHAIN_AVAILABLE = True
except Exception:  # pragma: no cover - optional import
    _LANGCHAIN_AVAILABLE = False


CANDIDATE_POOL = 50


def _build_chain(retriever: MossRetriever, top_k: int):
    """Compose the pipeline into a single callable.

    Input : ``{"query": str}``
    Output: :class:`SearchResponse`
    """

    def step_parse(inputs: Dict[str, Any]) -> Dict[str, Any]:
        parsed = parse_brief(inputs["query"])
        return {**inputs, "parsed": parsed}

    def step_retrieve(inputs: Dict[str, Any]) -> Dict[str, Any]:
        parsed: ParsedQuery = inputs["parsed"]
        # Enrich the raw query with keywords/niche from the parsed brief,
        # giving the retriever more signal to work with.
        enriched = " ".join(
            [
                inputs["query"],
                parsed.category or "",
                " ".join(parsed.niche),
                " ".join(parsed.keywords),
                parsed.tone or "",
            ]
        ).strip()
        candidates = retriever.search(enriched, top_k=CANDIDATE_POOL)
        return {**inputs, "candidates": candidates}

    def step_rerank(inputs: Dict[str, Any]) -> Dict[str, Any]:
        ranked = rerank(inputs["candidates"], inputs["parsed"], top_k=top_k)
        return {**inputs, "ranked": ranked}

    def step_insights(inputs: Dict[str, Any]) -> SearchResponse:
        ranked: list[RankedCreator] = inputs["ranked"]
        parsed: ParsedQuery = inputs["parsed"]
        summary = generate_insights(parsed, ranked)
        return SearchResponse(parsed_query=parsed, results=ranked, insights=summary)

    if _LANGCHAIN_AVAILABLE:
        return (
            RunnablePassthrough()
            | RunnableLambda(step_parse)
            | RunnableLambda(step_retrieve)
            | RunnableLambda(step_rerank)
            | RunnableLambda(step_insights)
        )

    def _plain(inputs: Dict[str, Any]) -> SearchResponse:
        return step_insights(step_rerank(step_retrieve(step_parse(inputs))))

    return _plain


def run_search(
    retriever: MossRetriever, query: str, top_k: int = 10
) -> SearchResponse:
    cache = get_cache_store()
    provider = active_provider()
    cached = cache.get_search(provider=provider, query=query, top_k=top_k)
    if cached is not None:
        return SearchResponse(**cached)

    chain = _build_chain(retriever, top_k=top_k)
    payload = {"query": query}
    if _LANGCHAIN_AVAILABLE:
        response: SearchResponse = chain.invoke(payload)  # type: ignore[assignment]
    else:
        response = chain(payload)  # type: ignore[misc]

    cache.set_search(
        provider=provider,
        query=query,
        top_k=top_k,
        payload=response.model_dump(),
    )
    return response
