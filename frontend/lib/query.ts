export type RunsFilter = {
  status?: string[];
  agent?: string[];
  started_from?: string;
  started_to?: string;
  q?: string;
  sort?: string;
  order?: string;
  page?: string;
};

export function buildRunsQuery(filters: RunsFilter): string {
  const params = new URLSearchParams();
  for (const s of filters.status ?? []) {
    if (s) params.append("status", s);
  }
  for (const a of filters.agent ?? []) {
    if (a) params.append("agent", a);
  }
  if (filters.started_from) params.set("started_from", filters.started_from);
  if (filters.started_to) params.set("started_to", filters.started_to);
  if (filters.q?.trim()) params.set("q", filters.q.trim());
  if (filters.sort) params.set("sort", filters.sort);
  if (filters.order) params.set("order", filters.order);
  if (filters.page) params.set("page", filters.page);
  return params.toString();
}

export function pageLabel(page: number, pageSize: number, total: number): string {
  if (total === 0) return "showing 0 of 0";
  const from = (page - 1) * pageSize + 1;
  const to = Math.min(page * pageSize, total);
  return `showing ${from}–${to} of ${total}`;
}
