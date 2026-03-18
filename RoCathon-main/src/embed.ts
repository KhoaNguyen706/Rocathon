import OpenAI from 'openai';
import supabase from './db';

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
  const { data: cached } = await supabase
    .from('query_cache')
    .select('embedding')
    .eq('query_text', query)
    .single();

  if (cached?.embedding) {
    const emb = cached.embedding;
    if (typeof emb === 'string') return JSON.parse(emb) as number[];
    return emb as number[];
  }

  const embedding = await getEmbedding(query);
  const embString = `[${embedding.join(',')}]`;

  await supabase
    .from('query_cache')
    .upsert({ query_text: query, embedding: embString });

  return embedding;
}
