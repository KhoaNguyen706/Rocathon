interface Props {
  insights: string;
}

export function InsightsPanel({ insights }: Props) {
  return (
    <div className="rounded-2xl border border-ink-200 bg-canvas-card p-5 shadow-card">
      <div className="mb-3 flex items-center gap-2">
        <span className="inline-block h-2 w-2 rounded-full bg-accent-pink" />
        <h3 className="text-sm font-medium text-ink-900">Insights</h3>
      </div>
      <p className="whitespace-pre-line text-sm leading-relaxed text-ink-700">
        {insights}
      </p>
    </div>
  );
}
