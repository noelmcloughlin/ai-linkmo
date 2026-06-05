import { describe, it, expect, beforeEach } from "vitest";
import { endpoint } from "./endpoint.svelte";
import { DEFAULT_ENDPOINT, ENDPOINTS } from "$lib/constants";

describe("Endpoint", () => {
  beforeEach(() => {
    endpoint.reset();
  });

  it("starts at the default endpoint", () => {
    expect(endpoint.current).toBe(DEFAULT_ENDPOINT);
    expect(endpoint.isLoading).toBe(false);
    expect(endpoint.isCurateMode).toBe(false);
    expect(endpoint.includeByod).toBe(true);
  });

  it("setCurrent() accepts a known endpoint key", () => {
    const known = ENDPOINTS.find((e) => e.key !== DEFAULT_ENDPOINT)?.key;
    if (!known) return; // no other endpoint configured, skip
    endpoint.setCurrent(known);
    expect(endpoint.current).toBe(known);
  });

  it("setCurrent() falls back to default on unknown endpoint", () => {
    endpoint.setCurrent("not-a-real-endpoint");
    expect(endpoint.current).toBe(DEFAULT_ENDPOINT);
  });

  it("setCurrent() is idempotent", () => {
    const before = endpoint.current;
    endpoint.setCurrent(before);
    expect(endpoint.current).toBe(before);
  });

  it("setLoading() updates loading state", () => {
    endpoint.setLoading(true);
    expect(endpoint.isLoading).toBe(true);
    endpoint.setLoading(false);
    expect(endpoint.isLoading).toBe(false);
  });

  it("setCurateMode() updates curate flag", () => {
    endpoint.setCurateMode(true);
    expect(endpoint.isCurateMode).toBe(true);
    endpoint.setCurateMode(false);
    expect(endpoint.isCurateMode).toBe(false);
  });

  it("getLabel() returns a non-empty label for default endpoint", () => {
    expect(endpoint.getLabel()).not.toBe("");
    expect(endpoint.getLabel(true)).toBe(endpoint.getLabel().toLowerCase());
  });
});
