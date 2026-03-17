import OpenAI from 'openai';
import pool from './db';

const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

export async function getEmbedding(text: string): Promise<number[]> {
  const res = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: text,
  });
  return res.data[0].embedding;
}

export async function getEmbeddings(texts: string[]): Promise<number[][]> {
  const res = await openai.embeddings.create({
    model: 'text-embedding-3-small',
    input: texts,
  });
  return res.data.map((d) => d.embedding);
}

export async function getEmbeddingCached(query: string): Promise<number[]> {
  const cached = await pool.query(
    'SELECT embedding::text FROM query_cache WHERE query_text = $1',
    [query]
  );

  if (cached.rows.length > 0) {
    const raw = cached.rows[0].embedding;
    return JSON.parse(raw) as number[];
  }

  const embedding = await getEmbedding(query);
  const embString = `[${embedding.join(',')}]`;

  await pool.query(
    'INSERT INTO query_cache (query_text, embedding) VALUES ($1, $2) ON CONFLICT (query_text) DO NOTHING',
    [query, embString]
  );

  return embedding;
}
