"use client";
export default function DashboardError({ error, reset }: { error: Error; reset: () => void }) {
  return (
    <div>
      <p role="alert">Something went wrong: {error.message}</p>
      <button onClick={reset}>Retry</button>
    </div>
  );
}
