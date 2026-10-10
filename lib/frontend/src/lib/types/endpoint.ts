export type EndpointType = {
  current: string;
  includeByod: boolean;
  isCurateMode: boolean;
  setLoading: (loading: boolean) => void;
  getIncludeByod: () => boolean;
};

// One entry of src/lib/entities.json, written by `just gen-ui-config` from lib/api/api.yaml.
export type GeneratedEndpoint = {
  key: string;
  path: string;
  label: string;
  type: string;
  byo: string;
  description: string;
  filters: string[];
  prominent: string[];
};

// A generated entry after the hand-written overlay in constants.ts is merged over it.
export type UiEndpoint = GeneratedEndpoint;
