import * as dotenv from 'dotenv';
dotenv.config();

import pool from './db';
import { getEmbeddingCached } from './embed';
import type { BrandProfile, RankedCreator, Industry } from './types';

const CANDIDATE_LIMIT = 50;

const WEIGHT_SEMANTIC = 0.40;
const WEIGHT_PROJECTED = 0.45;
const WEIGHT_DEMOGRAPHIC = 0.15;

function computeDemographicBonus(
  creatorGender: string,
  creatorAgeRanges: string[],
  brand: BrandProfile
): number {
  const genderMatch = creatorGender === brand.target_audience.gender;
  const ageOverlap = creatorAgeRanges.some((range) =>
    brand.target_audience.age_ranges.includes(range)
  );

  if (genderMatch && ageOverlap) return 1.0;
  if (genderMatch || ageOverlap) return 0.5;
  return 0.0;
}

function normalizeProjectedScore(score: number): number {
  return Math.max(0, Math.min(1, (score - 60) / 40));
}

export async function searchCreators(
  query: string,
  brandProfile: BrandProfile
): Promise<RankedCreator[]> {
  const queryEmbedding = await getEmbeddingCached(query);
  const embString = `[${queryEmbedding.join(',')}]`;

  const { rows } = await pool.query(
    `SELECT
       username, bio, content_style_tags, projected_score,
       follower_count, total_gmv_30d, avg_views_30d,
       engagement_rate, gpm, major_gender, gender_pct, age_ranges,
       1 - (embedding <=> $1::vector) AS semantic_score
     FROM creators
     ORDER BY embedding <=> $1::vector
     LIMIT $2`,
    [embString, CANDIDATE_LIMIT]
  );

  const ranked: RankedCreator[] = rows.map((row: any) => {
    const semanticScore: number = parseFloat(row.semantic_score);
    const projectedRaw: number = parseFloat(row.projected_score);
    const normalizedProjected = normalizeProjectedScore(projectedRaw);

    const demographicBonus = computeDemographicBonus(
      row.major_gender,
      row.age_ranges ?? [],
      brandProfile
    );

    const finalScore =
      WEIGHT_SEMANTIC * semanticScore +
      WEIGHT_PROJECTED * normalizedProjected +
      WEIGHT_DEMOGRAPHIC * demographicBonus;

    return {
      username: row.username,
      bio: row.bio,
      content_style_tags: row.content_style_tags as Industry[],
      projected_score: projectedRaw,
      metrics: {
        follower_count: row.follower_count,
        total_gmv_30d: row.total_gmv_30d,
        avg_views_30d: row.avg_views_30d,
        engagement_rate: row.engagement_rate,
        gpm: row.gpm,
        demographics: {
          major_gender: row.major_gender,
          gender_pct: row.gender_pct,
          age_ranges: row.age_ranges ?? [],
        },
      },
      scores: {
        semantic_score: parseFloat(semanticScore.toFixed(4)),
        projected_score: projectedRaw,
        final_score: parseFloat(finalScore.toFixed(4)),
      },
    };
  });

  ranked.sort((a, b) => b.scores.final_score - a.scores.final_score);

  return ranked;
}
