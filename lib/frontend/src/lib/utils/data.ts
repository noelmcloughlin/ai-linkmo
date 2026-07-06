import yaml from "js-yaml";
import type {
  EndpointType,
  NexusRecord,
  NexusClass,
  YamlFiles,
  YamlFile,
} from "$types/index";
import {
  buildQueryString,
  mapFileToEndpointFormat,
  mapEndpointToFileFormat,
  normalizeRecord,
  getByoSectionKey,
  mutateArray,
  stripInternalFields,
  validateRecordId,
  showNotify,
  notifyResult,
  devWarn,
} from "$utils/index";
import { dataState, filters, filtered } from "$states/index";
import {
  APP_URL,
  ENDPOINT_MAP,
  YOUR_FILES,
  YOUR_DEFAULT_DATA_FILE,
  PROMINENT_FIELDS,
} from "$lib/constants";

/// LOCAL STATE ///
const fileState = {
  yourFiles: {} as Record<string, YamlFile>,

  // get to static files, which can be used from file uploads or downloads
  // Accepts array of { key, data } objects
  setYourFiles(files: Record<string, YamlFile>) {
    this.yourFiles = files;
  },
};

// local helper get to reset filtered items
export function resetFiltered(
  epKey: string = "",
  isCurateMode: boolean = false,
) {
  filters.reset();
  const items: NexusRecord[] = isCurateMode
    ? dataState.getItem(`${epKey}&byod`)
    : dataState.getItem(epKey);
  filtered.reset(items);
}

// Fetch data from backend API (or your files only).
export async function fetchData(
  ep: EndpointType = {} as EndpointType,
  byod: boolean = ep.getIncludeByod(),
  apiParams: Record<string, string | boolean> = {},
) {
  try {
    ep.setLoading(true);
    let items: NexusRecord[] = [];

    if (ep.isCurateMode) {
      const result = await fetchYourData();
      if (!result || result.type === "error") {
        throw new Error("No data fetched from your files");
      }
      // Use getItem to if a flat array from the current endpoint
      items = dataState.getItem(`${ep.current}&byod`) || [];
    } else {
      items = await fetchBackendApiData(ep.current, byod, apiParams);
    }
    return items;
  } catch (error) {
    showNotify(
      "error",
      error && typeof error === "object" && "message" in error
        ? (error as { message: string }).message
        : "Failed to fetch data",
    );
    dataState.setItems([{ key: ep.current, items: [] }]);
    return [];
  } finally {
    ep.setLoading(false);
  }
}

// Fetch data from the Ai Atlas Nexus backend API
// Note: Loading state should be managed by the caller
// Accepts primitive values to avoid creating reactive dependencies
export async function fetchBackendApiData(
  endpointName: string,
  byod: boolean = false,
  apiParams: Record<string, string | boolean> = {},
) {
  try {
    // Use utility functions to build query string
    const queryString = buildQueryString(apiParams);
    const url = `${ENDPOINT_MAP[endpointName]}?${queryString}${queryString ? "&" : ""}byod=${byod}`;

    // Fetch from url
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`Failed to fetch items from endpoint: ${endpointName}`);
    }
    const data = await response.json();
    return (data.items as NexusRecord[]) || [];
  } catch (error) {
    showNotify(
      "error",
      error && typeof error === "object" && "message" in error
        ? (error as { message: string }).message
        : "Failed to fetch data",
    );
    return [];
  }
}

// Fetch your local YAML data files
export async function fetchYourData(): Promise<{
  type: "success" | "error";
  message: string;
}> {
  const allFilesData: { key: string; data: YamlFile }[] = [];
  try {
    const responses = await Promise.allSettled(
      YOUR_FILES.map((file) =>
        fetch(`${APP_URL}/byo?filename=${file.key}.yaml`),
      ),
    );

    // Load what we can: one broken/missing file must not block the rest.
    for (let i = 0; i < responses.length; i++) {
      const result = responses[i];
      const file = YOUR_FILES[i];
      try {
        if (result.status !== "fulfilled") {
          throw new Error(String(result.reason));
        }
        if (!result.value.ok) {
          throw new Error(`HTTP ${result.value.status}`);
        }
        const text = await result.value.text();
        const yamlData = yaml.load(text);
        // A 404 page or plain-text error parses as a string; reject it.
        if (!yamlData || typeof yamlData !== "object") {
          throw new Error("file is not a YAML mapping");
        }
        allFilesData.push({
          key: file.key,
          data: {
            key: file.key,
            data: yamlData as Record<string, NexusRecord[]>,
          },
        });
      } catch (err) {
        showNotify(
          "warning",
          `Skipping data file '${file.key}': ${err instanceof Error ? err.message : String(err)}`,
        );
      }
    }
  } catch (error) {
    const message =
      typeof error === "object" && error !== null && "message" in error
        ? (error as { message: string }).message
        : String(error);
    return notifyResult("error", `Failed to load your data files: ${message}`);
  }

  if (allFilesData.length === 0) {
    return notifyResult("error", "Failed to load any of your data files.");
  }

  // Build yourFiles as YamlFiles (dictionary of YamlFile)
  const yourFiles: YamlFiles = Object.fromEntries(
    allFilesData.map(({ key, data }) => [key, data]),
  );

  // Unwrap YamlFile objects to pass only the raw YAML data to mapFileToEndpointFormat
  const alignedData = mapFileToEndpointFormat(
    allFilesData.map(({ key, data }) => ({ key, data: data.data })),
  );

  const alignedDataArray: NexusClass[] = [];
  for (const key in alignedData) {
    const value = alignedData[key];
    alignedDataArray.push({
      key: `${key}&byod`,
      items: Array.isArray(value) ? (value as NexusRecord[]) : [],
    });
  }

  // Set yourFiles and yourItems in the file state
  fileState.setYourFiles(yourFiles);
  dataState.setYourItems(alignedDataArray);
  return notifyResult("success", "Your data files loaded successfully.");
}

export async function mutateAndSaveRecord({
  action,
  endpointName,
  record,
}: {
  action: "add" | "edit" | "do";
  endpointName: string;
  record: NexusRecord;
}) {
  if (!record) {
    return notifyResult("error", `No record to ${action}.`);
  }

  const validation = validateRecordId(record);
  if (validation.type !== "success") {
    return notifyResult("error", validation.message);
  }

  const items = dataState.getItem(`${endpointName}&byod`) || [];
  const mergedData: Record<string, NexusRecord[]> = {};
  const resultRecord: NexusRecord = normalizeRecord(record);

  // Use mutateArray from mutation logic
  mergedData[endpointName] = mutateArray(items, resultRecord, action);

  // Only use mapped from section key.
  const dictName: string = getByoSectionKey(endpointName);
  // Determine filenameKey which is needed.
  const filenameKey =
    (record._filenameKey as string) ||
    (record?.isDefinedByTaxonomy as string) ||
    YOUR_DEFAULT_DATA_FILE;

  // Compute the updated YAML section without mutating the loaded file;
  // the in-memory file is only committed after a successful save.
  const files = fileState.yourFiles || {};
  const yamlFile = Object.values(files).find(
    (f) => f && typeof f === "object" && f.key === filenameKey,
  );
  if (!yamlFile) {
    devWarn("No loaded data file matches:", filenameKey);
    return notifyResult(
      "error",
      `Cannot save record: no loaded data file matches '${filenameKey}'.`,
    );
  }
  const existingArr: NexusRecord[] = Array.isArray(yamlFile.data?.[dictName])
    ? (yamlFile.data[dictName] as NexusRecord[])
    : [];
  const updatedYamlDataArr = mutateArray(existingArr, resultRecord, action);

  // Wrap the array in an object with the section key
  const updatedYamlData: Record<string, NexusRecord[]> = {
    [dictName]: updatedYamlDataArr,
  };

  try {
    const result = await updateDataAndSaveFile(
      filenameKey,
      endpointName,
      updatedYamlData,
      mergedData[endpointName],
    );
    if (!result || result.type !== "success") {
      return notifyResult("error", result?.message || "Failed to save data.");
    }
    // Always set a Notify object on success as well
    return notifyResult("success", "Operation successful.");
  } catch (err) {
    return notifyResult(
      "error",
      err instanceof Error ? err.message : String(err),
    );
  }
}

// Helper to update items array for a given key
function updateItemsArray(
  itemsArray: NexusClass[],
  key: string,
  items: NexusRecord[],
): NexusClass[] {
  let found = false;
  const updated = itemsArray.map((d) => {
    if (d.key === key) {
      found = true;
      return { ...d, items };
    }
    return d;
  });
  if (!found) {
    updated.push({ key, items });
  }
  return updated;
}

// Helper to update data and save the file
export async function updateDataAndSaveFile(
  filenameKey: string,
  endpointName: string,
  updatedYamlData: Record<string, NexusRecord[]>,
  updatedData: NexusRecord[],
) {
  // Merge the updatedYamlData into the full YAML structure to avoid clobbering
  if (updatedYamlData) {
    try {
      const yourFileKeyData = fileState.yourFiles[filenameKey];
      const fullYaml: Record<string, NexusRecord[]> =
        yourFileKeyData && yourFileKeyData.data
          ? { ...yourFileKeyData.data }
          : {};
      // Merge the updated section into the full YAML structure, but only for super keys
      for (const section of Object.keys(updatedYamlData)) {
        fullYaml[section] = updatedYamlData[section];
      }
      const result = await saveYamlData({
        yamlData: fullYaml,
        yourFileName: filenameKey,
      });
      if (result.type !== "success") {
        return result;
      }
      // Mutating dataState *refreshes UI* so done *after saveFile*.
      dataState.yourItems = updateItemsArray(
        dataState.yourItems,
        `${endpointName}&byod`,
        updatedData,
      );
      if (yourFileKeyData) yourFileKeyData.data = fullYaml;
      // Invalidate cached (non-curate) data that may include byod records
      dataState.bumpVersion();
    } catch (error) {
      return notifyResult(
        "error",
        "Failed to save YAML data." +
          (error instanceof Error ? error.message : String(error)),
      );
    }
    return notifyResult("success", "Data saved successfully.");
  }
  return notifyResult("error", "No YAML data to update or save.");
}

// Helper to remove empty/null/undefined values from objects
function removeEmptyFields(obj: unknown): unknown {
  if (obj === null || obj === undefined) {
    return undefined;
  }

  if (Array.isArray(obj)) {
    // Filter out empty/null items and recursively clean remaining items
    const cleaned = obj
      .map((item) => removeEmptyFields(item))
      .filter((item) => {
        if (item === null || item === undefined || item === "") return false;
        if (Array.isArray(item) && item.length === 0) return false;
        if (typeof item === "object" && Object.keys(item).length === 0)
          return false;
        return true;
      });
    return cleaned.length > 0 ? cleaned : undefined;
  }

  if (typeof obj === "object") {
    const cleaned: Record<string, unknown> = {};
    for (const [key, value] of Object.entries(obj)) {
      const cleanedValue = removeEmptyFields(value);
      // Only add field if it's not empty/null/undefined
      if (
        cleanedValue !== null &&
        cleanedValue !== undefined &&
        cleanedValue !== ""
      ) {
        if (Array.isArray(cleanedValue) && cleanedValue.length === 0) continue;
        if (
          typeof cleanedValue === "object" &&
          !Array.isArray(cleanedValue) &&
          Object.keys(cleanedValue).length === 0
        )
          continue;
        cleaned[key] = cleanedValue;
      }
    }
    return cleaned;
  }

  // Primitive values: return as-is unless empty string
  return obj === "" ? undefined : obj;
}

// Helper to reorder object fields with PROMINENT_FIELDS first.
// Otherwise the yaml looks a bit silly.
function reorderFields(obj: unknown): unknown {
  if (obj === null || obj === undefined) {
    return obj;
  }

  if (Array.isArray(obj)) {
    // Recursively reorder items in array
    return obj.map((item) => reorderFields(item));
  }

  if (typeof obj === "object") {
    const record = obj as Record<string, unknown>;
    const reordered: Record<string, unknown> = {};

    // First, add prominent fields in order if they exist
    for (const prominentField of PROMINENT_FIELDS) {
      if (prominentField in record) {
        const value = record[prominentField];
        // Recursively reorder nested objects/arrays
        reordered[prominentField] = reorderFields(value);
      }
    }

    // Then add remaining fields in their original order
    for (const [key, value] of Object.entries(record)) {
      if (!PROMINENT_FIELDS.includes(key)) {
        // Recursively reorder nested objects/arrays
        reordered[key] = reorderFields(value);
      }
    }

    return reordered;
  }

  // Primitive values: return as-is
  return obj;
}

// Save YAML data and set a result object
export async function saveYamlData({
  yamlData = {} as Record<string, NexusRecord[]>,
  yourFileName = YOUR_DEFAULT_DATA_FILE,
}: {
  yamlData?: Record<string, NexusRecord[]>;
  yourFileName?: string;
}) {
  try {
    // Prevent saving empty files - indicates a logical error or state confusion
    if (!yamlData || Object.keys(yamlData).length === 0) {
      return notifyResult(
        "error",
        "Cannot save empty YAML file. This may indicate a state error or page refresh issue.",
      );
    }

    // Strip _filenameKey from all records before saving
    const strippedYamlData: Record<string, NexusRecord[]> = {};
    for (const [key, val] of Object.entries(yamlData)) {
      if (Array.isArray(val)) {
        strippedYamlData[key] = stripInternalFields(val);
      } else if (val && typeof val === "object") {
        strippedYamlData[key] = stripInternalFields([val as NexusRecord]);
      } else {
        strippedYamlData[key] = [];
      }
    }

    const cleanYamlData = mapEndpointToFileFormat(strippedYamlData);
    // Remove empty/null/undefined fields before writing to YAML
    const yamlDataWithoutEmpties = removeEmptyFields(cleanYamlData);
    // Reorder fields so PROMINENT_FIELDS appear first
    const yamlDataReordered = reorderFields(yamlDataWithoutEmpties);

    // Final check: ensure we're not saving an empty structure after cleaning
    if (
      !yamlDataReordered ||
      typeof yamlDataReordered !== "object" ||
      Object.keys(yamlDataReordered as Record<string, unknown>).length === 0
    ) {
      return notifyResult(
        "error",
        "Cannot save YAML file: all data was filtered out during cleaning. This may indicate empty records or a state error.",
      );
    }

    const yamlText = yaml.dump(yamlDataReordered);

    // Persist the actual file (backup handled by API server)
    const res = await fetch(`${APP_URL}/byo?filename=${yourFileName}.yaml`, {
      method: "PUT",
      headers: { "Content-Type": "application/octet-stream" },
      body: yamlText,
    });

    if (!res.ok) {
      const errorText = await res.text();
      return notifyResult(
        "error",
        `Failed to save data from ${yourFileName}: ${errorText}`,
      );
    }

    // In-memory state (fileState + dataState.yourItems) is updated by the
    // caller (updateDataAndSaveFile) after this returns success, using the
    // endpoint-scoped items; doing it here with raw file sections risked
    // storing the wrong section under the endpoint key.
    return notifyResult("success", "Data saved successfully.");
  } catch (e) {
    const msg =
      e && typeof e === "object" && "message" in e
        ? (e as { message?: string }).message || ""
        : String(e);
    return notifyResult("error", `Failed to save data: ${msg}`);
  }
}
