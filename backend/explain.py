from __future__ import annotations
import asyncio
import os
from collections import Counter
def build_explain_text(run) -> str:
    tools = Counter(s.tool for s in run.steps)
    tool_str = ", ".join(f"{t} x{c}" for t, c in sorted(tools.items())) if tools else "no steps"
    base = (f"Run {run.id} used agent {run.agent} ({run.model}) with prompt: {(run.prompt or '').strip()[:160]}. " f"It took {len(run.steps)} steps ({tool_str}), duration {run.duration_ms}ms, " f"tokens in={run.input_tokens} out={run.output_tokens}, cost {run.cost_usd}. ")
    if run.error:
        e = run.error
        tail = f"Status {run.status}: {e.get('type')}: {e.get('message')} at step {e.get('step_index')}. "
        step = next((s for s in run.steps if s.index == e.get('step_index')), None)
        if step is not None:
            tail += f"Failing step used tool {step.tool} ({step.name}). "
        elif not run.steps:
            tail += "The run has no steps, so the error index points past the trace. "
        return base + tail
    return base + f"Status {run.status}. "
class MockExplainProvider:
    async def stream(self, run):
        text = build_explain_text(run)
        delay = int(os.environ.get("EXPLAIN_DELAY_MS", "40")) / 1000
        for sent in [s.strip() for s in text.split(". ") if s.strip()]:
            yield sent + ". "
            await asyncio.sleep(delay)
