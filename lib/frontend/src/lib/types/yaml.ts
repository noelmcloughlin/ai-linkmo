// Grouping of records by key (e.g., endpoint section).

export type NexusClass = { key: string; items: NexusRecord[] };

export type YamlFile = {
  key: string;
  data: Record<string, NexusRecord[]>;
};

export type YamlFiles = {
  [key: string]: YamlFile;
};

// A NexusSection is the section-key string used to index into a YAML file
// (e.g., "controls", "actions", "entries").
export type NexusSection = string;

export type NexusRecord = { id?: string; [key: string]: unknown };
