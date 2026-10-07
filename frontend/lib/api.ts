export interface TokenUsage {
  input: number;
  output: number;
}

export interface Step {
  index: number;
  name: string;
  tool: string;
  status: string;
  started_at: string;
  duration_ms: number | null;
  input: string;
  output: string | null;
  tokens: TokenUsage;
}

export interface RunSummary {
  id: string;
  agent: string;
  model: string;
  status: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number | null;
  input_tokens: number;
  output_tokens: number;
  cost_usd: number | null;
  prompt: string;
  error: Record<string, unknown> | null;
  tenant_id: string;
}

export interface RunDetail extends RunSummary {
  steps: Step[];
}

export interface RunsPage {
  items: RunSummary[];
  total: number;
  page: number;
  page_size: number;
}

export interface Stats {
  total: number;
  by_status: Record<string, number>;
  by_agent: Record<string, number>;
  success_rate: number;
  success_by_agent: Record<string, number>;
  median_duration_ms: number | null;
  p95_duration_ms: number | null;
  total_cost: number;
  cost_by_agent: Record<string, number>;
  unpriced_count: number;
  unpriced_by_agent: Record<string, number>;
  runs_per_day: unknown[];
  meta: Record<string, unknown>;
}

export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? process.env.API_URL ?? "http://localhost:8000";

export async function getRuns(query: string): Promise<RunsPage> {
  const qs = query ? (query.startsWith("?") ? query : `?${query}`) : "";
  const res = await fetch(`${API_URL}/api/runs${qs}`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to fetch runs: ${res.status}`);
  return (await res.json()) as RunsPage;
}

export async function getRun(id: string): Promise<RunDetail> {
  const res = await fetch(`${API_URL}/api/runs/${id}`, { cache: "no-store" });
  if (res.status === 404) throw new Error("run not found");
  if (!res.ok) throw new Error(`failed to fetch run: ${res.status}`);
  return (await res.json()) as RunDetail;
}

export async function getStats(): Promise<Stats> {
  const res = await fetch(`${API_URL}/api/stats`, { cache: "no-store" });
  if (!res.ok) throw new Error(`failed to fetch stats: ${res.status}`);
  return (await res.json()) as Stats;
}
