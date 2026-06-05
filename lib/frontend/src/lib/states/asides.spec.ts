import { beforeEach, describe, expect, it } from "vitest";
import { asides } from "./asides.svelte";

describe("Asides", () => {
  beforeEach(() => {
    asides.leftToggle(true);
    asides.rightToggle(true);
    asides.saveState();
  });

  it("restore() reopens both panels after a Zen-style hide when both were already closed", () => {
    asides.leftToggle(false);
    asides.rightToggle(false);

    asides.hideAll();
    asides.restore();

    expect(asides.leftOpen).toBe(true);
    expect(asides.rightOpen).toBe(true);
  });

  it("restore() still respects partially open saved state", () => {
    asides.leftToggle(false);
    asides.rightToggle(true);

    asides.hideAll();
    asides.restore();

    expect(asides.leftOpen).toBe(false);
    expect(asides.rightOpen).toBe(true);
  });
});
