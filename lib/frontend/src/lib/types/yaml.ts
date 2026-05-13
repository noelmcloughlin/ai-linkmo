// Grouping Promise records by key (e.g., endpoint section).

export type  NexusClass = { key: string; items: NexusRecord[] };

export type  YamlFile = {
  key: string;
  data: Record<string, NexusSection[]>;
}

export type  YamlFiles = {
  [key: string]: YamlFile;
}

export type  NexusSection = {
  [section: string]: NexusRecord[];
}

export type  NexusRecord = { id?: string; [key: string]: unknown };

