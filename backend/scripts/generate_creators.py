"""Generate a diverse, realistic creators.json dataset.

Produces 1000 creators matching the Pydantic schema in backend.models.schemas.
Run with:  python backend/scripts/generate_creators.py
"""
from __future__ import annotations

import json
import random
from pathlib import Path

random.seed(42)

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "data" / "creators.json"

# ---------------------------------------------------------------------------
# Niche templates: tag combos, bio snippets, first-name pool, handle suffixes
# ---------------------------------------------------------------------------

NICHE_TEMPLATES: list[dict] = [
    {
        "tags": ["Beauty"],
        "bios": [
            "Clean-girl beauty routines, skincare firsts, and honest product reviews.",
            "Luxury skincare and anti-aging deep dives for women who read ingredient lists.",
            "Drugstore vs high-end comparisons, dupes, and glowing skin tutorials.",
            "K-beauty routines, glass skin tips, and gentle actives explained.",
            "Barrier-repair skincare, dermatologist-vetted picks, and sensitive-skin friendly routines.",
            "Glow-up makeup, neutral glam, and everyday wearable beauty looks.",
            "Anti-aging rituals, retinoid guides, and honest over-40 skincare talk.",
        ],
        "handle_words": ["skin", "glow", "beauty", "derm", "clean", "radiant", "silk", "velvet"],
        "gender_bias": "FEMALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"], ["35-44", "45-54"]],
        "gmv_range": (15000, 220000),
        "followers_range": (40000, 900000),
        "gpm_range": (8.0, 22.0),
    },
    {
        "tags": ["Beauty", "Health"],
        "bios": [
            "Inner + outer beauty: collagen, supplements, and skincare that actually works.",
            "Wellness-focused beauty — clean ingredients, gut-skin axis, and daily rituals.",
            "Holistic glow: nutrition, hydration, and the serums I cannot live without.",
        ],
        "handle_words": ["wellness", "glowup", "holistic", "inside", "ritual"],
        "gender_bias": "FEMALE",
        "age_mix": [["25-34", "35-44"], ["35-44", "45-54"]],
        "gmv_range": (20000, 180000),
        "followers_range": (60000, 700000),
        "gpm_range": (9.0, 20.0),
    },
    {
        "tags": ["Fashion"],
        "bios": [
            "Everyday outfit inspo, capsule wardrobes, and affordable trend pieces.",
            "Summer hauls, college fits, and trendy drops under $50.",
            "Quiet luxury, elevated basics, and old-money style breakdowns.",
            "Curvy style, plus-size finds, and body-positive fit checks.",
            "Workwear meets streetwear — transitional pieces for the 9-to-5 girlie.",
            "Y2K revivals, vintage hunts, and thrift flips you can actually wear.",
        ],
        "handle_words": ["style", "fits", "wardrobe", "outfit", "closet", "chic", "drip"],
        "gender_bias": "FEMALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (10000, 260000),
        "followers_range": (30000, 850000),
        "gpm_range": (7.0, 18.0),
    },
    {
        "tags": ["Fashion (Men's)"],
        "bios": [
            "Menswear essentials, tailored fits, and wardrobe upgrades for real life.",
            "Streetwear drops, sneaker reviews, and hype-vs-worth breakdowns.",
            "Old money menswear: loafers, linen, and timeless basics.",
            "Gym-to-street fits, techwear, and everyday rotation breakdowns.",
        ],
        "handle_words": ["menswear", "fits", "tailored", "drip", "street", "wardrobe"],
        "gender_bias": "MALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (8000, 180000),
        "followers_range": (25000, 600000),
        "gpm_range": (6.5, 15.0),
    },
    {
        "tags": ["Health"],
        "bios": [
            "Gut health, probiotics, and the supplements that actually changed my energy.",
            "Evidence-based wellness — sleep, stress, and daily habits.",
            "Marathon training, recovery routines, and mobility for busy adults.",
            "Hormone health, cycle syncing, and women's wellness done simply.",
            "High-protein meals, macro tracking, and realistic fitness for beginners.",
        ],
        "handle_words": ["wellness", "fit", "strong", "vitality", "pulse", "thrive"],
        "gender_bias": None,
        "age_mix": [["25-34", "35-44"], ["35-44", "45-54"]],
        "gmv_range": (10000, 150000),
        "followers_range": (30000, 500000),
        "gpm_range": (6.0, 14.0),
    },
    {
        "tags": ["Food & Beverage"],
        "bios": [
            "30-minute family dinners, meal prep, and pantry staples that slap.",
            "High-protein recipes, viral TikTok food trends, and honest taste tests.",
            "Baker by night — sourdough, laminated pastry, and cozy kitchen vibes.",
            "Air fryer everything, budget meals, and one-pan weeknight dinners.",
            "Specialty coffee, latte art, and home barista gear reviews.",
        ],
        "handle_words": ["kitchen", "eats", "bites", "fork", "plate", "pantry", "cook"],
        "gender_bias": None,
        "age_mix": [["25-34", "35-44"], ["18-24", "25-34"], ["35-44", "45-54"]],
        "gmv_range": (5000, 120000),
        "followers_range": (25000, 700000),
        "gpm_range": (5.5, 13.0),
    },
    {
        "tags": ["Home"],
        "bios": [
            "Cozy home decor, small space hacks, and Amazon finds that upgrade any room.",
            "First-time homeowner DIYs, renovations, and budget-friendly makeovers.",
            "Rental-friendly decor, peel-and-stick wins, and aesthetic storage.",
            "Minimalist home organization, labeled pantries, and calm-aesthetic rooms.",
        ],
        "handle_words": ["home", "nest", "abode", "casa", "decor", "space"],
        "gender_bias": "FEMALE",
        "age_mix": [["25-34", "35-44"], ["35-44", "45-54"]],
        "gmv_range": (8000, 140000),
        "followers_range": (30000, 500000),
        "gpm_range": (6.5, 14.0),
    },
    {
        "tags": ["Sports & Outdoors"],
        "bios": [
            "Ultralight backpacking, thru-hike gear reviews, and trail storytelling.",
            "Rock climbing, bouldering, and outdoor gear for weekend warriors.",
            "Trail running, ultra-marathon training, and honest shoe breakdowns.",
            "Camping hacks, van life builds, and national park road trips.",
        ],
        "handle_words": ["trail", "peak", "summit", "wild", "ridge", "outdoor"],
        "gender_bias": "MALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (5000, 90000),
        "followers_range": (20000, 400000),
        "gpm_range": (5.0, 12.0),
    },
    {
        "tags": ["Toys & Hobbies"],
        "bios": [
            "Lego builds, collector sets, and display shelf deep dives.",
            "Trading card unboxings, Pokemon pulls, and collector market updates.",
            "Plush reviews, kidcore aesthetics, and soft toy hauls.",
            "Board game reviews for families, couples, and heavy strategy nights.",
        ],
        "handle_words": ["toys", "collector", "pulls", "build", "hobby", "play"],
        "gender_bias": None,
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (3000, 80000),
        "followers_range": (15000, 350000),
        "gpm_range": (4.5, 11.0),
    },
    {
        "tags": ["Baby & Maternity"],
        "bios": [
            "First-time mom honest reviews, must-have registry items, and newborn tips.",
            "Pregnancy journey, bump updates, and maternity fashion finds.",
            "Toddler parenting, Montessori setups, and realistic routines with kids.",
        ],
        "handle_words": ["mama", "bump", "mom", "tiny", "nest", "little"],
        "gender_bias": "FEMALE",
        "age_mix": [["25-34", "35-44"]],
        "gmv_range": (8000, 120000),
        "followers_range": (20000, 450000),
        "gpm_range": (6.0, 14.0),
    },
    {
        "tags": ["Phones & Electronics"],
        "bios": [
            "Apple ecosystem deep dives, iOS tips, and new hardware reviews.",
            "Android flagships, camera comparisons, and honest phone buying advice.",
            "Desk setups, mechanical keyboards, and productivity gadget reviews.",
            "Smart home tech, audio gear, and tech deals worth your money.",
        ],
        "handle_words": ["tech", "gear", "gadget", "wired", "byte", "circuit"],
        "gender_bias": "MALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (10000, 200000),
        "followers_range": (40000, 900000),
        "gpm_range": (7.0, 16.0),
    },
    {
        "tags": ["Books"],
        "bios": [
            "Romance recs, BookTok hype, and honest five-star reviews.",
            "Fantasy deep dives, series breakdowns, and TBR hauls.",
            "Self-help, productivity books, and lessons I wish I learned earlier.",
        ],
        "handle_words": ["reads", "pages", "book", "shelf", "lit", "story"],
        "gender_bias": "FEMALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (2000, 40000),
        "followers_range": (15000, 250000),
        "gpm_range": (3.5, 9.0),
    },
    {
        "tags": ["Beauty", "Fashion"],
        "bios": [
            "Full get-ready-with-me content: makeup, outfit, and the details.",
            "Soft glam plus elevated closet staples for date nights and the office.",
            "Editorial beauty looks paired with runway-inspired outfits.",
        ],
        "handle_words": ["grwm", "polished", "muse", "edit", "styled"],
        "gender_bias": "FEMALE",
        "age_mix": [["18-24", "25-34"], ["25-34", "35-44"]],
        "gmv_range": (12000, 220000),
        "followers_range": (40000, 800000),
        "gpm_range": (7.5, 18.0),
    },
]

FIRST_NAMES = [
    "ava", "mia", "zoe", "ella", "isla", "nora", "lily", "emma", "olivia", "sophia",
    "maya", "jade", "ivy", "ruby", "hazel", "aria", "chloe", "grace", "luna", "iris",
    "noah", "liam", "ethan", "mason", "lucas", "logan", "jaxon", "leo", "kai", "asher",
    "caleb", "owen", "elijah", "dylan", "finn", "theo", "miles", "jose", "andre", "zach",
    "sara", "priya", "aisha", "mei", "nia", "sana", "rita", "diana", "bri", "tess",
    "kyle", "ryan", "devin", "jalen", "marco", "adrian", "bryce", "hunter", "trent", "cole",
    "bella", "luca", "sienna", "paige", "harper", "cora", "willow", "stella", "quinn", "riley",
    "jordan", "avery", "peyton", "morgan", "reese", "skyler", "rowan", "taylor", "casey", "sage",
]

HANDLE_STYLES = [
    "{word}_with_{name}",
    "{name}_{word}",
    "{word}_{name}",
    "the_{word}_{name}",
    "{name}s_{word}",
    "{word}_diaries_{name}",
    "{name}_{word}_lab",
    "{word}_club_{name}",
]


def _int_step(low: int, high: int, step: int) -> int:
    span = (high - low) // step
    return low + random.randint(0, span) * step


def _build_handle(words: list[str], used: set[str]) -> str:
    for _ in range(50):
        name = random.choice(FIRST_NAMES)
        word = random.choice(words)
        style = random.choice(HANDLE_STYLES)
        handle = style.format(word=word, name=name)
        if handle not in used:
            used.add(handle)
            return handle
    # Fallback guaranteed-unique handle
    handle = f"{random.choice(words)}_{random.choice(FIRST_NAMES)}_{len(used)}"
    used.add(handle)
    return handle


def _pick_demographics(template: dict) -> dict:
    bias = template["gender_bias"]
    if bias == "FEMALE":
        major = "FEMALE"
        pct = random.randint(6500, 8800)
    elif bias == "MALE":
        major = "MALE"
        pct = random.randint(6200, 8600)
    else:
        major = random.choice(["FEMALE", "MALE"])
        pct = random.randint(5200, 6800)
    age_ranges = list(random.choice(template["age_mix"]))
    return {
        "major_gender": major,
        "gender_pct": pct,
        "age_ranges": age_ranges,
    }


def _generate_creator(template: dict, used: set[str]) -> dict:
    username = _build_handle(template["handle_words"], used)
    bio = random.choice(template["bios"])

    # Tags: template tags, sometimes add a complementary tag
    tags = list(template["tags"])
    if random.random() < 0.12 and len(tags) == 1:
        bonus = random.choice(["Health", "Fashion", "Beauty", "Home", "Food & Beverage"])
        if bonus not in tags:
            tags.append(bonus)

    followers = _int_step(*template["followers_range"], 1000)
    # Viewership ~ 1.5x - 3x followers
    avg_views = int(followers * random.uniform(1.4, 3.2))
    avg_views = (avg_views // 1000) * 1000

    # GMV: weighted so ~20% creators report zero (no shop presence)
    has_shop = random.random() < 0.8
    if has_shop:
        gmv = _int_step(*template["gmv_range"], 500)
        gpm = round(random.uniform(*template["gpm_range"]), 2)
    else:
        gmv = 0
        gpm = 0

    engagement = round(random.uniform(0.04, 0.12), 3)

    # Projected score loosely correlates with GMV + engagement + followers
    base = 55.0
    base += min(25.0, gmv / 10000.0)
    base += engagement * 120.0
    base += min(8.0, followers / 150000.0)
    base += random.uniform(-6.0, 6.0)
    projected_score = round(max(55.0, min(97.0, base)), 2)

    return {
        "username": username,
        "bio": bio,
        "content_style_tags": tags,
        "projected_score": projected_score,
        "metrics": {
            "follower_count": followers,
            "total_gmv_30d": gmv,
            "avg_views_30d": avg_views,
            "engagement_rate": engagement,
            "gpm": gpm,
            "demographics": _pick_demographics(template),
        },
    }


def generate(n: int = 1000) -> list[dict]:
    used: set[str] = set()
    creators: list[dict] = []
    # Weight templates so the dataset looks realistic across niches
    weights = [
        14, 8, 14, 8, 12, 12, 8, 8, 6, 6, 8, 4, 6,
    ]
    assert len(weights) == len(NICHE_TEMPLATES)
    for _ in range(n):
        template = random.choices(NICHE_TEMPLATES, weights=weights, k=1)[0]
        creators.append(_generate_creator(template, used))
    return creators


def main() -> None:
    data = generate(1000)
    OUTPUT_PATH.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Wrote {len(data)} creators to {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
