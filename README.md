# AI Creator Discovery Copilot

Natural-language creator search for brand campaigns. Type a brief in
plain English → get a ranked shortlist of creators plus an AI-generated
insights summary.

> Evolution of the previous RoCathon TypeScript search engine. This
> version is a full web app built around a **Moss** semantic retrieval
> core, a FastAPI multi-agent backend (Gemini + OpenAI + LangChain), and a
> Next.js + Tailwind frontend.

## Architecture

```
Next.js (App Router)  ──►  FastAPI  ──►  ┌─────────────────────────────┐
                                         │ 1. Parse brief  (Gemini)    │
                                         │ 2. Moss retrieval (top 50)  │
                                         │ 3. Hybrid rerank (Python)   │
                                         │ 4. Insights     (Gemini)    │
                                         └─────────────────────────────┘
                                                │
                                                ▼
                                       JSON ► rendered in UI
```

### Hybrid scoring

```
final_score = 0.40 * semantic_score
            + 0.50 * projected_score   (normalised 60–100 → 0–1)
            + 0.10 * demographic_bonus
```

| Signal             | Weight | What it is |
|--------------------|:------:|------------|
| Semantic score     | 0.40   | Cosine similarity between query and creator embedding |
| Projected score    | 0.50   | RoC's pre-computed commerce score |
| Demographic bonus  | 0.10   | 1.0 if gender + age match, 0.5 for one match, 0.0 otherwise |

## Project structure

```
/
├── backend/                # FastAPI + LangChain + Moss
│   ├── main.py             # App entry, boots Moss on startup
│   ├── routers/search.py   # POST /search
│   ├── services/
│   │   ├── parse_brief.py      # Agent 1 — brief → structured JSON (Gemini)
│   │   ├── moss_retriever.py   # Semantic index (provider embeddings + fallback)
│   │   ├── embedding_client.py # Provider-aware embedding client + cache hooks
│   │   ├── cache_store.py      # Embedding + search result cache
│   │   ├── creator_store.py    # PostgreSQL / JSON creator source
│   │   ├── reranker.py         # Hybrid scoring formula
│   │   ├── insights.py         # Agent 2 — results → summary (Gemini)
│   │   ├── orchestrator.py     # LangChain Runnable pipeline
│   │   └── gemini_client.py    # Thin SDK wrapper
│   ├── models/schemas.py   # Pydantic request/response models
│   ├── data/creators.json  # ~200 mock creators
│   └── Dockerfile
├── frontend/               # Next.js 14 + Tailwind
│   ├── app/page.tsx        # Single-page UI
│   ├── components/         # SearchForm, ParsedQueryCard, ResultsTable, InsightsPanel
│   ├── lib/{api,types}.ts  # Typed API client
│   └── Dockerfile
├── docker-compose.yml
└── RoCathon-main/          # Previous hackathon submission (kept for reference)
```

## Quick start

### Option A — Docker Compose (zero local install)

```bash
cp .env.example .env
# optionally paste your OpenAI/Gemini keys into .env
docker compose up -d --build
```

Visit **http://localhost:3000**.

### Choose creator store + cache

In `.env` (root or `backend/.env`) set storage:

- `CREATOR_STORE=postgres` (recommended default)
- `DATABASE_URL=...` (PostgreSQL)
- `CACHE_BACKEND=sqlite|memory`
- `CACHE_SQLITE_PATH=./data/cache.db`
- `SEARCH_CACHE_TTL_SECONDS=1800`

By default, Docker Compose starts `frontend`, `backend`, and `postgres`
together, so no extra infrastructure setup is needed.

### Option B — Run locally

**Backend**

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows PowerShell
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
cp .env.example .env            # optional
uvicorn main:app --reload --port 8000
```

**Frontend**

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Frontend: http://localhost:3000 · Backend: http://localhost:8000/docs

## API

### `POST /search`

```json
{
  "query": "Find creators for affordable smart home gadgets targeting college students, Gen Z",
  "top_k": 10
}
```

**Response**

```json
{
  "parsed_query": {
    "category": "smart home",
    "audience_age": ["18-24"],
    "gender": "ANY",
    "tone": null,
    "niche": ["Home", "Phones & Electronics"],
    "keywords": ["affordable", "smart", "home", "gadgets", "college", "students"]
  },
  "results": [
    {
      "username": "…",
      "bio": "…",
      "content_style_tags": ["Home"],
      "projected_score": 88,
      "metrics": { "…": "…" },
      "scores": {
        "semantic_score": 0.7321,
        "projected_score": 0.7,
        "demographic_bonus": 1.0,
        "final_score": 0.7429
      }
    }
  ],
  "insights": "The top 10 creators skew toward Home and Phones & Electronics…"
}
```

### `GET /health`

Returns whether Gemini is configured and which Moss backend is active
(`embedding:openai` / `embedding:gemini` or `tfidf` fallback), plus
active cache backend/provider info.

## About "Moss"

`MossRetriever` (in `backend/services/moss_retriever.py`) is the
semantic-search abstraction. In the MVP it ships with two backends:

1. **Provider embeddings** (`EMBEDDING_PROVIDER=openai|gemini`) +
   in-memory cosine similarity.
2. **Pure-Python TF-IDF** — dependency-free fallback so demos run
   offline.

Both implement the same `build(creators)` / `search(query, top_k)`
interface, so swapping in a real vector DB (Pinecone, Chroma, Weaviate)
means editing only that one file.

## Cost control (cache)

To protect OpenAI credits, the backend now caches:

- **Embedding cache** keyed by provider + model + text hash
- **Search-response cache** keyed by provider + query + top_k (TTL-based)

Default cache backend is SQLite (`./data/cache.db`) so it persists across restarts.

## Demo mode (no API key)

Leave `OPENAI_API_KEY` and `GEMINI_API_KEY` blank and the app still runs end-to-end:

- **parse agent** → regex/keyword heuristics
- **retrieval**  → TF-IDF cosine similarity
- **insights**   → deterministic template summary

The hybrid scoring formula and the UI behave identically.

## Extending

- **Swap the retriever** — replace `MossRetriever` internals with your
  vector DB of choice.
- **Add an agent** — drop a new step into `services/orchestrator.py`
  (the pipeline uses `RunnableLambda`, so new stages are one line).
- **Personalise brand profiles** — extend `ParsedQuery` with brand
  context and wire it into the reranker.
