"use client";
export default function RunsError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <p>Something went wrong: {error.message}</p>
      <button onClick={reset}>Retry</button>
    </div>
  );
}
