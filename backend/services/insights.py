"""Agent #2 — generate a natural language insights summary for a ranked list."""

from __future__ import annotations

from collections import Counter
from typing import List

from models.schemas import ParsedQuery, RankedCreator
from services.gemini_client import get_chat_model


INSIGHTS_PROMPT = """You are a creator-marketing strategist. Given the
campaign brief and the top ranked creators, write a short (3–5 sentence)
insight summary for the brand team.

Cover:
- why these creators were selected (patterns you notice),
- trends in niches or audience demographics,
- one tradeoff or risk to flag.

Be concrete, reference specific creators by @username, and avoid generic
marketing fluff.
"""


def _summarise_ranked(ranked: List[RankedCreator]) -> str:
    """Build a compact text summary of the ranked results for the LLM."""
    lines = []
    for r in ranked:
        tags = ", ".join(r.content_style_tags) or "general"
        demo = r.metrics.demographics
        ages = ", ".join(demo.age_ranges) or "—"
        lines.append(
            f"- @{r.username} | niches: {tags} | audience: {demo.major_gender} {ages} "
            f"| semantic={r.scores.semantic_score:.2f} "
            f"projected={r.scores.projected_score:.2f} "
            f"final={r.scores.final_score:.2f}"
        )
    return "\n".join(lines)


def _heuristic_insights(parsed: ParsedQuery, ranked: List[RankedCreator]) -> str:
    if not ranked:
        return "No creators matched the brief — try broadening your target audience or category."

    niche_counts = Counter(t for r in ranked for t in r.content_style_tags)
    top_niches = ", ".join(n for n, _ in niche_counts.most_common(3)) or "mixed"

    gender_counts = Counter(r.metrics.demographics.major_gender for r in ranked)
    dominant_gender = gender_counts.most_common(1)[0][0].lower()

    avg_semantic = sum(r.scores.semantic_score for r in ranked) / len(ranked)
    avg_final = sum(r.scores.final_score for r in ranked) / len(ranked)

    top = ranked[0]

    return (
        f"The top {len(ranked)} creators skew toward {top_niches} niches with an "
        f"audience that is primarily {dominant_gender}. @{top.username} leads the list with "
        f"a final score of {top.scores.final_score:.2f}, balancing a {top.scores.semantic_score:.2f} "
        f"semantic match with a strong projected commerce score. Average semantic match is "
        f"{avg_semantic:.2f} and average final score is {avg_final:.2f}. "
        f"Tradeoff to flag: the ranking is pulled heavily by projected GMV (weight 0.50), "
        f"so highly-relevant but early-stage creators may be under-indexed — consider a secondary "
        f"pass for discovery."
    )


def generate_insights(parsed: ParsedQuery, ranked: List[RankedCreator]) -> str:
    """Produce a short natural language insights summary via Gemini.

    Falls back to a deterministic template when Gemini isn't configured.
    """
    model = get_chat_model()
    if model is None or not ranked:
        return _heuristic_insights(parsed, ranked)

    try:
        parsed_json = parsed.model_dump_json(indent=2)
        body = _summarise_ranked(ranked)
        prompt = (
            f"{INSIGHTS_PROMPT}\n\n"
            f"Parsed brief:\n{parsed_json}\n\n"
            f"Top creators:\n{body}\n"
        )
        resp = model.generate_content(prompt)
        text = (resp.text or "").strip()
        return text or _heuristic_insights(parsed, ranked)
    except Exception:
        return _heuristic_insights(parsed, ranked)
