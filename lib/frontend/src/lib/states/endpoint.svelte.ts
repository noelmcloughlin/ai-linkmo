import {  DEFAULT_ENDPOINT, ENDPOINTS } from "$lib/constants";
import {  notify } from "$states/notify.svelte";
import {  filters } from "$states/filters.svelte";

class Endpoint {
  current = $state(DEFAULT_ENDPOINT);
  isLoading = $state(false);
  isCurateMode = $state(false);
  includeByod = $state(true);

  getCurrent() {
    return this.current;
  }

  getIsLoading() {
    return this.isLoading;
  }

  getIsCurateMode() {
    return this.isCurateMode;
  }

  getIncludeByod() {
    return this.includeByod;
  }

  setIncludeByod(value: boolean) {
    if (value !== this.includeByod) {
      this.includeByod = value;
    }
  }

  setCurrent(ep: string) {
    if (this.current === ep) {
      return; // Avoid redundant updates
    }

    if (ENDPOINTS.some((e) => e.key === ep)) {
      this.current = ep;
      // Clear all notifications on endpoint change
      notify.resetAll();
      // Reset filters when switching endpoints to prevent cross-contamination
      filters.reset();
    } else {
      notify.error(`Invalid endpoint: ${ep}, resetting to default.`);
      this.current = DEFAULT_ENDPOINT; // Reset to default if invalid
      filters.reset();
    }
  }

  setLoading(loading: boolean) {
    if (loading !== this.isLoading) {
      this.isLoading = loading;
    }
  }

  setCurateMode(mode: boolean) {
    if (mode !== this.isCurateMode) {
      this.isCurateMode = mode;
    }
  }

  // Reset the endpoint state
  reset() {
    this.current = DEFAULT_ENDPOINT;
    this.isLoading = false;
    this.isCurateMode = false;
    this.includeByod = true; // Reset to default
  }

  getLabel(lowerCase = false) {
    if (!Array.isArray(ENDPOINTS) || !this.current) {
      return ""; // ENDPOINTS is not an array or current is falsy
    }
    const match = ENDPOINTS.find((e) => e && e.key === this.current);
    let label = "";
    if (match && match.label) {
      label = match.label;
    } else if (typeof this.current === "string" && this.current.length > 0) {
      label = this.current.charAt(0).toUpperCase() + this.current.slice(1);
    } else {
      label = "";
    }
    return lowerCase ? label.toLowerCase() : label;
  }
}
export const endpoint = new Endpoint();