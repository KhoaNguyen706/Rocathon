"""Creator data source abstraction.

Supported stores:
- json (default)
- postgres
- mongo

The app falls back to JSON when DB credentials are missing or a DB read fails.
"""

from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import List

from models.schemas import Creator, CreatorMetrics, Demographics

try:
    import psycopg  # type: ignore
except Exception:  # pragma: no cover
    psycopg = None  # type: ignore

try:
    from pymongo import MongoClient  # type: ignore
except Exception:  # pragma: no cover
    MongoClient = None  # type: ignore


log = logging.getLogger("copilot.creator_store")


def _to_creator(item: dict) -> Creator:
    metrics = item.get("metrics", {}) or {}
    demo = metrics.get("demographics", {}) or {}
    return Creator(
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


def _load_json(path: Path) -> List[Creator]:
    with path.open("r", encoding="utf-8") as f:
        raw = json.load(f)
    out: List[Creator] = []
    for item in raw:
        try:
            out.append(_to_creator(item))
        except Exception:
            continue
    return out


def _load_postgres() -> List[Creator]:
    database_url = os.getenv("DATABASE_URL")
    if not database_url or psycopg is None:
        return []

    table = os.getenv("POSTGRES_CREATORS_TABLE", "creators")
    out: List[Creator] = []
    with psycopg.connect(database_url) as conn:
        with conn.cursor() as cur:
            # Preferred schema: payload JSONB
            try:
                cur.execute(f"SELECT payload FROM {table}")
                rows = cur.fetchall()
                for row in rows:
                    payload = row[0] if isinstance(row[0], dict) else json.loads(row[0])
                    out.append(_to_creator(payload))
                return out
            except Exception:
                # Clear failed transaction state before trying fallback query.
                conn.rollback()

            # Fallback schema: plain columns; row_to_json works for many layouts.
            cur.execute(f"SELECT row_to_json(t)::text FROM {table} AS t")
            rows = cur.fetchall()
            for row in rows:
                payload = json.loads(row[0])
                out.append(_to_creator(payload))
    return out


def _load_mongo() -> List[Creator]:
    mongo_uri = os.getenv("MONGO_URI")
    if not mongo_uri or MongoClient is None:
        return []
    db_name = os.getenv("MONGO_DB", "creator_copilot")
    collection = os.getenv("MONGO_CREATORS_COLLECTION", "creators")

    out: List[Creator] = []
    client = MongoClient(mongo_uri)
    try:
        docs = client[db_name][collection].find({})
        for d in docs:
            d.pop("_id", None)
            try:
                out.append(_to_creator(d))
            except Exception:
                continue
    finally:
        client.close()
    return out


def load_creators_from_store(default_json_path: Path) -> List[Creator]:
    """Load creators from configured store, with JSON fallback."""
    store = os.getenv("CREATOR_STORE", "json").strip().lower()

    try:
        if store == "postgres":
            creators = _load_postgres()
            if creators:
                log.info("Loaded %d creators from PostgreSQL.", len(creators))
                return creators
            log.warning("PostgreSQL creator store empty/unavailable; falling back to JSON.")
        elif store == "mongo":
            creators = _load_mongo()
            if creators:
                log.info("Loaded %d creators from MongoDB.", len(creators))
                return creators
            log.warning("Mongo creator store empty/unavailable; falling back to JSON.")
    except Exception as exc:
        log.warning("Creator store '%s' failed: %s. Falling back to JSON.", store, exc)

    creators = _load_json(default_json_path)
    log.info("Loaded %d creators from JSON (%s).", len(creators), default_json_path)
    return creators
