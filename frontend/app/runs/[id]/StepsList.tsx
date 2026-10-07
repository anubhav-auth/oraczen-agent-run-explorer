"use client";

import { useEffect } from "react";
import type { Step } from "@/lib/api";

export default function StepsList({ steps }: { steps: Step[] }) {
  useEffect(() => {
    const match = window.location.hash.match(/^#step-(\d+)$/);
    if (!match) return;
    const el = document.getElementById(`step-${match[1]}`);
    if (el instanceof HTMLDetailsElement) {
      el.open = true;
      el.scrollIntoView();
    }
  }, []);

  return (
    <>
      {steps.map((step) => (
        <details key={step.index} id={`step-${step.index}`}>
          <summary>
            {step.index}: {step.name} · {step.tool} · {step.status} ·{" "}
            {step.duration_ms ?? "—"}ms · {step.tokens.input}/
            {step.tokens.output} tok
          </summary>
          <div>
            <h3>Input</h3>
            <pre>{step.input}</pre>
            <h3>Output</h3>
            <pre>{step.output ?? "—"}</pre>
          </div>
        </details>
      ))}
    </>
  );
}
