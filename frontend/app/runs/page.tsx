import Link from "next/link";
import { getRuns } from "@/lib/api";
import { buildRunsQuery, pageLabel } from "@/lib/query";

const STATUSES = ["succeeded", "failed", "cancelled", "running"];
const AGENTS = ["email-drafter", "contract-reviewer", "support-router", "kpi-analyst", "invoice-extractor"];

type SP = { [k: string]: string | string[] | undefined };
const asArray = (v: string | string[] | undefined): string[] =>
  v === undefined ? [] : Array.isArray(v) ? v : [v];

export default async function RunsPage({ searchParams }: { searchParams: Promise<SP> }) {
  const sp = await searchParams;
  const status = asArray(sp.status);
  const agent = asArray(sp.agent);
  const q = typeof sp.q === "string" ? sp.q : "";
  const started_from = typeof sp.started_from === "string" ? sp.started_from : "";
  const started_to = typeof sp.started_to === "string" ? sp.started_to : "";
  const SORTS = ["started_at", "duration_ms", "cost_usd"];
  const ORDERS = ["asc", "desc"];
  const sortParam = typeof sp.sort === "string" ? sp.sort : "started_at";
  const orderParam = typeof sp.order === "string" ? sp.order : "desc";
  const sort = SORTS.includes(sortParam) ? sortParam : "started_at";
  const order = ORDERS.includes(orderParam) ? orderParam : "desc";
  const page = Math.max(1, parseInt(typeof sp.page === "string" ? sp.page : "1", 10) || 1);
  const query = buildRunsQuery({ status, agent, started_from, started_to, q, sort, order, page: String(page) });
  let body: Awaited<ReturnType<typeof getRuns>>;
  try {
    body = await getRuns(query);
  } catch {
    throw new Error("Could not reach the backend. Is FastAPI running on :8000?");
  }
  const pageSize = body.page_size;
  const mkHref = (p: number) => `/runs?${buildRunsQuery({ status, agent, started_from, started_to, q, sort, order, page: String(p) })}`;
  return (
    <div>
      <h1>Runs</h1>
      <form className="filters" method="get" action="/runs">
        <fieldset>
          <legend>Status</legend>
          {STATUSES.map((s) => (
            <label key={s}><input type="checkbox" name="status" value={s} defaultChecked={status.includes(s)} /> {s}</label>
          ))}
        </fieldset>
        <fieldset>
          <legend>Agent</legend>
          {AGENTS.map((a) => (
            <label key={a}><input type="checkbox" name="agent" value={a} defaultChecked={agent.includes(a)} /> {a}</label>
          ))}
        </fieldset>
        <label>Search <input type="search" name="q" defaultValue={q} placeholder="prompt text" /></label>
        <label>From <input type="date" name="started_from" defaultValue={started_from} /></label>
        <label>To <input type="date" name="started_to" defaultValue={started_to} /></label>
        <label>Sort <select name="sort" defaultValue={sort}>
          <option value="started_at">started_at</option>
          <option value="duration_ms">duration_ms</option>
          <option value="cost_usd">cost_usd</option>
        </select></label>
        <label>Order <select name="order" defaultValue={order}>
          <option value="desc">desc</option>
          <option value="asc">asc</option>
        </select></label>
        <button type="submit">Apply</button>
      </form>
      <p>{pageLabel(page, pageSize, body.total)}</p>
      {body.items.length === 0 ? (
        <p>No runs match these filters. Try clearing the search.</p>
      ) : (
        <>
          <div className="table-scroll">
          <table className="runs">
            <thead><tr><th>ID</th><th>Agent</th><th>Status</th><th>Started</th><th>Duration</th><th>Cost</th></tr></thead>
            <tbody>
              {body.items.map((r) => (
                <tr key={r.id}>
                  <td><Link href={`/runs/${r.id}`}>{r.id}</Link></td>
                  <td>{r.agent}</td><td><span className={`pill pill-${r.status}`}>{r.status}</span></td><td>{r.started_at}</td>
                  <td>{r.duration_ms ?? "—"}</td><td>{r.cost_usd ?? "unpriced"}</td>
                </tr>
              ))}
            </tbody>
          </table>
          </div>
          <div className="cards">
            {body.items.map((r) => (
              <div className="card" key={r.id}>
                <Link href={`/runs/${r.id}`}>{r.id}</Link>
                <p>{r.agent} · <span className={`pill pill-${r.status}`}>{r.status}</span></p>
                <p>{r.started_at} · {r.duration_ms ?? "—"}ms · {r.cost_usd ?? "unpriced"}</p>
              </div>
            ))}
          </div>
          <nav aria-label="Runs pagination" className="pager">
            {page > 1 && <Link href={mkHref(page - 1)}>← Prev</Link>}
            {Array.from({ length: Math.ceil(body.total / pageSize) }, (_, i) => i + 1).map((p) =>
              p === page ? (
                <span key={p} aria-current="page" className="page-current">{p}</span>
              ) : (
                <Link key={p} href={mkHref(p)}>{p}</Link>
              )
            )}
            {(page * pageSize < body.total) && <Link href={mkHref(page + 1)}>Next →</Link>}
          </nav>
        </>
      )}
    </div>
  );
}
