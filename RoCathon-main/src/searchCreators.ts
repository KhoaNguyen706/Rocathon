import * as dotenv from 'dotenv';
dotenv.config();

import supabase from './db';
import { getEmbeddingCached } from './embed';
import type { BrandProfile, RankedCreator, Industry } from './types';

const CANDIDATE_LIMIT = 50;

const W_SEMANTIC = 0.40;
const W_PROJECTED = 0.50;
const W_DEMOGRAPHIC = 0.10;

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

  const { data: rows, error } = await supabase.rpc('match_creators', {
    query_embedding: embString,
    match_count: CANDIDATE_LIMIT,
  });

  if (error) throw error;

  const ranked: RankedCreator[] = (rows ?? []).map((row: any) => {
    const semanticScore: number = parseFloat(row.semantic_score) || 0;
    const projectedRaw: number = parseFloat(row.projected_score) || 60;
    const normalizedProjected = normalizeProjectedScore(projectedRaw);

    const demographicBonus = computeDemographicBonus(
      row.major_gender || '',
      row.age_ranges ?? [],
      brandProfile
    );

    const finalScore =
      W_SEMANTIC * semanticScore +
      W_PROJECTED * normalizedProjected +
      W_DEMOGRAPHIC * demographicBonus;

    return {
      username: row.username,
      bio: row.bio || '',
      content_style_tags: (row.content_style_tags || []) as Industry[],
      projected_score: projectedRaw,
      metrics: {
        follower_count: row.follower_count ?? 0,
        total_gmv_30d: row.total_gmv_30d ?? 0,
        avg_views_30d: row.avg_views_30d ?? 0,
        engagement_rate: row.engagement_rate ?? 0,
        gpm: row.gpm ?? 0,
        demographics: {
          major_gender: row.major_gender || 'UNKNOWN',
          gender_pct: row.gender_pct ?? 0,
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
