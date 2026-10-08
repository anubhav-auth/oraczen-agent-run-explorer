import { describe, expect, it, vi, afterEach } from "vitest";
import { buildRunsQuery, pageLabel } from "./query";
import { getStats } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
});
describe("buildRunsQuery", () => {
  it("repeats multi-value params and drops empties", () => {
    const q = buildRunsQuery({ status: ["succeeded", "failed"], agent: ["email-drafter"], tool: ["llm", "sql"], q: "  ", sort: "duration_ms", order: "asc", page: "2" });
    expect(q).toContain("status=succeeded");
    expect(q).toContain("status=failed");
    expect(q).toContain("agent=email-drafter");
    expect(q).toContain("tool=llm");
    expect(q).toContain("tool=sql");
    expect(q).not.toContain("q=");
    expect(q).toContain("sort=duration_ms");
  });
});
describe("pageLabel", () => {
  it("renders showing X-Y of Z", () => {
    expect(pageLabel(1, 25, 200)).toBe("showing 1–25 of 200");
    expect(pageLabel(8, 25, 200)).toBe("showing 176–200 of 200");
  });
});
describe("transient fetch failures", () => {
  it("retries network errors then succeeds", async () => {
    const ok = { ok: true, json: async () => ({ total: 200 }) } as Response;
    const stub = vi
      .fn()
      .mockRejectedValueOnce(new TypeError("fetch failed"))
      .mockRejectedValueOnce(new TypeError("fetch failed"))
      .mockResolvedValueOnce(ok);
    vi.stubGlobal("fetch", stub);
    await expect(getStats()).resolves.toEqual({ total: 200 });
    expect(stub).toHaveBeenCalledTimes(3);
  });
  it("does not retry HTTP error statuses", async () => {
    const bad = { ok: false, status: 500 } as Response;
    const stub = vi.fn().mockResolvedValueOnce(bad);
    vi.stubGlobal("fetch", stub);
    await expect(getStats()).rejects.toThrow("failed to fetch stats: 500");
    expect(stub).toHaveBeenCalledTimes(1);
  });
});
