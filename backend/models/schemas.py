"""Pydantic schemas for the AI Creator Discovery Copilot API.

These models describe the shape of the request/response payloads, the
structured query produced by the parse agent, and the ranked creator
records returned to the frontend.
"""

from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Parsed query (output of the Gemini parse agent)
# ---------------------------------------------------------------------------


class ParsedQuery(BaseModel):
    """Structured representation of a natural language campaign brief."""

    category: Optional[str] = Field(
        default=None, description="Product category, e.g. 'smart home', 'beauty'."
    )
    audience_age: List[str] = Field(
        default_factory=list,
        description="Target audience age ranges, e.g. ['18-24','25-34'].",
    )
    gender: Optional[Literal["MALE", "FEMALE", "ANY"]] = Field(
        default="ANY", description="Preferred audience gender."
    )
    tone: Optional[str] = Field(
        default=None, description="Campaign tone, e.g. 'authentic, energetic'."
    )
    niche: List[str] = Field(
        default_factory=list,
        description="Creator niches that fit the brief (content tags).",
    )
    keywords: List[str] = Field(
        default_factory=list,
        description="Free-form keywords extracted from the brief for semantic search.",
    )


# ---------------------------------------------------------------------------
# Creator models
# ---------------------------------------------------------------------------


class Demographics(BaseModel):
    major_gender: Literal["MALE", "FEMALE"]
    gender_pct: float = 0.0
    age_ranges: List[str] = Field(default_factory=list)


class CreatorMetrics(BaseModel):
    follower_count: int = 0
    total_gmv_30d: float = 0.0
    avg_views_30d: int = 0
    engagement_rate: float = 0.0
    gpm: float = 0.0
    demographics: Demographics


class Creator(BaseModel):
    username: str
    bio: str = ""
    content_style_tags: List[str] = Field(default_factory=list)
    projected_score: float = 60.0  # raw RoC projected score (60–100)
    metrics: CreatorMetrics


class CreatorScores(BaseModel):
    semantic_score: float
    projected_score: float  # normalized 0–1
    demographic_bonus: float
    final_score: float


class RankedCreator(Creator):
    scores: CreatorScores


# ---------------------------------------------------------------------------
# API payloads
# ---------------------------------------------------------------------------


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=3, description="Natural language campaign brief.")
    top_k: int = Field(default=10, ge=1, le=50)


class SearchResponse(BaseModel):
    parsed_query: ParsedQuery
    results: List[RankedCreator]
    insights: str
