"use client";

import { useEffect, useRef, useState } from "react";

const STEPS = [
  {
    key: "parse",
    label: "Reading your brief",
    hint: "Gemini parses category, audience, tone & niche.",
  },
  {
    key: "moss",
    label: "Moss retrieval",
    hint: "Semantic search over 1,000 creator documents.",
  },
  {
    key: "rank",
    label: "Hybrid ranking",
    hint: "Blend semantic · projected · demographic scores.",
  },
  {
    key: "insights",
    label: "Generating insights",
    hint: "Gemini summarises the top matches for your brief.",
  },
] as const;

interface Props {
  /** Whether the backend request is still in flight. */
  loading: boolean;
  /** Fires when the finished-state animation completes. */
  onDone?: () => void;
}

/**
 * Visible pipeline progress UI.
 *
 * The backend is fast (often <1s), so we pace the steps client-side with a
 * minimum visible duration per stage. If the request finishes early we
 * accelerate the remaining steps rather than stalling; if it takes longer,
 * we hold on the last step until the response lands.
 */
export function PipelineLoader({ loading, onDone }: Props) {
  const [current, setCurrent] = useState(0);
  const [finished, setFinished] = useState(false);
  const startedRef = useRef(false);
  const onDoneRef = useRef(onDone);
  onDoneRef.current = onDone;

  // Advance through the first N-1 steps at a steady human-readable pace.
  useEffect(() => {
    if (!loading) return;
    startedRef.current = true;
    setFinished(false);
    setCurrent(0);

    let i = 0;
    const id = window.setInterval(() => {
      i += 1;
      if (i >= STEPS.length - 1) {
        setCurrent(STEPS.length - 1);
        window.clearInterval(id);
      } else {
        setCurrent(i);
      }
    }, 520);

    return () => window.clearInterval(id);
  }, [loading]);

  // When the request completes, run a brief "done" flourish before hiding.
  // Minimum perceptible run-time so the animation is visible even if the
  // backend replied in <100ms. Total minimum: ~1.0s.
  useEffect(() => {
    if (loading) return;
    if (!startedRef.current) return;
    const timers: number[] = [];
    timers.push(
      window.setTimeout(() => {
        setCurrent(STEPS.length);
        setFinished(true);
        timers.push(
          window.setTimeout(() => onDoneRef.current?.(), 420),
        );
      }, 600),
    );
    return () => timers.forEach((t) => window.clearTimeout(t));
  }, [loading]);

  return (
    <div className="rounded-2xl border border-ink-200 bg-canvas-card p-6 shadow-card">
      <div className="mb-5 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <LiveDot />
          <span className="text-xs uppercase tracking-[0.2em] text-ink-500">
            Moss agent
          </span>
        </div>
        <span className="text-xs text-ink-500">
          {finished ? "Complete" : "Working…"}
        </span>
      </div>

      <div className="flex items-center justify-center py-4">
        <HeroBlob running={!finished} />
      </div>

      <ol className="mt-4 space-y-3">
        {STEPS.map((step, idx) => {
          const state: "done" | "active" | "pending" =
            idx < current ? "done" : idx === current ? "active" : "pending";
          return (
            <li key={step.key} className="flex items-start gap-3">
              <StepDot state={state} index={idx} />
              <div className="flex-1">
                <div
                  className={
                    "flex items-center justify-between text-sm " +
                    (state === "pending"
                      ? "text-ink-400"
                      : "text-ink-900")
                  }
                >
                  <span className="font-medium">{step.label}</span>
                  {state === "active" ? (
                    <span className="text-xs text-ink-500">in progress</span>
                  ) : state === "done" ? (
                    <span className="text-xs text-ink-500">done</span>
                  ) : null}
                </div>
                <div className="mt-0.5 text-xs text-ink-500">{step.hint}</div>
                {state === "active" ? (
                  <div className="mt-2 h-[3px] w-full overflow-hidden rounded-full bg-ink-100">
                    <div className="shimmer h-full w-full rounded-full" />
                  </div>
                ) : null}
              </div>
            </li>
          );
        })}
      </ol>
    </div>
  );
}

function StepDot({
  state,
  index,
}: {
  state: "done" | "active" | "pending";
  index: number;
}) {
  if (state === "done") {
    return (
      <span className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full bg-ink-900 text-[11px] text-white">
        <svg viewBox="0 0 20 20" className="h-3.5 w-3.5" fill="none">
          <path
            d="M4 10.5l4 4 8-9"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
    );
  }
  if (state === "active") {
    return (
      <span className="relative mt-0.5 flex h-6 w-6 items-center justify-center rounded-full border border-ink-900 text-[11px] text-ink-900">
        <span className="absolute inset-0 animate-ping rounded-full bg-ink-900/10" />
        {index + 1}
      </span>
    );
  }
  return (
    <span className="mt-0.5 flex h-6 w-6 items-center justify-center rounded-full border border-ink-200 text-[11px] text-ink-400">
      {index + 1}
    </span>
  );
}

function LiveDot() {
  return (
    <span className="relative flex h-2 w-2">
      <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-accent-green opacity-60" />
      <span className="relative inline-flex h-2 w-2 rounded-full bg-accent-green" />
    </span>
  );
}

export function HeroBlob({ running = true }: { running?: boolean }) {
  return (
    <div className="relative flex h-32 w-32 items-center justify-center">
      <div
        className={
          "absolute inset-0 rounded-full bg-accent-pink blur-2xl " +
          (running ? "animate-blob" : "opacity-70")
        }
      />
      <div
        className={
          "absolute inset-4 rounded-full bg-accent-lime/60 blur-xl " +
          (running ? "animate-blob" : "")
        }
        style={{ animationDelay: "-2s" }}
      />
      <div className="relative h-16 w-16 rounded-full bg-gradient-to-br from-accent-pink to-accent-lime/70 shadow-inner" />
    </div>
  );
}
