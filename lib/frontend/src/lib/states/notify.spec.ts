import { describe, it, expect, beforeEach } from "vitest";
import { notifyStore } from "./notify.svelte";

// Run inside an effect root so Svelte 5 `$state` works under vitest.
// vitest-browser-svelte provides a wrapper; here we just exercise the public
// methods directly because the class fields with $state work fine in tests
// when accessed inside a `.svelte.ts` module.

describe("NotifyStore", () => {
  beforeEach(() => {
    notifyStore.resetAll();
  });

  it("starts empty", () => {
    expect(notifyStore.getAll()).toEqual([]);
    expect(notifyStore.type).toBe("info");
  });

  it("add() pushes a notification and tracks the latest type", () => {
    notifyStore.add({ id: 1, type: "error", message: "boom" });
    expect(notifyStore.getAll()).toHaveLength(1);
    expect(notifyStore.type).toBe("error");
    expect(notifyStore.message).toBe("boom");
  });

  it("dismiss() removes only the matching id", () => {
    notifyStore.add({ id: 1, type: "info", message: "a" });
    notifyStore.add({ id: 2, type: "success", message: "b" });
    notifyStore.dismiss(1);
    const all = notifyStore.getAll();
    expect(all).toHaveLength(1);
    expect(all[0].id).toBe(2);
  });

  it("resetAll() clears everything", () => {
    notifyStore.add({ id: 1, type: "warning", message: "x" });
    notifyStore.resetAll();
    expect(notifyStore.getAll()).toEqual([]);
    expect(notifyStore.type).toBe("info");
    expect(notifyStore.message).toBe("");
  });
});
