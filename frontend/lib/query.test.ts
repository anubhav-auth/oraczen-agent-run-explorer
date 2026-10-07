import { describe, expect, it } from "vitest";
import { buildRunsQuery, pageLabel } from "./query";
describe("buildRunsQuery", () => {
  it("repeats multi-value params and drops empties", () => {
    const q = buildRunsQuery({ status: ["succeeded", "failed"], agent: ["email-drafter"], q: "  ", sort: "duration_ms", order: "asc", page: "2" });
    expect(q).toContain("status=succeeded");
    expect(q).toContain("status=failed");
    expect(q).toContain("agent=email-drafter");
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
