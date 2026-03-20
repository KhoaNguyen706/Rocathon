import * as dotenv from 'dotenv';
dotenv.config();

import * as fs from 'fs';
import * as path from 'path';
import supabase from '../src/db';
import { getEmbeddings } from '../src/embed';
import type { Creator } from '../src/types';

const BATCH_SIZE = 50;

function buildEmbeddingText(creator: Creator): string {
  const bio = creator.bio || '';
  const tags = (creator.content_style_tags || []).join(', ');
  const demo = creator.metrics?.demographics;
  const gender = demo?.major_gender?.toLowerCase() || 'unknown';
  const ages = (demo?.age_ranges || []).join(', ');
  return `${bio}. Content categories: ${tags}. Audience: primarily ${gender}, ages ${ages}.`;
}

async function ingest() {
  const customFile = process.argv[2];
  const fileName = customFile || 'creators.json';
  const filePath = path.resolve(__dirname, '..', fileName);
  const raw = fs.readFileSync(filePath, 'utf-8');
  const creators: Creator[] = JSON.parse(raw);
  console.log(`Loaded ${creators.length} creators from JSON.`);

  const { error: delError } = await supabase.from('creators').delete().neq('id', 0);
  if (delError) throw delError;
  console.log('Cleared existing creators from database.');

  for (let i = 0; i < creators.length; i += BATCH_SIZE) {
    const batch = creators.slice(i, i + BATCH_SIZE);
    const texts = batch.map(buildEmbeddingText);

    console.log(`Embedding batch ${i / BATCH_SIZE + 1} (${batch.length} creators)...`);
    const embeddings = await getEmbeddings(texts);

    const rows = batch.map((c, j) => ({
      username: c.username,
      bio: c.bio || '',
      content_style_tags: c.content_style_tags || [],
      projected_score: c.projected_score ?? 60,
      follower_count: c.metrics?.follower_count ?? 0,
      total_gmv_30d: c.metrics?.total_gmv_30d ?? 0,
      avg_views_30d: c.metrics?.avg_views_30d ?? 0,
      engagement_rate: c.metrics?.engagement_rate ?? 0,
      gpm: c.metrics?.gpm ?? 0,
      major_gender: c.metrics?.demographics?.major_gender || 'UNKNOWN',
      gender_pct: c.metrics?.demographics?.gender_pct ?? 0,
      age_ranges: c.metrics?.demographics?.age_ranges || [],
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
