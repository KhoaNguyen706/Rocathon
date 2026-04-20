"use client";

import { FormEvent, useState } from "react";

interface Props {
  onSubmit: (query: string) => void;
  loading: boolean;
}

const EXAMPLES = [
  "Luxury anti-aging skincare for women over 40",
  "High-energy fitness content for men 18-34",
  "Affordable smart-home gadgets for college students",
  "Clean-ingredient baby food, moms 25-34",
];

export function SearchForm({ onSubmit, loading }: Props) {
  const [value, setValue] = useState(EXAMPLES[0]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const q = value.trim();
    if (q.length < 3) return;
    onSubmit(q);
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div className="relative">
        <textarea
          id="brief"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          rows={3}
          placeholder="Describe the creators you're looking for…"
          className="w-full resize-y rounded-2xl border border-ink-200 bg-canvas-card px-5 py-4 text-base text-ink-900 placeholder-ink-400 shadow-soft outline-none transition focus:border-ink-900 focus:ring-2 focus:ring-ink-900/10"
        />
      </div>

      <div className="flex flex-wrap items-center gap-3">
        <button
          type="submit"
          disabled={loading}
          className="inline-flex items-center gap-2 rounded-full bg-ink-900 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-ink-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <>
              <Spinner />
              Searching…
            </>
          ) : (
            <>
              Find creators
              <span aria-hidden>→</span>
            </>
          )}
        </button>

        <span className="text-xs uppercase tracking-[0.18em] text-ink-500">
          Try
        </span>
        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              onClick={() => setValue(ex)}
              className="rounded-full border border-ink-200 bg-canvas-card px-3 py-1 text-xs text-ink-700 transition hover:border-ink-900 hover:text-ink-900"
            >
              {truncate(ex, 42)}
            </button>
          ))}
        </div>
      </div>
    </form>
  );
}

function truncate(s: string, n: number) {
  return s.length > n ? s.slice(0, n - 1) + "…" : s;
}

function Spinner() {
  return (
    <svg
      className="h-4 w-4 animate-spin"
      viewBox="0 0 24 24"
      fill="none"
      aria-hidden
    >
      <circle
        className="opacity-25"
        cx="12"
        cy="12"
        r="10"
        stroke="currentColor"
        strokeWidth="4"
      />
      <path
        className="opacity-75"
        fill="currentColor"
        d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
      />
    </svg>
  );
}
