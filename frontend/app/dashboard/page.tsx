import { getStats } from "@/lib/api";

export const dynamic = "force-dynamic";

function Bars({
  data,
  format,
  label,
}: {
  data: { label: string; value: number }[];
  format: (v: number) => string;
  label: string;
}) {
  const max = data.length > 0 ? Math.max(...data.map((d) => d.value)) : 0;
  const height = data.length * 26 + 10;
  return (
    <div className="chart-scroll">
      <svg
        viewBox={`0 0 600 ${height}`}
        width={600}
        style={{ maxWidth: "100%", height: "auto" }}
        role="img"
        aria-label={label}
      >
        <title>{label}</title>
        {data.map((d, i) => {
          const y = 10 + i * 26;
          const w = max > 0 ? (d.value / max) * 380 : 0;
          return (
            <g key={d.label}>
              <text x={0} y={y + 12} fontSize={12}>
                {d.label}
              </text>
              <rect x={150} y={y} width={w} height={16} fill="#0b5fff" />
              <text x={150 + w + 6} y={y + 12} fontSize={12}>
                {format(d.value)}
              </text>
            </g>
          );
        })}
      </svg>
    </div>
  );
}

export default async function DashboardPage() {
  let stats: Awaited<ReturnType<typeof getStats>>;
  try {
    stats = await getStats();
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(
      `Could not load stats (${msg}). Is FastAPI running on :8000?`
    );
  }

  const runsPerDay = (
    stats.runs_per_day as { date: string; count: number }[]
  )
    .filter((d) => d.count > 0)
    .map((d) => ({ label: d.date.slice(5), value: d.count }));

  const successByAgent = Object.entries(
    stats.success_by_agent as Record<string, number | null>
  ).map(([agent, rate]) => ({ label: agent, value: rate ?? 0 }));

  const costByAgent = Object.entries(stats.cost_by_agent).map(
    ([agent, cost]) => ({ label: agent, value: cost })
  );

  return (
    <div>
      <h1>Dashboard</h1>
      <div className="stat-grid">
        <div className="stat">
          <div>total runs</div>
          <div>{stats.total}</div>
        </div>
        <div className="stat">
          <div>success (excl. running)</div>
          <div>{(stats.success_rate * 100).toFixed(1)}%</div>
        </div>
        <div className="stat">
          <div>median ms</div>
          <div>
            {stats.median_duration_ms == null
              ? "—"
              : `${stats.median_duration_ms} ms`}
          </div>
        </div>
        <div className="stat">
          <div>p95 ms</div>
          <div>
            {stats.p95_duration_ms == null
              ? "—"
              : `${stats.p95_duration_ms} ms`}
          </div>
        </div>
      </div>
      <p>
        Total cost ${stats.total_cost.toFixed(2)} — excludes{" "}
        {stats.unpriced_count} unpriced runs.
      </p>
      <h2>Runs per day</h2>
      <Bars data={runsPerDay} format={(v) => `${v}`} label="Runs per day" />
      <h2>Success rate by agent</h2>
      <Bars
        data={successByAgent}
        format={(v) => `${(v * 100).toFixed(1)}%`}
        label="Success rate by agent"
      />
      <h2>Cost by agent</h2>
      <Bars data={costByAgent} format={(v) => `$${v.toFixed(2)}`} label="Cost by agent" />
      <h2>Data quality</h2>
      <ul>
        {((stats.meta as { duplicate_ids?: string[] }).duplicate_ids ?? []).length > 0 && (
          <li>
            Duplicate {((stats.meta as { duplicate_ids?: string[] }).duplicate_ids ?? []).length === 1 ? "id" : "ids"}{" "}
            {((stats.meta as { duplicate_ids?: string[] }).duplicate_ids ?? []).join(", ")}: kept the last record, see API meta.
          </li>
        )}
        {((stats.meta as { excluded_negative?: string[] }).excluded_negative ?? []).length > 0 && (
          <li>
            {((stats.meta as { excluded_negative?: string[] }).excluded_negative ?? []).join(", ")} has a negative duration: kept as-is,
            excluded from median/p95.
          </li>
        )}
        {stats.unpriced_count > 0 && (
          <li>{stats.unpriced_count} unpriced runs excluded from cost totals.</li>
        )}
      </ul>
    </div>
  );
}
