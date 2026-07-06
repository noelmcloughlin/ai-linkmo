// lib/frontend/src/lib/utils/linkml.ts
import { ENDPOINTS } from "$lib/constants";

// Mapping: Nexus yaml file section → webapp endpoint format section key
export function getByoSectionKey(endpointKey: string): string {
  const ep = ENDPOINTS.find((e) => e.key === endpointKey);
  return ep?.byo || endpointKey;
}

// Mapping: Nexus Yaml file format → webapp endpoint format
export function mapFileToEndpointFormat(
  yamlFiles: { key: string; data: unknown }[],
): Record<string, unknown> {
  const alignedData: Record<string, unknown> = {};
  for (const file of yamlFiles) {
    const yamlData = file.data;
    if (typeof yamlData === "object" && yamlData !== null) {
      for (const ep of ENDPOINTS) {
        const byoSection = getByoSectionKey(ep.key);
        if (byoSection === "entries") continue;
        if (Array.isArray((yamlData as Record<string, unknown>)[byoSection])) {
          if (!alignedData[ep.key]) alignedData[ep.key] = [];
          // Add _filenameKey to each record
          const sectionArr = (yamlData as Record<string, unknown>)[
            byoSection
          ] as unknown[];
          const sectionArrWithKey = sectionArr.map((rec) => {
            if (typeof rec === "object" && rec !== null) {
              return {
                ...(rec as Record<string, unknown>),
                _filenameKey: file.key,
              };
            }
            return rec;
          });
          alignedData[ep.key] = (alignedData[ep.key] as unknown[]).concat(
            sectionArrWithKey,
          );
        }
      }
      // Always check for 'entries' as a special case
      if (Array.isArray((yamlData as Record<string, unknown>)["entries"])) {
        // Iterate through each entry in the 'entries' section
        for (const entry of (yamlData as Record<string, unknown>)[
          "entries"
        ] as unknown[]) {
          for (const ep of ENDPOINTS) {
            const byoSection = getByoSectionKey(ep.key);
            if (byoSection !== "entries") continue;
            // Check if the entry matches the endpoint type
            if ((entry as Record<string, unknown>).type === ep.type) {
              // Initialize the array if it doesn't exist
              if (!alignedData[ep.key]) alignedData[ep.key] = [];
              // Add _filenameKey to each entry
              if (typeof entry === "object" && entry !== null) {
                // Add the entry with the filename key
                (alignedData[ep.key] as unknown[]).push({
                  ...(entry as Record<string, unknown>),
                  _filenameKey: file.key,
                });
              } else {
                (alignedData[ep.key] as unknown[]).push(entry);
              }
              break;
            }
          }
        }
      }
    }
  }
  return alignedData || {};
}

// Mapping: webapp endpoint format → Nexus Yaml file format
export function mapEndpointToFileFormat(
  mergedData: Record<string, unknown>,
): Record<string, unknown> {
  const yamlData: Record<string, unknown> = {};

  // Always include entries if present
  if (Array.isArray(mergedData.entries) && mergedData.entries.length > 0) {
    yamlData.entries = mergedData.entries.map((item: unknown) =>
      typeof item === "object" && item !== null
        ? JSON.parse(JSON.stringify(item))
        : item,
    );
  }
  // Include all other array properties, using getByoSectionKey
  for (const key in mergedData) {
    if (
      key !== "entries" &&
      Array.isArray(mergedData[key]) &&
      mergedData[key].length > 0
    ) {
      const byoSection = getByoSectionKey(key);
      yamlData[byoSection] = (mergedData[key] as unknown[]).map(
        (item: unknown) =>
          typeof item === "object" && item !== null
            ? JSON.parse(JSON.stringify(item))
            : item,
      );
    }
  }
  return yamlData;
}
