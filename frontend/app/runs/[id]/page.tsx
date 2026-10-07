import Link from "next/link";
import { notFound } from "next/navigation";
import { getRun, NotFoundError } from "../../../lib/api";
import ExplainButton from "./ExplainButton";
import StepsList from "./StepsList";

export const dynamic = "force-dynamic";

export default async function RunDetailPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;

  let run: Awaited<ReturnType<typeof getRun>>;
  try {
    run = await getRun(id);
  } catch (e) {
    if (e instanceof NotFoundError) notFound();
    const msg = e instanceof Error ? e.message : String(e);
    throw new Error(`Could not load run (${msg}). Is FastAPI running on :8000?`);
  }

    const runError = run.error as {
      type?: unknown;
      message?: unknown;
      step_index?: unknown;
    } | null;

    return (
      <div>
        <Link href="/runs">Back to runs</Link>
        <h1>{run.id}</h1>

        <dl className="meta">
          <dt>Agent</dt>
          <dd>
            {run.agent} / {run.model}
          </dd>
          <dt>Status</dt>
          <dd>{run.status}</dd>
          <dt>Started</dt>
          <dd>{run.started_at}</dd>
          <dt>Duration</dt>
          <dd>{run.duration_ms ?? "—"} ms</dd>
          <dt>Tokens</dt>
          <dd>
            {run.input_tokens} in / {run.output_tokens} out
          </dd>
          <dt>Cost</dt>
          <dd>{run.cost_usd ?? "unpriced"}</dd>
          <dt>Prompt</dt>
          <dd>
            <pre>{run.prompt}</pre>
          </dd>
        </dl>

        {run.error && runError ? (
          <div role="alert" className="error">
            <div>Type: {String(runError.type ?? "unknown")}</div>
            <div>Message: {String(runError.message ?? "")}</div>
            <div>Step: {String(runError.step_index ?? "")}</div>
          </div>
        ) : null}

        <ExplainButton runId={run.id} />

        <h2>Steps ({run.steps.length})</h2>
        {run.steps.length === 0 ? (
          <p>This run has no steps.</p>
        ) : (
          <StepsList steps={run.steps} />
        )}
      </div>
    );
}
