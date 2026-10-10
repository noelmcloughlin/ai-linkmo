import entities from "./entities.json";
import type { GeneratedEndpoint, UiEndpoint } from "$types/endpoint";

// Identity customiztion (BYO identity)
export const BYO_ICON_TEXT: string = "ACME";
export const APP_NAME: string = "AI-LinkMO";
// Files in static/ (Vite publicDir) are served from the site root.
export const APP_LOGO_PATH: string = "/ai_atlas_nexus_vector.svg";
export const BYO_LOGO_PATH: string = "/mylogo.png";
export const ACME_LOGO_URL: string =
  "https://upload.wikimedia.org/wikipedia/commons/9/91/Acme_Markets_lolo_1.svg";
export const FINOS_LOGO_URL: string =
  "https://finos.org/hubfs/FINOS/finos-logo/FINOS_Icon_Workmark_Name_horz_White.svg";

// Footer
export const GITHUB_REPO_URL: string =
  "https://github.com/noelmcloughlin/ai-linkmo.git";
export const AI_ATLAS_NEXUS_URL: string =
  "https://ibm.github.io/ai-atlas-nexus";
export const AI_ONTOLOGY_URL: string =
  "https://ibm.github.io/ai-atlas-nexus/ontology/";
export const SVELTE_URL: string = "https://svelte.dev";
export const VITE_URL: string = "https://vite.dev";
export const LINKML_URL: string = "https://linkml.io";
export const FINOS_URL: string = "https://finos.org";

// UI dimensions live as CSS custom properties in app.css (:root):
// --header-height, --footer-height, --aside-*. Reference them with var().

// Timing and animation
export const NOTIFICATION_DEFAULT_DURATION: number = 5000; // in milliseconds
export const DROPDOWN_DEBOUNCE_WAIT: number = 2000; // in milliseconds

// Cache
export const MAX_CACHE_SIZE: number = 20;

// Notification colors by type
export const NOTIFICATION_COLORS = {
  error: { border: "#dc2626", background: "#fee2e2" },
  success: { border: "#16a34a", background: "#d1fae5" },
  warning: { border: "#f59e42", background: "#fef3c7" },
  info: { border: "#2563eb", background: "#e0edfa" },
} as const;

// Generate using linkml gen-jsonschema.
export const SCHEMA_FILE_JSON: string = "/schema/ai-risk-ontology.json";

// Default base URL for the application
export const APP_URL: string = ""; // use Vite's proxy for development

// BYO Taxonomies
export const YOUR_DEFAULT_DATA_FILE: string = "finos-aigf";
// Keys must be the basename (no .yaml suffix) of a file in byo/data/.
// fetchYourData appends ".yaml" when calling /byo?filename=...
export const YOUR_FILES = [
  { key: "finos-aigf", priority: 1 },
  { key: "eu_ai_act", priority: 2 },
  { key: "ffiec_it_handbook", priority: 3 },
  { key: "iso_42001", priority: 4 },
  { key: "nist_ai_600_1", priority: 5 },
  { key: "nist_sp_800_53_r5", priority: 6 },
  { key: "owasp_llm_top_10", priority: 7 },
  { key: "owasp_ml_top_10", priority: 8 },
  { key: "sr_11_7", priority: 9 },
];

// Default endpoint for the application
// This is the endpoint that will be selected when the app loads
export const DEFAULT_ENDPOINT: string = "taxonomy";

// The entity list is generated from lib/api/api.yaml by `just gen-ui-config`, so an
// endpoint key here is an API route by construction. entities.json is not hand-edited;
// what the schema cannot know lives in the overlays below and is merged over it.
const GENERATED_ENDPOINTS: GeneratedEndpoint[] = entities.endpoints;

// Hand-written overrides per endpoint key. A label replaces the plural derived from the
// class name where that reads badly in the sidebar; a byo replaces the derived
// Container slot if a bring-your-own-data file ever keeps a class under another key.
const ENDPOINT_OVERLAY: Record<
  string,
  Partial<Pick<UiEndpoint, "label" | "byo">>
> = {
  taxonomy: { label: "Taxonomies" },
  obligation: { label: "Obligations" },
  recommendation: { label: "Recommendations" },
  group: { label: "Risk Groups" },
  evaluation: { label: "Evaluations" },
};

// List of all endpoints available in the application, in the order of api.yaml.
// Each endpoint has a key, label, class name, byo section and derived defaults.
// Used to dynamically generate UI forms and views based on selected endpoint.
export const ENDPOINTS: UiEndpoint[] = GENERATED_ENDPOINTS.map((e) => ({
  ...e,
  ...(ENDPOINT_OVERLAY[e.key] ?? {}),
}));

// Grouped endpoints for navigation accordion
export const ENDPOINT_GROUPS = [
  {
    id: "governance",
    label: "Governance & Risk",
    icon: "",
    endpoints: [
      "taxonomy",
      "vocabulary",
      "obligation",
      "recommendation",
      "requirement",
      "risk",
      "group",
      "principle",
    ],
  },
  {
    id: "ai-resources",
    label: "AI Resources",
    icon: "",
    endpoints: [
      "model",
      "task",
      "evaluation",
      "dataset",
      "adapter",
      "intrinsic",
    ],
  },
  {
    id: "operations",
    label: "Operations",
    icon: "",
    endpoints: ["control", "incident", "action"],
  },
  {
    id: "data",
    label: "Data & Docs",
    icon: "",
    endpoints: ["document", "benchmarkcard", "questionpolicy"],
  },
  {
    id: "entities",
    label: "Entities",
    icon: "",
    endpoints: ["organization", "stakeholder"],
  },
];

// Endpoint key to API route. The generator takes both from the same exposure entry.
export const ENDPOINT_MAP: Record<string, string> = Object.fromEntries(
  ENDPOINTS.map((e) => [e.key, e.path]),
);

// Record field IDs for display priority in all UI cards, any endpoint
export const PROMINENT_FIELDS = [
  "id",
  "name",
  "description",
  "isDefinedByTaxonomy",
  "isDefinedByRisk",
  "isDefinedByDocument",
];

// Fields that should be rendered as textarea-multiline inputs in forms
export const TEXTAREA_FIELDS = ["description", "concern"];

// Which Right Aside filter buttons to show per endpoint key. Every name must be a
// parameter of the endpoint's class (the API rejects an unknown filter with 422;
// lib/test/test_ui_config.py checks this list against the schema). An endpoint absent
// here falls back to the filters the generator derived from the schema.
const UI_FILTER_OVERLAY: { [key: string]: string[] } = {
  taxonomy: ["hasDocumentation", "hasLicense", "type"],
  // risk - excluding 'hasDocumentation', 'phase', 'implementationByAdapter'.
  risk: [
    "isDefinedByTaxonomy",
    "risk_type",
    "isPartOf",
    "descriptor",
    "broad_mappings",
    "related_mappings",
    "hasRelatedAction",
  ],
  obligation: [
    "isDefinedByTaxonomy",
    "hasControlApplication",
    "hasEvidenceCategory",
    "hasTypicalLocation",
    "hasRule",
    "hasRequirement",
    "hasRequirementType",
  ],
  requirement: [
    "isDefinedByTaxonomy",
    "hasApplication",
    "hasFrequency",
    "hasRequirementType",
    "hasRule",
    "type",
    "isCategorizedAs",
  ],
  recommendation: [
    "isDefinedByTaxonomy",
    "hasControlApplication",
    "hasEvidenceCategory",
    "hasTypicalLocation",
    "hasRule",
    "hasRequirement",
    "hasRequirementType",
  ],
  // group - excluding 'hasPart', 'isDetectedBy'.
  group: [
    "isDefinedByTaxonomy",
    "hasDocumentation",
    "belongsToDomain",
    "type",
    "broad_mappings",
    "narrow_mappings",
  ],
  action: [
    "isDefinedByTaxonomy",
    "hasAiActorTask",
    "detectsRiskConcept",
    "hasRelatedRisk",
  ],
  control: [
    "isDefinedByTaxonomy",
    "hasDocumentation",
    "detectsRiskConcept",
    "isDetectedBy",
    "hasRelatedRisk",
  ],
  incident: [
    "isDefinedByTaxonomy",
    "refersToRisk",
    "hasConsequence",
    "hasImpact",
    "hasLikelihood",
  ],
  benchmarkcard: [
    "hasDocumentation",
    "hasLicense",
    "hasTasks",
    "hasDomains",
    "hasRelatedRisk",
  ],
  evaluation: [
    "hasDocumentation",
    "hasLicense",
    "hasDataset",
    "hasTasks",
    "hasRelatedRisk",
  ],
  document: ["hasLicense"],
  dataset: ["hasDocumentation", "hasLicense", "isProvidedBy"],
  model: [
    "hasDocumentation",
    "hasLicense",
    "hasRiskControl",
    "performsTask",
    "hasInputModality",
    "hasOutputModality",
    "isProvidedBy",
  ],
  task: [
    "hasDocumentation",
    "isDefinedByTaxonomy",
    "isDefinedByVocabulary",
    "requiredByTask",
    "implementedByAdapter",
    "requiresCapability",
  ],
  adapter: [
    "hasDocumentation",
    "isDefinedByTaxonomy",
    "hasLicense",
    "hasAdapterType",
    "adaptsModel",
    "implementsCapability",
    "hasRelatedRisk",
    "hasRiskControl",
  ],
  stakeholder: ["isDefinedByTaxonomy", "isPartOf"],
  intrinsic: [
    "isDefinedByTaxonomy",
    "hasDocumentation",
    "isDefinedByVocabulary",
    "hasAdapter",
    "requiredByTask",
    "implementedByAdapter",
    "requiresCapability",
    "hasRelatedRisk",
  ],
  questionpolicy: ["isDefinedByTaxonomy", "hasRule", "hasRelatedRisk"],
  principle: [
    "isDefinedByTaxonomy",
    "isDefinedByVocabulary",
    "hasDocumentation",
    "isPartOf",
    "implementedByAdapter",
    "requiresCapability",
  ],
  organization: ["grants_license"],
};

export const UI_WANTED_FILTERS: { [key: string]: string[] } =
  Object.fromEntries(
    ENDPOINTS.map((e) => [e.key, UI_FILTER_OVERLAY[e.key] ?? e.filters]),
  );

// Default personas for authentication with avatars
export const DEFAULT_PERSONAS = [
  {
    name: "Jane First-Line",
    avatar:
      "https://ui-avatars.com/api/?name=Jane+Doe&background=0D8ABC&color=fff&size=32",
  },
  {
    name: "John Second-Line",
    avatar:
      "https://ui-avatars.com/api/?name=John+Smith&background=43b02a&color=fff&size=32",
  },
  {
    name: "Alice Third-Line",
    avatar:
      "https://ui-avatars.com/api/?name=Alice+Johnson&background=6366f1&color=fff&size=32",
  },
];

// fallback avatar for personas
export const DEFAULT_AVATAR =
  "https://ui-avatars.com/api/?name=Default&background=cccccc&color=ffffff&size=32";
