import type { RankedCreator } from "@/lib/types";

interface Props {
  results: RankedCreator[];
}

export function ResultsTable({ results }: Props) {
  if (!results.length) {
    return (
      <div className="rounded-2xl border border-ink-200 bg-canvas-card p-6 text-center text-sm text-ink-500">
        No creators matched this brief.
      </div>
    );
  }

  return (
    <div className="overflow-hidden rounded-2xl border border-ink-200 bg-canvas-card shadow-card">
        <table className="w-full table-fixed border-collapse text-sm">
          <thead className="border-b border-ink-200 bg-canvas text-left text-[11px] uppercase tracking-[0.14em] text-ink-500">
            <tr>
              <th className="w-8 px-2 py-3">#</th>
              <th className="w-[26%] px-3 py-3">Creator</th>
              <th className="w-[16%] px-2 py-3">Niche</th>
              <th className="w-[14%] px-2 py-3 text-right">Semantic</th>
              <th className="w-[14%] px-2 py-3 text-right">Projected</th>
              <th className="w-[16%] px-2 py-3 text-right">Demographic</th>
              <th className="w-[10%] px-2 py-3 text-right">Final</th>
            </tr>
          </thead>
          <tbody>
            {results.map((r, i) => (
              <tr
                key={r.username}
                className="border-t border-ink-100 transition hover:bg-canvas"
              >
                <td className="px-2 py-3 text-ink-400">{i + 1}</td>
                <td className="px-3 py-3">
                  <div className="truncate font-medium text-ink-900">@{r.username}</div>
                  <div className="mt-0.5 truncate text-xs text-ink-500">
                    {r.bio}
                  </div>
                </td>
                <td className="px-2 py-3">
                  <div className="flex flex-wrap gap-1">
                    {r.content_style_tags.slice(0, 2).map((t) => (
                      <span
                        key={t}
                        className="max-w-full truncate rounded-full border border-ink-200 bg-canvas px-2 py-0.5 text-[10px] text-ink-700"
                      >
                        {t}
                      </span>
                    ))}
                    {r.content_style_tags.length > 2 ? (
                      <span className="text-xs text-ink-400">
                        +{r.content_style_tags.length - 2}
                      </span>
                    ) : null}
                  </div>
                </td>
                <ScoreCell value={r.scores.semantic_score} />
                <ScoreCell value={r.scores.projected_score} />
                <ScoreCell value={r.scores.demographic_bonus} />
                <td className="px-2 py-3 text-right font-semibold text-ink-900">
                  {r.scores.final_score.toFixed(3)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
    </div>
  );
}

function ScoreCell({ value }: { value: number }) {
  const pct = Math.max(0, Math.min(1, value));
  return (
    <td className="px-2 py-3 text-right font-mono text-[11px]">
      <div className="flex flex-col items-end gap-1">
        <span className="text-ink-900">{value.toFixed(3)}</span>
        <span className="block h-1 w-14 rounded-full bg-ink-100" aria-hidden>
          <span
            className="block h-1 rounded-full bg-ink-900"
            style={{ width: `${pct * 100}%` }}
          />
        </span>
      </div>
    </td>
  );
}
