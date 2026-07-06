import type { NexusRecord, Notify, NotificationType } from "$types/index";
import { notify } from "$states/index";
import { ACTIVE_FILTER_PARAMS } from "$states/filters.svelte";

// Safely converts string/array of strings to lowercase.
// If not string or array, returns empty string.
export const safeLower = (v: string | string[]): string | string[] =>
  typeof v === "string"
    ? v.toLowerCase()
    : Array.isArray(v)
      ? v.map((s) => (typeof s === "string" ? s.toLowerCase() : ""))
      : "";

// utility get from building query strings
export function buildQueryString(params: unknown): string {
  return Object.entries(params as Record<string, unknown>)
    .filter(([, v]) => v !== undefined && v !== "")
    .map(
      ([k, v]) => `${encodeURIComponent(k)}=${encodeURIComponent(String(v))}`,
    )
    .join("&");
}

export function normalizeRecord(obj: NexusRecord): NexusRecord {
  if (obj && typeof obj === "object") {
    const c = { ...obj };
    for (const k in c) {
      if (c[k] === undefined || c[k] === null) {
        c[k] = "";
      } else if (Array.isArray(c[k]) && c[k].length === 0) {
        c[k] = [];
      } else if (typeof c[k] === "string" && c[k].trim() === "") {
        c[k] = "";
      } else if (Array.isArray(c[k])) {
        // if the property is an array of NexusRecord, normalize each element
        c[k] = c[k].map((item: NexusRecord) => normalizeRecord(item));
      }
    }
    return c;
  }
  return obj;
}

// Utility to deeply strip _filenameKey from all records in all arrays
export function stripInternalFields(
  record: NexusRecord | NexusRecord[],
): NexusRecord[] {
  if (Array.isArray(record)) {
    return record.map((r) => stripInternalFields(r)[0]);
  }
  if (record && typeof record === "object") {
    const { _filenameKey: _drop, ...rest } = record;
    void _drop;
    return [rest as NexusRecord];
  }
  return [];
}

// Helper to apply add/edit/delete ("do") to an array of records.
// Always returns a new array so callers can defer committing to state
// until the change has actually been persisted.
export function mutateArray(
  arr: NexusRecord[],
  record: NexusRecord,
  action: "add" | "edit" | "do",
): NexusRecord[] {
  if (action === "do") {
    return arr.filter((r) => r.id !== record.id);
  }
  const idx = arr.findIndex((r) => r.id === record.id);
  if (idx !== -1) {
    const copy = [...arr];
    copy[idx] = record;
    return copy;
  }
  return [...arr, record];
}

// Only http(s) URLs may be rendered as links; record data comes from
// editable YAML files, so anything else (javascript:, data:, ...) is unsafe.
export function isSafeHttpUrl(value: unknown): value is string {
  return typeof value === "string" && /^https?:\/\//i.test(value.trim());
}

// get to if a specific file by key
export function validateRecordId(record: NexusRecord): Notify {
  if (!record || typeof record.id !== "string" || record.id.trim() === "") {
    return { type: "error", message: "ID is required." };
  }
  return { type: "success", message: "" };
}

// Helper to show notifications
export function showNotify(type: NotificationType | string, message: string) {
  if (type === "error") {
    notify.error(message);
  } else {
    notify.add({ type: type as NotificationType, message });
  }
}

// Helper to create Notify object
export function notifyResult(
  type: "success" | "error",
  message: string,
): { type: "success" | "error"; message: string } {
  return { type: type, message };
}

// Utility to check if any filters are active
export function hasAnyActiveFilter(
  filters: Record<string, unknown> | { [key: string]: unknown },
  includeOnlyShowIds = false,
): boolean {
  // Check if any filter param is truthy (excludes schemaField and isRelatedMode)
  const hasFilter = ACTIVE_FILTER_PARAMS.some((param: string | number) => {
    const value = filters[param];
    return value && value !== "";
  });

  return hasFilter || (includeOnlyShowIds && Boolean(filters.onlyShowIds));
}

// Development-only console logging
export function devLog(message: string, ...args: unknown[]): void {
  if (import.meta.env?.DEV) {
    console.log(message, ...args);
  }
}

export function devWarn(message: string, ...args: unknown[]): void {
  if (import.meta.env?.DEV) {
    console.warn(message, ...args);
  }
}

export function devError(message: string, ...args: unknown[]): void {
  if (import.meta.env?.DEV) {
    console.error(message, ...args);
  }
}
