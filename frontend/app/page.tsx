"use client";

import { useState } from "react";

import { PipelineLoader } from "@/components/PipelineLoader";
import { InsightsPanel } from "@/components/InsightsPanel";
import { ParsedQueryCard } from "@/components/ParsedQueryCard";
import { ResultsTable } from "@/components/ResultsTable";
import { SearchForm } from "@/components/SearchForm";
import { searchCreators } from "@/lib/api";
import type { SearchResponse } from "@/lib/types";

export default function HomePage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<SearchResponse | null>(null);
  const [showLoader, setShowLoader] = useState(false);

  const handleSearch = async (query: string) => {
    setLoading(true);
    setError(null);
    setShowLoader(true);
    setData(null);
    try {
      const res = await searchCreators(query, 10);
      setData(res);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setData(null);
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto min-h-screen max-w-6xl px-6 pb-16 pt-10 sm:pt-12">
      <header className="mb-8 rounded-2xl border border-ink-200 bg-canvas-card p-6 shadow-soft">
        <div className="mb-4 inline-flex items-center gap-2 rounded-full border border-ink-200 bg-canvas px-3 py-1 text-xs text-ink-700">
          <span className="inline-block h-1.5 w-1.5 rounded-full bg-accent-green" />
          Creator Discovery Copilot
        </div>
        <h1 className="font-serif text-4xl leading-tight tracking-tight text-ink-900 sm:text-5xl">
          Find the right creators in plain English
        </h1>
        <p className="mt-3 max-w-3xl text-sm text-ink-700 sm:text-base">
          Describe your campaign and we will parse the brief, run Moss semantic
          retrieval over 1,000 creators, and return ranked matches with Gemini
          insights.
        </p>
        <div className="mt-6">
          <SearchForm onSubmit={handleSearch} loading={loading} />
        </div>
      </header>

      <section>
          {showLoader ? (
            <PipelineLoader
              loading={loading}
              onDone={() => setShowLoader(false)}
            />
          ) : null}

          {error && !showLoader ? (
            <div className="mt-6 rounded-2xl border border-red-300 bg-red-50 p-4 text-sm text-red-700">
              {error}
            </div>
          ) : null}

          {data && !showLoader ? <Results data={data} /> : null}

          {!data && !showLoader && !error ? <EmptyState /> : null}
      </section>

    </main>
  );
}

function Results({ data }: { data: SearchResponse }) {
  return (
    <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
      <div className="xl:col-span-1">
        <div className="space-y-6">
          <ParsedQueryCard parsed={data.parsed_query} />
          <InsightsPanel insights={data.insights} />
        </div>
      </div>
      <div className="xl:col-span-2">
        <div className="mb-3">
          <h2 className="text-[11px] uppercase tracking-[0.2em] text-ink-500">
            Top {data.results.length} creators
          </h2>
        </div>
        <ResultsTable results={data.results} />
      </div>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-2xl border border-dashed border-ink-200 bg-canvas-card p-10 text-center shadow-soft">
      <p className="font-serif text-2xl text-ink-900">
        Describe your campaign above.
      </p>
      <p className="mt-2 text-sm text-ink-500">
        Results appear here — parsed brief, top 10 ranked creators, and an
        AI-generated insights summary.
      </p>
    </div>
  );
}

