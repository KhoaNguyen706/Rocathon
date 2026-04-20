import type { ParsedQuery } from "@/lib/types";

interface Props {
  parsed: ParsedQuery;
}

export function ParsedQueryCard({ parsed }: Props) {
  return (
    <div className="rounded-2xl border border-ink-200 bg-canvas-card p-5 shadow-card">
      <div className="mb-4 flex items-center">
        <h3 className="text-sm font-medium text-ink-900">Parsed brief</h3>
      </div>

      <dl className="space-y-3 text-sm">
        <Row label="Category" value={parsed.category ?? "—"} />
        <Row label="Gender" value={parsed.gender ?? "ANY"} />
        <Row
          label="Audience age"
          value={
            parsed.audience_age.length ? parsed.audience_age.join(", ") : "—"
          }
        />
        <Row
          label="Niche"
          value={
            parsed.niche.length ? (
              <div className="flex flex-wrap gap-1">
                {parsed.niche.map((n) => (
                  <Pill key={n}>{n}</Pill>
                ))}
              </div>
            ) : (
              "—"
            )
          }
        />
        <Row
          label="Keywords"
          value={
            parsed.keywords.length ? (
              <div className="flex flex-wrap gap-1">
                {parsed.keywords.map((k) => (
                  <Pill key={k} muted>
                    {k}
                  </Pill>
                ))}
              </div>
            ) : (
              "—"
            )
          }
        />
      </dl>
    </div>
  );
}

function Row({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div className="rounded-xl border border-ink-100 bg-canvas p-3">
      <dt className="mb-1 text-[11px] uppercase tracking-[0.14em] text-ink-500">
        {label}
      </dt>
      <dd className="text-sm leading-6 text-ink-900">{value}</dd>
    </div>
  );
}

function Pill({
  children,
  muted = false,
}: {
  children: React.ReactNode;
  muted?: boolean;
}) {
  return (
    <span
      className={
        muted
          ? "rounded-full border border-ink-200 bg-canvas px-2 py-0.5 text-xs text-ink-700"
          : "rounded-full bg-ink-900 px-2 py-0.5 text-xs text-white"
      }
    >
      {children}
    </span>
  );
}
