"""Hybrid re-ranking logic.

final_score = 0.40 * semantic_score
            + 0.50 * projected_score (normalised to 0–1)
            + 0.10 * demographic_bonus
"""

from __future__ import annotations

from typing import List, Tuple

from models.schemas import (
    Creator,
    CreatorScores,
    ParsedQuery,
    RankedCreator,
)


W_SEMANTIC = 0.40
W_PROJECTED = 0.50
W_DEMOGRAPHIC = 0.10


def _normalize_projected(raw: float) -> float:
    """Map RoC's 60–100 score into 0–1."""
    return max(0.0, min(1.0, (raw - 60.0) / 40.0))


def _demographic_bonus(creator: Creator, parsed: ParsedQuery) -> float:
    """Return 1.0 / 0.5 / 0.0 depending on how well the creator's audience
    overlaps with the brand's target audience."""
    demo = creator.metrics.demographics

    # Gender match — if parsed gender is ANY we treat it as a match.
    gender_match = (
        parsed.gender == "ANY"
        or parsed.gender is None
        or demo.major_gender == parsed.gender
    )

    # Age overlap
    if parsed.audience_age:
        age_overlap = any(age in demo.age_ranges for age in parsed.audience_age)
    else:
        age_overlap = True  # brief didn't constrain, so it's a pass

    if gender_match and age_overlap:
        return 1.0
    if gender_match or age_overlap:
        return 0.5
    return 0.0


def _niche_overlap(creator: Creator, parsed: ParsedQuery) -> bool:
    """Whether creator tags overlap with parsed target niches."""
    if not parsed.niche:
        return True
    creator_tags = {t.lower().strip() for t in creator.content_style_tags}
    target = {t.lower().strip() for t in parsed.niche}
    return bool(creator_tags & target)


def rerank(
    candidates: List[Tuple[Creator, float]],
    parsed: ParsedQuery,
    top_k: int = 10,
) -> List[RankedCreator]:
    """Apply the hybrid scoring formula and return the top-K creators."""
    ranked: List[RankedCreator] = []
    for creator, semantic_score in candidates:
        niche_match = _niche_overlap(creator, parsed)
        projected_norm = _normalize_projected(creator.projected_score)
        demo_bonus = _demographic_bonus(creator, parsed)

        final = (
            W_SEMANTIC * semantic_score
            + W_PROJECTED * projected_norm
            + W_DEMOGRAPHIC * demo_bonus
        )

        # Precision guard:
        # If the brief includes an explicit niche (e.g. Beauty), down-rank
        # creators whose tags are out-of-niche. This prevents high projected
        # GMV creators in unrelated categories from dominating.
        if parsed.niche and not niche_match:
            final -= 0.20
            if semantic_score < 0.35:
                final -= 0.20

        final = max(0.0, min(1.0, final))

        ranked.append(
            RankedCreator(
                **creator.model_dump(),
                scores=CreatorScores(
                    semantic_score=round(semantic_score, 4),
                    projected_score=round(projected_norm, 4),
                    demographic_bonus=round(demo_bonus, 4),
                    final_score=round(final, 4),
                ),
            )
        )

    ranked.sort(key=lambda r: r.scores.final_score, reverse=True)
    return ranked[:top_k]
