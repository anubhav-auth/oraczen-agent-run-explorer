"use client";

import { useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ExplainButton({ runId }: { runId: string }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  async function handleClick() {
    setBusy(true);
    setErr(null);
    setText("");
    try {
      const res = await fetch(`${API_URL}/api/runs/${runId}/explain`, {
        method: "POST",
      });
      if (!res.ok || !res.body) {
        throw new Error(`explain failed: ${res.status}`);
      }
      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setText((prev) => prev + chunk);
      }
    } catch (e) {
      setErr(e instanceof Error ? e.message : "Explain failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <button onClick={handleClick} disabled={busy}>
        {busy ? "Explaining…" : "Explain this run"}
      </button>
      {text ? <pre aria-live="polite">{text}</pre> : null}
      {err ? <div role="alert">{err}</div> : null}
    </div>
  );
}
