export type  EndpointType = {
  current: string;
  includeByod: boolean;
  isCurateMode: boolean;
  setLoading: (loading: boolean) => void;
  getIncludeByod: () => boolean;
};
