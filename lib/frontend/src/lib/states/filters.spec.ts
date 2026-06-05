import { describe, it, expect, beforeEach } from "vitest";
import { filters } from "./filters.svelte";

describe("FilterState", () => {
  beforeEach(() => {
    filters.reset();
  });

  it("reset() clears all filter params", () => {
    filters.setParam("hasDocumentation", "doc-1");
    filters.setParam("isPartOf", "group-a");
    expect(filters.getParam("hasDocumentation")).toBe("doc-1");
    filters.reset();
    expect(filters.getParam("hasDocumentation")).toBe("");
    expect(filters.getParam("isPartOf")).toBe("");
  });

  it('reset() leaves schemaField at "description" by default', () => {
    filters.reset();
    expect(filters.getParam("schemaField")).toBe("description");
  });

  it("reset() respects the except list", () => {
    filters.setParam("hasDocumentation", "doc-1");
    filters.reset(["hasDocumentation"]);
    expect(filters.getParam("hasDocumentation")).toBe("doc-1");
  });

  it("setParam() only writes known params", () => {
    filters.setParam("not-a-real-param", "value");
    expect(filters.getParam("not-a-real-param")).toBeNull();
  });

  it("getAllParamValues() returns each tracked field", () => {
    filters.setParam("hasDocumentation", "doc-1");
    const values = filters.getAllParamValues();
    expect(values.hasDocumentation).toBe("doc-1");
    expect(Object.keys(values)).toContain("searchText");
  });
});
