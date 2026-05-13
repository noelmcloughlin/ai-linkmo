// Identity customiztion (BYO identity)
export const BYO_ICON_TEXT: string = 'ACME';
export const APP_NAME: string = 'AI-LinkMO';
export const APP_LOGO_PATH: string = '/static/ai_atlas_nexus_vector.svg';
export const BYO_LOGO_PATH: string = '/static/mylogo.svg';
export const ACME_LOGO_URL: string = 'https://upload.wikimedia.org/wikipedia/commons/9/91/Acme_Markets_lolo_1.svg';
export const FINOS_LOGO_URL: string = 'https://finos.org/hubfs/FINOS/finos-logo/FINOS_Icon_Workmark_Name_horz_White.svg';

// Footer
export const GITHUB_REPO_URL: string = 'https://github.com/IBM/ai-atlas-nexus-user-demo.git';
export const AI_ATLAS_NEXUS_URL: string = 'https://ibm.github.io/ai-atlas-nexus';
export const AI_ONTOLOGY_URL: string = 'https://ibm.github.io/ai-atlas-nexus/ontology/';
export const SVELTEKIT_URL: string = 'https://kit.svelte.dev';
export const LINKML_URL: string = 'https://linkml.io';
export const FINOS_URL: string = 'https://finos.org';

// UI Dimensions
export const HEADER_HEIGHT: string = '6.25rem';
export const ASIDE_TOP_OFFSET_LEFT: string = `calc(${HEADER_HEIGHT} + 1.25rem)`;
export const ASIDE_TOP_OFFSET_RIGHT: string = '7.25rem';
export const ASIDE_HEIGHT: string = '80vh';
export const ASIDE_WIDTH_LEFT: string = `clamp(260px, 18vw, 300px)`;
export const ASIDE_WIDTH_RIGHT: string = `clamp(300px, 32vw, 360px)`;
export const FOOTER_HEIGHT: string = '56px';
export const ASIDE_TRANSITION_DURATION: string = '0.2s';

// Timing and animation
export const NOTIFICATION_DEFAULT_DURATION: number = 5000; // in milliseconds
export const DROPDOWN_DEBOUNCE_WAIT: number = 2000;  // in milliseconds

// Cache
export const MAX_CACHE_SIZE: number = 20;

// Notification colors by type
export const NOTIFICATION_COLORS = {
    error: { border: '#dc2626', background: '#fee2e2' },
    success: { border: '#16a34a', background: '#d1fae5' },
    warning: { border: '#f59e42', background: '#fef3c7' },
    info: { border: '#2563eb', background: '#e0edfa' },
} as const;

// Generate using linkml gen-jsonschema.
export const SCHEMA_FILE_JSON: string = '/static/schema/ai-risk-ontology.json';

// Default base URL for the application
export const APP_URL: string = '';  // use Vite's proxy for development

// BYO Taxonomies
export const YOUR_DEFAULT_DATA_FILE: string = 'acme-ai-taxonomy';
export const YOUR_FILES = [
    { key: 'acme-ai-taxonomy', priority: 1 },
    { key: 'acme-ai-dso-taxonomy', priority: 2 },
];

// Default endpoint for the application
// This is the endpoint that will be selected when the app loads
export const DEFAULT_ENDPOINT: string = 'taxonomy';

// List of all endpoints available in the application
// Each endpoint has a key, label, and class name for TS schema mappings.
// Used to dynamically generate UI forms and views based on selected endpoint.
export const ENDPOINTS = [
    { key: 'taxonomy', label: 'Taxonomies', type: "RiskTaxonomy", byo: 'taxonomies' },
    { key: 'obligation', label: 'Obligations', type: "ControlActivityObligation", byo: 'rules' },
    { key: 'recommendation', label: 'Recommendations', type: "ControlActivityRecommendation", byo: 'rules' },
    { key: 'risk', label: 'Risks', type: "Risk", byo: 'entries' },
    { key: 'group', label: 'Risk Groups', type: "RiskGroup", byo: 'groups' },
    { key: 'action', label: 'Actions', type: "Action", byo: 'actions' },
    { key: 'control', label: 'Controls', type: "RiskControl", byo: 'controls' },
    { key: 'incident', label: 'Incidents', type: "RiskIncident", byo: 'incidents' },
    { key: 'model', label: 'Ai Models', type: "AiModel", byo: 'aimodels' },
    { key: 'task', label: 'Ai Tasks', type: "AiTask", byo: 'aitasks' },
    { key: 'evaluation', label: 'Evaluations', type: "AiEval", byo: 'evaluations' },
    { key: 'dataset', label: 'Datasets', type: "Dataset", byo: 'datasets' },
    { key: 'adapter', label: 'Adapters', type: "Adapter", byo: 'adapters' },
    { key: 'intrinsic', label: 'LLM Intrinsics', type: "LLMIntrinsic", byo: 'intrinsics' },
    { key: 'organization', label: 'Organizations', type: "Organization", byo: 'organizations' },
    { key: 'document', label: 'Documents', type: "Documentation", byo: 'documents' },
    { key: 'principle', label: 'Principles', type: "Principle", byo: 'entries' },
    { key: 'stakeholder', label: 'Stakeholders', type: "Stakeholder", byo: 'stakeholders' },
    { key: 'benchmarkcard', label: 'Benchmarkcards', type: "BenchmarkMetadataCard", byo: 'benchmarkcards' },
    { key: 'questionpolicy', label: 'Questionpolicies', type: 'LLMQuestionPolicy', byo: 'questionpolicies' },
];

// Grouped endpoints for navigation accordion
export const ENDPOINT_GROUPS = [
    {
        id: 'governance',
        label: 'Governance & Risk',
        icon: '',
        endpoints: ['taxonomy', 'obligation', 'recommendation', 'risk', 'group', 'principle']
    },
    {
        id: 'ai-resources',
        label: 'AI Resources',
        icon: '',
        endpoints: ['model', 'task', 'evaluation', 'dataset', 'adapter', 'intrinsic']
    },
    {
        id: 'operations',
        label: 'Operations',
        icon: '',
        endpoints: ['control', 'incident', 'action']
    },
    {
        id: 'data',
        label: 'Data & Docs',
        icon: '',
        endpoints: ['document', 'benchmarkcard', 'questionpolicy']
    },
    {
        id: 'entities',
        label: 'Entities',
        icon: '',
        endpoints: ['organization', 'stakeholder']
    }
];

// Convert ENDPOINTS array to a map for key lookup
export const ENDPOINT_MAP = Array.isArray(ENDPOINTS)
    ? Object.fromEntries(ENDPOINTS.map(e => [e.key, `/${e.key}`]))
    : ENDPOINTS;

// Record field IDs for display priority in all UI cards, any endpoint
export const PROMINENT_FIELDS = ['id', 'name', 'description', 'isDefinedByTaxonomy', 'isDefinedByRisk', 'isDefinedByDocument'];

// Fields that should be rendered as textarea-multiline inputs in forms
export const TEXTAREA_FIELDS = ['description', 'concern'];

// Defines which Right Aside filter buttons are valid for each scope (endpoing key)
export const UI_WANTED_FILTERS: { [key: string]: string[] } = {
    taxonomy: ['hasDocumentation', 'hasLicense', 'type'],
    // risk - excluding 'hasDocumentation', 'phase', 'implementationByAdapter'.
    risk: ['isDefinedByTaxonomy', 'risk_type', 'isPartOf', 'descriptor', 'broad_mappings', 'related_mappings', 'hasRelatedAction'],
    obligation: ['isDefinedByTaxonomy', 'hasControlApplication', 'hasEvidenceCategory', 'hasTypicalLocation', 'appliesToCapability', 'hasRule', 'hasRequirement', 'hasRequirementType'],
    recommendation: ['isDefinedByTaxonomy', 'hasControlApplication', 'hasEvidenceCategory', 'hasTypicalLocation', 'appliesToCapability', 'hasRule', 'hasRequirement', 'hasRequirementType'],
    // group - excluding 'hasPart', 'isDetectedBy'.
    group: ['isDefinedByTaxonomy', 'hasDocumentation', 'belongsToDomain', 'type', 'broad_mappings', 'narrow_mappings'],
    action: ['isDefinedByTaxonomy', 'hasAiActorTask', 'detectsRiskConcept', 'hasRelatedRisk'],
    control: ['isDefinedByTaxonomy', 'hasDocumentation', 'hasAiActorTask', 'detectsRiskConcept', 'isDetectedBy', 'hasRelatedRisk'],
    incident: ['isDefinedByTaxonomy', 'refersToRisk', 'hasConsequence', 'hasImpact', 'hasLikelihood'],
    benchmarkcard: ['hasDocumentation', 'hasLicense', 'hasTasks', 'hasDomains', 'hasRelatedRisk'],
    evaluation: ['hasDocumentation', 'hasLicense', 'hasDataset', 'hasTasks', 'hasRelatedRisk'],
    document: ['hasLicense'],
    dataset: ['hasDocumentation', 'hasLicense', 'hasProvider'],
    model: ['hasDocumentation', 'hasLicense', 'hasRiskControl', 'performsTask', 'hasInputModality', 'hasOutputModality', 'isProvidedBy'],
    task: ['hasDocumentation', 'isDefinedByTaxonomy', 'isDefinedByVocabulary', 'hasLicense', 'hasAdapterType', 'adaptsModel', 'implementsCapability', 'hasRelatedRisk', 'hasRiskControl'],
    adapter: ['hasDocumentation', 'isDefinedByTaxonomy', 'hasLicense', 'hasAdapterType', 'adaptsModel', 'implementsCapability', 'hasRelatedRisk', 'hasRiskControl'],
    stakeholder: ['isDefinedByTaxonomy', 'isPartOf'],
    intrinsic: ['isDefinedByTaxonomy', 'hasDocumentation', 'isDefinedByVocabulary', 'hasAdapter', 'requiredByTask', 'implementedByAdapter', 'requiresCapability', 'hasRelatedRisk'],
    questionpolicy: ['isDefinedByTaxonomy', 'hasRule', 'hasRelatedRisk'],
    principle: ['isDefinedByTaxonomy', 'isDefinedByVocabulary', 'hasDocumentation', 'isPartOf', 'implementedByAdapter', 'requiredByTask', 'requiresCapability'],
    organization: ['grants_license'],
};

// Default personas for authentication with avatars
export const DEFAULT_PERSONAS = [
    {
        name: 'Jane First-Line',
        avatar:
            "https://ui-avatars.com/api/?name=Jane+Doe&background=0D8ABC&color=fff&size=32"
    },
    {
        name: 'John Second-Line',
        avatar:
            "https://ui-avatars.com/api/?name=John+Smith&background=43b02a&color=fff&size=32"
    },
    {
        name: 'Alice Third-Line',
        avatar:
            "https://ui-avatars.com/api/?name=Alice+Johnson&background=6366f1&color=fff&size=32"
    },
];

// fallback avatar for personas
export const DEFAULT_AVATAR = "https://ui-avatars.com/api/?name=Default&background=cccccc&color=ffffff&size=32";