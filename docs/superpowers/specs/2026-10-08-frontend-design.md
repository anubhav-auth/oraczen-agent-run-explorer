# Frontend Design — Agent Run Explorer UI

Date: 2026-10-08. Scope: minimal responsive Next.js UI on `feat/frontend`. Backend contract frozen (`backend/app.py`).

## Approach (approved)

Minimal Next.js App Router + TypeScript, server components, plain CSS. No Tailwind, no chart lib, no client state for filters. Essentially semantic HTML rendered by Next.js — satisfies the stack mandate with the least machinery.

## Responsive system (per design-systems guidance)

- Content-first intrinsic layout: fluid container `max-width 1100px`, `clamp()` type scale, flex/grid that wraps without breakpoints where possible.
- One breakpoint at `720px` only where content demands it: runs table → stacked cards; filter fieldset → full-width stack; stat cards grid 4→2→1; charts get horizontal scroll container as fallback (SVG `viewBox` scales otherwise).
- Touch: interactive targets ≥44px, native controls (checkbox, select, date, details/summary) so keyboard/focus/labels come free. `:target` highlight for `#step-N` anchors.
- States: every data surface specifies loading (`loading.tsx` suspense), empty, and error (`error.tsx`) — no blank screens on phone or desktop.

## Pages

1. `/runs` — server component. Reads awaited `searchParams`, builds backend query via `lib/query.ts`, fetches with `cache: 'no-store'`. Native `<form method="get">`: status/agent checkbox groups, `q` text, date range, sort/order selects. GET submit keeps state in URL (Slack-shareable, zero JS). Pagination links preserve params, show "showing X–Y of Z".
2. `/runs/[id]` — server component. Metadata grid, error callout if present, steps as `<details id="step-N">` with duration/tokens in summary, input/output in `<pre>`. One client island: `ExplainButton` POSTs to explain endpoint, appends `ReadableStream` chunks as they arrive.
3. `/dashboard` — server component. Stat cards + 3 hand SVG charts (runs/day bars, success-by-agent bars, cost-by-agent bars) + honest "excludes 3 unpriced" note. Costs from `/api/stats` need no client math.

## Data flow

Server components fetch `API_URL` (env, default `http://localhost:8000`) directly — no Next.js API routes for data (brief forbids). Client island uses `NEXT_PUBLIC_API_URL` for the browser-side explain POST.

## Testing

Vitest unit tests on pure helpers (`buildRunsQuery`, pagination label, chart scaling). Component/e2e skipped with DECISIONS paragraph (brief allows): no backend fixture harness, helpers carry the logic risk.
