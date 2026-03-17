import * as dotenv from 'dotenv';
dotenv.config();

import * as fs from 'fs';
import * as path from 'path';
import pool from '../src/db';
import { getEmbeddings } from '../src/embed';
import type { Creator } from '../src/types';

const BATCH_SIZE = 50;

function buildEmbeddingText(creator: Creator): string {
  return `${creator.bio}. Tags: ${creator.content_style_tags.join(', ')}`;
}

async function ingest() {
  const filePath = path.resolve(__dirname, '..', 'creators.json');
  const raw = fs.readFileSync(filePath, 'utf-8');
  const creators: Creator[] = JSON.parse(raw);
  console.log(`Loaded ${creators.length} creators from JSON.`);

  const client = await pool.connect();

  try {
    for (let i = 0; i < creators.length; i += BATCH_SIZE) {
      const batch = creators.slice(i, i + BATCH_SIZE);
      const texts = batch.map(buildEmbeddingText);

      console.log(`Embedding batch ${i / BATCH_SIZE + 1} (${batch.length} creators)...`);
      const embeddings = await getEmbeddings(texts);

      for (let j = 0; j < batch.length; j++) {
        const c = batch[j];
        const emb = embeddings[j];
        const embString = `[${emb.join(',')}]`;

        await client.query(
          `INSERT INTO creators
            (username, bio, content_style_tags, projected_score,
             follower_count, total_gmv_30d, avg_views_30d,
             engagement_rate, gpm, major_gender, gender_pct,
             age_ranges, embedding)
           VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12,$13)
           ON CONFLICT (username) DO UPDATE SET
             bio = EXCLUDED.bio,
             content_style_tags = EXCLUDED.content_style_tags,
             projected_score = EXCLUDED.projected_score,
             follower_count = EXCLUDED.follower_count,
             total_gmv_30d = EXCLUDED.total_gmv_30d,
             avg_views_30d = EXCLUDED.avg_views_30d,
             engagement_rate = EXCLUDED.engagement_rate,
             gpm = EXCLUDED.gpm,
             major_gender = EXCLUDED.major_gender,
             gender_pct = EXCLUDED.gender_pct,
             age_ranges = EXCLUDED.age_ranges,
             embedding = EXCLUDED.embedding`,
          [
            c.username,
            c.bio,
            c.content_style_tags,
            c.projected_score,
            c.metrics.follower_count,
            c.metrics.total_gmv_30d,
            c.metrics.avg_views_30d,
            c.metrics.engagement_rate,
            c.metrics.gpm,
            c.metrics.demographics.major_gender,
            c.metrics.demographics.gender_pct,
            c.metrics.demographics.age_ranges,
            embString,
          ]
        );
      }

      console.log(`  Inserted ${batch.length} creators.`);
    }

    // IVFFlat index skipped — not needed for 200 rows, and Supabase free tier
    // doesn't have enough maintenance_work_mem. Exact scan is fast at this scale.

    const { rows } = await client.query('SELECT COUNT(*) FROM creators;');
    console.log(`Done. ${rows[0].count} creators in database.`);
  } finally {
    client.release();
    await pool.end();
  }
}

ingest().catch((err) => {
  console.error('Ingestion failed:', err);
  process.exit(1);
});
