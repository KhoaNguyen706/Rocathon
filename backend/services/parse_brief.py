"""Agent #1 — parse a natural-language brief into structured fields using Gemini.

If Gemini is not configured, we fall back to a lightweight heuristic
parser so the pipeline keeps working end-to-end for demos.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict

from models.schemas import ParsedQuery
from services.gemini_client import get_chat_model


PARSE_SYSTEM_PROMPT = """You are a marketing analyst. Extract structured fields
from a brand's creator-campaign brief.

Return ONLY a JSON object with this exact shape (no prose, no markdown):

{
  "category": string | null,         // e.g. "smart home", "beauty", "fitness"
  "audience_age": string[],          // any of "13-17","18-24","25-34","35-44","45-54","55+"
  "gender": "MALE" | "FEMALE" | "ANY",
  "tone": string | null,             // e.g. "authentic, energetic"
  "niche": string[],                 // creator niches / content tags
  "keywords": string[]               // key phrases for semantic search
}
"""


# --- Heuristic fallback ------------------------------------------------------

_AGE_PATTERNS = {
    "13-17": [r"\bteen", r"high ?school", r"13-17"],
    "18-24": [r"college", r"gen ?z", r"young adult", r"18-24"],
    "25-34": [r"millennial", r"25-34", r"young professional"],
    "35-44": [r"35-44", r"parents?", r"moms?", r"dads?"],
    "45-54": [r"45-54", r"over 40", r"middle[- ]aged"],
    "55+": [r"55\+", r"boomer", r"senior"],
}

_NICHE_HINTS = {
    "Beauty": ["beauty", "skincare", "makeup", "anti-aging"],
    "Fashion": ["fashion", "outfit", "streetwear", "style"],
    "Health": ["fitness", "wellness", "health", "gym", "workout"],
    "Food & Beverage": ["food", "recipe", "cooking", "beverage", "drink"],
    "Home": ["home", "decor", "cleaning", "household", "smart home"],
    "Phones & Electronics": ["gadget", "tech", "phone", "electronics", "smart"],
    "Sports & Outdoors": ["outdoor", "hiking", "sports", "adventure"],
    "Pet": ["pet", "dog", "cat", "puppy"],
    "Baby & Maternity": ["baby", "maternity", "mom", "parent"],
    "Toys & Hobbies": ["toy", "hobby", "craft"],
    "Tools & Hardware": ["tool", "diy", "hardware"],
    "Books": ["book", "reading", "booktok"],
}


def _heuristic_parse(query: str) -> ParsedQuery:
    q = query.lower()

    gender = "ANY"
    if re.search(r"\b(women|female|girls?|ladies)\b", q):
        gender = "FEMALE"
    elif re.search(r"\b(men|male|guys?|dudes?)\b", q):
        gender = "MALE"

    ages: list[str] = []
    for bucket, patterns in _AGE_PATTERNS.items():
        if any(re.search(p, q) for p in patterns):
            ages.append(bucket)

    niche: list[str] = []
    category: str | None = None
    for tag, hints in _NICHE_HINTS.items():
        if any(h in q for h in hints):
            niche.append(tag)
            if category is None:
                category = hints[0]

    tone = None
    tone_matches = re.findall(
        r"\b(authentic|energetic|casual|playful|luxurious|professional|chaotic|gentle|bold)\b",
        q,
    )
    if tone_matches:
        tone = ", ".join(sorted(set(tone_matches)))

    # naive keyword extraction — meaningful words longer than 3 chars
    stop = {
        "with", "that", "this", "from", "into", "find", "want", "need",
        "creators", "creator", "audience", "campaign", "engagement",
        "strong", "targeting", "target", "their", "about", "have", "some",
        "them", "very", "real", "best",
    }
    words = re.findall(r"[a-zA-Z][a-zA-Z\-]{3,}", q)
    keywords = []
    seen: set[str] = set()
    for w in words:
        if w in stop or w in seen:
            continue
        seen.add(w)
        keywords.append(w)
    keywords = keywords[:10]

    return ParsedQuery(
        category=category,
        audience_age=ages or ["18-24", "25-34"],
        gender=gender,  # type: ignore[arg-type]
        tone=tone,
        niche=niche,
        keywords=keywords,
    )


# --- Public API --------------------------------------------------------------


def _clean_json_block(text: str) -> str:
    """Strip markdown fences that Gemini sometimes wraps JSON with."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?", "", text).strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    return text


def parse_brief(query: str) -> ParsedQuery:
    """Parse a natural language brief into a :class:`ParsedQuery`.

    Uses Gemini when available, otherwise falls back to a regex heuristic.
    """
    model = get_chat_model()
    if model is None:
        return _heuristic_parse(query)

    try:
        prompt = f"{PARSE_SYSTEM_PROMPT}\n\nBrief:\n\"\"\"{query}\"\"\""
        resp = model.generate_content(prompt)
        raw = _clean_json_block(resp.text or "")
        data: Dict[str, Any] = json.loads(raw)
        # normalise a few fields before handing to pydantic
        if data.get("gender") not in {"MALE", "FEMALE", "ANY", None}:
            data["gender"] = "ANY"
        return ParsedQuery(**data)
    except Exception:
        return _heuristic_parse(query)
