import * as dotenv from 'dotenv';
dotenv.config();

import pool from '../src/db';

async function setupDatabase() {
  const client = await pool.connect();
  try {
    await client.query('CREATE EXTENSION IF NOT EXISTS vector;');
    console.log('pgvector extension enabled.');

    await client.query(`
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
    `);
    console.log('creators table created.');

    await client.query(`
      CREATE TABLE IF NOT EXISTS query_cache (
        query_text  TEXT PRIMARY KEY,
        embedding   vector(1536),
        created_at  TIMESTAMPTZ DEFAULT NOW()
      );
    `);
    console.log('query_cache table created.');

    console.log('Database setup complete.');
  } finally {
    client.release();
    await pool.end();
  }
}

setupDatabase().catch((err) => {
  console.error('Setup failed:', err);
  process.exit(1);
});
