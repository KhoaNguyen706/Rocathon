-- Run this in the Supabase SQL Editor (one time setup)

CREATE EXTENSION IF NOT EXISTS vector;

CREATE TABLE IF NOT EXISTS creators (
  id              SERIAL PRIMARY KEY,
  username        TEXT UNIQUE NOT NULL,
  bio             TEXT,
  content_style_tags TEXT[],
  projected_score FLOAT,
  follower_count  INT,
  total_gmv_30d   FLOAT,
  avg_views_30d   FLOAT,
  engagement_rate FLOAT,
  gpm             FLOAT,
  major_gender    TEXT,
  gender_pct      FLOAT,
  age_ranges      TEXT[],
  embedding       vector(1536)
);

CREATE TABLE IF NOT EXISTS query_cache (
  query_text  TEXT PRIMARY KEY,
  embedding   vector(1536),
  created_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE OR REPLACE FUNCTION match_creators(
  query_embedding vector(1536),
  match_count int DEFAULT 50
)
RETURNS TABLE (
  username text,
  bio text,
  content_style_tags text[],
  projected_score float,
  follower_count int,
  total_gmv_30d float,
  avg_views_30d float,
  engagement_rate float,
  gpm float,
  major_gender text,
  gender_pct float,
  age_ranges text[],
  semantic_score float
) AS $$
  SELECT
    c.username, c.bio, c.content_style_tags, c.projected_score,
    c.follower_count, c.total_gmv_30d, c.avg_views_30d,
    c.engagement_rate, c.gpm, c.major_gender, c.gender_pct, c.age_ranges,
    (1 - (c.embedding <=> query_embedding))::float AS semantic_score
  FROM creators c
  ORDER BY c.embedding <=> query_embedding
  LIMIT match_count;
$$ LANGUAGE sql;
