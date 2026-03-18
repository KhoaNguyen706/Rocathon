import * as dotenv from 'dotenv';
dotenv.config();

import * as fs from 'fs';
import * as path from 'path';
import supabase from '../src/db';
import { getEmbeddings } from '../src/embed';
import type { Creator } from '../src/types';

const BATCH_SIZE = 50;

function buildEmbeddingText(creator: Creator): string {
  const tags = creator.content_style_tags.join(', ');
  const gender = creator.metrics.demographics.major_gender.toLowerCase();
  const ages = creator.metrics.demographics.age_ranges.join(', ');
  return `${creator.bio}. Content categories: ${tags}. Audience: primarily ${gender}, ages ${ages}.`;
}

async function ingest() {
  const filePath = path.resolve(__dirname, '..', 'creators.json');
  const raw = fs.readFileSync(filePath, 'utf-8');
  const creators: Creator[] = JSON.parse(raw);
  console.log(`Loaded ${creators.length} creators from JSON.`);

  for (let i = 0; i < creators.length; i += BATCH_SIZE) {
    const batch = creators.slice(i, i + BATCH_SIZE);
    const texts = batch.map(buildEmbeddingText);

    console.log(`Embedding batch ${i / BATCH_SIZE + 1} (${batch.length} creators)...`);
    const embeddings = await getEmbeddings(texts);

    const rows = batch.map((c, j) => ({
      username: c.username,
      bio: c.bio,
      content_style_tags: c.content_style_tags,
      projected_score: c.projected_score,
      follower_count: c.metrics.follower_count,
      total_gmv_30d: c.metrics.total_gmv_30d,
      avg_views_30d: c.metrics.avg_views_30d,
      engagement_rate: c.metrics.engagement_rate,
      gpm: c.metrics.gpm,
      major_gender: c.metrics.demographics.major_gender,
      gender_pct: c.metrics.demographics.gender_pct,
      age_ranges: c.metrics.demographics.age_ranges,
      embedding: `[${embeddings[j].join(',')}]`,
    }));

    const { error } = await supabase
      .from('creators')
      .upsert(rows, { onConflict: 'username' });

    if (error) throw error;
    console.log(`  Inserted ${batch.length} creators.`);
  }

  const { count } = await supabase
    .from('creators')
    .select('*', { count: 'exact', head: true });

  console.log(`Done. ${count} creators in database.`);
}

ingest().catch((err) => {
  console.error('Ingestion failed:', err);
  process.exit(1);
});
