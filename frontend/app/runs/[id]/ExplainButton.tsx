"use client";

import { useEffect, useRef, useState } from "react";

const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ExplainButton({ runId }: { runId: string }) {
  const [text, setText] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);
  const ctrlRef = useRef<AbortController | null>(null);
  const readerRef = useRef<ReadableStreamDefaultReader<Uint8Array> | null>(null);

  useEffect(() => {
    return () => {
      ctrlRef.current?.abort();
      readerRef.current?.cancel().catch(() => {});
    };
  }, []);

  async function handleClick() {
    setBusy(true);
    setErr(null);
    setText("");
    const ctrl = new AbortController();
    ctrlRef.current = ctrl;
    try {
      const res = await fetch(`${API_URL}/api/runs/${runId}/explain`, {
        method: "POST",
        signal: ctrl.signal,
      });
      if (!res.ok || !res.body) {
        throw new Error(`explain failed: ${res.status}`);
      }
      const reader = res.body.getReader();
      readerRef.current = reader;
      const decoder = new TextDecoder();
      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        const chunk = decoder.decode(value, { stream: true });
        setText((prev) => prev + chunk);
      }
      setText((prev) => prev + decoder.decode());
    } catch (e) {
      if (e instanceof DOMException && e.name === "AbortError") return;
      if (ctrl.signal.aborted) return;
      setErr(e instanceof Error ? e.message : "Explain failed");
    } finally {
      if (!ctrl.signal.aborted) setBusy(false);
    }
  }

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={busy}
        aria-busy={busy}
        aria-controls="explain-output"
      >
        {busy ? "Explaining…" : "Explain this run"}
      </button>
      {text ? (
        <pre id="explain-output" aria-live="polite">
          {text}
        </pre>
      ) : null}
      {err ? <div role="alert">{err}</div> : null}
    </div>
  );
}
