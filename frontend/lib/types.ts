export interface ParsedQuery {
  category: string | null;
  audience_age: string[];
  gender: "MALE" | "FEMALE" | "ANY" | null;
  tone: string | null;
  niche: string[];
  keywords: string[];
}

export interface Demographics {
  major_gender: "MALE" | "FEMALE";
  gender_pct: number;
  age_ranges: string[];
}

export interface CreatorMetrics {
  follower_count: number;
  total_gmv_30d: number;
  avg_views_30d: number;
  engagement_rate: number;
  gpm: number;
  demographics: Demographics;
}

export interface CreatorScores {
  semantic_score: number;
  projected_score: number;
  demographic_bonus: number;
  final_score: number;
}

export interface RankedCreator {
  username: string;
  bio: string;
  content_style_tags: string[];
  projected_score: number;
  metrics: CreatorMetrics;
  scores: CreatorScores;
}

export interface SearchResponse {
  parsed_query: ParsedQuery;
  results: RankedCreator[];
  insights: string;
}
