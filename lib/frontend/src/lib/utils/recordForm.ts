// Helpers behind RecordForm.svelte. They turn a class definition from the JSON
// Schema that gen-jsonschema writes into the schema and UI schema that @sjsf
// renders, seed a record the way the hand-built form did, and merge the value
// the form submits back into a record for the save path. They are plain
// functions so that the unit tests can run them in node.

import type { ResolvableUiOptions, Schema, UiSchema } from "@sjsf/form";
import type { Ajv } from "ajv";
import { SCHEMA_FILE_JSON, YOUR_DEFAULT_DATA_FILE } from "$lib/constants";
import type { NexusRecord } from "$types/yaml";

type JsonObject = Record<string, unknown>;

/** The fields of an ENDPOINTS entry that locate a class in the JSON Schema. */
export type FormEndpoint = { key: string; type?: string; byo?: string };

/** One endpoint's records, in the shape dataState keeps them. */
export type RecordList = { key: string; items?: NexusRecord[] };

// The app fills these slots in itself, so the form leaves them out. The dates
// are stamped when the record is seeded, and the taxonomy follows the taxonomy
// file chosen above the generated fields.
export const APP_MANAGED_SLOTS = [
  "dateCreated",
  "dateModified",
  "isDefinedByTaxonomy",
];

// The class designator is filled in from the endpoint and shown read-only.
export const READ_ONLY_SLOTS = ["type"];

const DEFS_PREFIX = "#/$defs/";
const ANY_REF = `${DEFS_PREFIX}Any`;

let jsonSchemaCache: JsonObject | undefined;
let jsonSchemaRequest: Promise<JsonObject> | undefined;

/** The JSON Schema, when an earlier call to loadJsonSchema has fetched it. */
export function cachedJsonSchema(): JsonObject | undefined {
  return jsonSchemaCache;
}

/**
 * Fetches the JSON Schema the app already loads at start-up. The browser's
 * cached copy is used when there is one, and the result is kept so that every
 * form opened afterwards can build its fields at once.
 */
export function loadJsonSchema(): Promise<JsonObject> {
  jsonSchemaRequest ??= fetch(SCHEMA_FILE_JSON, { cache: "force-cache" })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`Failed to fetch ${SCHEMA_FILE_JSON}`);
      }
      return response.json() as Promise<JsonObject>;
    })
    .then((schema) => (jsonSchemaCache = schema));
  jsonSchemaRequest.catch(() => {
    // Let the next form try again rather than keep the failed request.
    jsonSchemaRequest = undefined;
  });
  return jsonSchemaRequest;
}

/**
 * Registers the two formats gen-jsonschema writes into this schema. Without
 * ajv-formats, ajv would skip both with a warning; these simple checks need no
 * extra package. A URI starts with a scheme, and a date is written YYYY-MM-DD.
 */
export function addSchemaFormats(ajv: Ajv): Ajv {
  return ajv
    .addFormat("uri", /^[a-z][a-z0-9+.-]*:/i)
    .addFormat("date", /^\d{4}-\d{2}-\d{2}$/);
}

function isObject(value: unknown): value is JsonObject {
  return typeof value === "object" && value !== null && !Array.isArray(value);
}

function definitionName(ref: unknown): string | undefined {
  return typeof ref === "string" && ref.startsWith(DEFS_PREFIX)
    ? ref.slice(DEFS_PREFIX.length)
    : undefined;
}

function allowsType(type: unknown, name: string): boolean {
  return type === name || (Array.isArray(type) && type.includes(name));
}

/**
 * Finds the class an endpoint edits the same way utils/schema.ts finds its
 * fields: by the endpoint's class name in $defs, or else through the items of
 * the Container slot that holds the endpoint's records.
 */
export function findClassName(
  jsonSchema: JsonObject,
  endpoint: FormEndpoint,
): string | undefined {
  const defs = isObject(jsonSchema.$defs) ? jsonSchema.$defs : {};
  const hasProperties = (name: string | undefined): name is string => {
    const definition = name === undefined ? undefined : defs[name];
    return isObject(definition) && isObject(definition.properties);
  };

  const direct = endpoint.type || endpoint.key;
  if (hasProperties(direct)) {
    return direct;
  }
  const container = isObject(defs.Container) ? defs.Container : {};
  const slots = isObject(container.properties) ? container.properties : {};
  const slot = slots[endpoint.byo || endpoint.key];
  const items = isObject(slot) && isObject(slot.items) ? slot.items : undefined;
  if (items === undefined) {
    return undefined;
  }
  const candidates = Array.isArray(items.anyOf) ? items.anyOf : [items];
  for (const candidate of candidates) {
    const name = isObject(candidate)
      ? definitionName(candidate.$ref)
      : undefined;
    if (hasProperties(name)) {
      return name;
    }
  }
  return undefined;
}

// The type of a branch that says nothing except its type and description.
function plainBranchType(branch: unknown): unknown {
  if (!isObject(branch)) {
    return undefined;
  }
  const keys = Object.keys(branch).filter((key) => key !== "description");
  return keys.length === 1 && keys[0] === "type" ? branch.type : undefined;
}

/**
 * Rewrites one slot's schema into a shape the form can render. A slot whose
 * range is linkml:Any refers to the Any definition, which allows every JSON
 * type; @sjsf would take the first type after null and draw a checkbox, while
 * the records hold identifiers, so such a slot becomes a string. A union whose
 * branches are all strings, which a slot ranging over several classes that are
 * not inlined produces, becomes a plain string as well.
 */
export function normaliseSlot(schema: unknown): unknown {
  if (!isObject(schema)) {
    return schema;
  }
  if (schema.$ref === ANY_REF) {
    const { $ref: _ref, ...rest } = schema;
    return { ...rest, type: "string" };
  }
  const result: JsonObject = { ...schema };
  if (isObject(result.items)) {
    result.items = normaliseSlot(result.items);
  }
  if (isObject(result.properties)) {
    result.properties = Object.fromEntries(
      Object.entries(result.properties).map(([key, value]) => [
        key,
        normaliseSlot(value),
      ]),
    );
  }
  if (Array.isArray(result.anyOf)) {
    const branches = result.anyOf.map(normaliseSlot);
    const types = branches.map(plainBranchType);
    if (types.every((type) => type === "string" || type === "null")) {
      delete result.anyOf;
      result.type =
        types.includes("null") || allowsType(result.type, "null")
          ? ["string", "null"]
          : "string";
    } else {
      result.anyOf = branches;
    }
  }
  return result;
}

// Adds the definitions a schema refers to, and those they refer to in turn.
function collectDefinitions(
  node: unknown,
  defs: JsonObject,
  found: JsonObject,
): void {
  if (Array.isArray(node)) {
    node.forEach((item) => collectDefinitions(item, defs, found));
    return;
  }
  if (!isObject(node)) {
    return;
  }
  const name = definitionName(node.$ref);
  if (name !== undefined && !(name in found) && isObject(defs[name])) {
    found[name] = normaliseSlot(defs[name]);
    collectDefinitions(found[name], defs, found);
  }
  for (const [key, value] of Object.entries(node)) {
    if (key !== "$ref") {
      collectDefinitions(value, defs, found);
    }
  }
}

// Offers suggested values as examples, which the theme's text inputs show as
// a datalist. Examples are annotations, so a value outside the list is still
// valid. A list slot carries the suggestions on its items.
function withSuggestions(
  schema: unknown,
  values: string[] | undefined,
): unknown {
  if (!isObject(schema) || values === undefined || values.length === 0) {
    return schema;
  }
  const examples = [...new Set(values)];
  if (isObject(schema.items)) {
    return allowsType(schema.items.type, "string")
      ? { ...schema, items: { ...schema.items, examples } }
      : schema;
  }
  return allowsType(schema.type, "string") ? { ...schema, examples } : schema;
}

export type FormSchemaOptions = {
  /** Slots the form leaves out. */
  hidden?: string[];
  /** Slots shown but not editable. */
  readOnly?: string[];
  /** Values to suggest per slot. */
  suggestions?: Record<string, string[]>;
};

// A read-only slot keeps its value whatever it is. The class designator is the
// case in point: the endpoint for groups also lists RiskGroup and AiTaskGroup
// records, whose type the Group definition's one-value enum would reject, so
// the enum goes and the slot is marked readOnly instead.
function asReadOnly(schema: unknown): unknown {
  if (!isObject(schema)) {
    return schema;
  }
  const { enum: _enum, ...rest } = schema;
  return { ...rest, readOnly: true };
}

/**
 * Builds the schema the form renders for one endpoint's class, or returns
 * undefined when the JSON Schema has no such class. The class definition is
 * copied without the hidden slots, and the definitions it refers to come along
 * under $defs, where @sjsf and ajv resolve each $ref with this schema as the
 * root.
 *
 * additionalProperties is left out on purpose. A record can hold keys its class
 * does not declare, such as _filenameKey, and those must neither fail
 * validation nor turn into editable fields.
 */
export function buildFormSchema(
  jsonSchema: JsonObject,
  endpoint: FormEndpoint,
  options: FormSchemaOptions = {},
): Schema | undefined {
  const name = findClassName(jsonSchema, endpoint);
  if (name === undefined) {
    return undefined;
  }
  const defs = jsonSchema.$defs as JsonObject;
  const definition = defs[name] as JsonObject;
  const hidden = new Set(options.hidden ?? []);
  const readOnly = new Set(options.readOnly ?? []);

  const properties: JsonObject = {};
  for (const [slot, slotSchema] of Object.entries(
    definition.properties as JsonObject,
  )) {
    if (hidden.has(slot)) {
      continue;
    }
    const normalised = normaliseSlot(slotSchema);
    properties[slot] = readOnly.has(slot)
      ? asReadOnly(normalised)
      : withSuggestions(normalised, options.suggestions?.[slot]);
  }

  const schema: JsonObject = { title: name, type: "object", properties };
  const required = Array.isArray(definition.required)
    ? definition.required.filter(
        (slot): slot is string =>
          typeof slot === "string" && slot in properties,
      )
    : [];
  if (required.length > 0) {
    schema.required = required;
  }
  const found: JsonObject = {};
  collectDefinitions(properties, defs, found);
  if (Object.keys(found).length > 0) {
    schema.$defs = found;
  }
  return schema as Schema;
}

/** A UI schema for the form's root: never a bare $ref, so slots can be read. */
export type FormUiSchema = UiSchema & {
  "ui:globalOptions"?: ResolvableUiOptions;
};

export type UiSchemaOptions = {
  /** The slot order the cards use; slots not listed follow in schema order. */
  order: string[];
  /** Slots edited in a textarea. */
  textarea: string[];
};

/**
 * Builds the UI schema: the slot order, the slots edited in a textarea, and a
 * title for each slot that is only a $ref. Such a slot would otherwise be
 * labelled with the title of the enumeration it points at, and the form labels
 * every field with its slot name, as the hand-built form did.
 */
export function buildUiSchema(
  schema: Schema,
  options: UiSchemaOptions,
): FormUiSchema {
  const properties = schema.properties ?? {};
  const slots = Object.keys(properties);
  const uiSchema: FormUiSchema = {
    "ui:options": {
      order: [...options.order.filter((slot) => slots.includes(slot)), "*"],
    },
    // The lists hold identifiers whose order carries no meaning, so their
    // items get a remove button but no move buttons.
    "ui:globalOptions": { orderable: false },
  };
  for (const slot of slots) {
    const slotSchema = properties[slot];
    if (isObject(slotSchema) && typeof slotSchema.$ref === "string") {
      uiSchema[slot] = { "ui:options": { title: slot } };
    }
  }
  for (const slot of options.textarea) {
    if (slots.includes(slot)) {
      uiSchema[slot] = { "ui:components": { textWidget: "textareaWidget" } };
    }
  }
  return uiSchema;
}

/**
 * Seeds the record to edit exactly as the hand-built form did: a new record
 * goes to the default taxonomy file, the class designator comes from the
 * endpoint, the taxonomy follows the file, and the dates are stamped.
 */
export function seedRecord(
  record: NexusRecord | null | undefined,
  mode: string,
  displayFields: string[],
  endpointType: string | undefined,
  today: string,
): NexusRecord {
  const seeded: NexusRecord = record ? { ...record } : {};
  if (mode === "add" && !seeded._filenameKey) {
    seeded._filenameKey = YOUR_DEFAULT_DATA_FILE;
  }
  if (displayFields.includes("type") && !seeded.type && endpointType) {
    seeded.type = endpointType;
  }
  if (displayFields.includes("isDefinedByTaxonomy") && seeded._filenameKey) {
    seeded.isDefinedByTaxonomy = seeded._filenameKey;
  }
  if (
    mode === "add" &&
    displayFields.includes("dateCreated") &&
    !seeded.dateCreated
  ) {
    seeded.dateCreated = today;
  }
  if (
    (mode === "add" || mode === "edit") &&
    displayFields.includes("dateModified")
  ) {
    seeded.dateModified = today;
  }
  return seeded;
}

/** The part of a record the form edits: the slots its schema declares. */
export function formValueOf(record: NexusRecord, schema: Schema): NexusRecord {
  const slots = Object.keys(schema.properties ?? {});
  return Object.fromEntries(
    Object.entries(record).filter(([key]) => slots.includes(key)),
  );
}

/**
 * Records the taxonomy file the record is saved to. A class with an
 * isDefinedByTaxonomy slot takes the file as its taxonomy too, as the hand-built
 * form did when the file was chosen.
 */
export function applyTaxonomyFile(
  record: NexusRecord,
  filenameKey: string | undefined,
  linksTaxonomy: boolean,
): NexusRecord {
  if (!filenameKey) {
    return record;
  }
  const result: NexusRecord = { ...record, _filenameKey: filenameKey };
  if (linksTaxonomy) {
    result.isDefinedByTaxonomy = filenameKey;
  }
  return result;
}

function isEmptyValue(value: unknown): boolean {
  return (
    value === undefined ||
    value === null ||
    value === "" ||
    (Array.isArray(value) && value.length === 0)
  );
}

/**
 * Merges the submitted form value into the seeded record. Keys the form does
 * not edit keep their seeded values. A slot the record did not have stays out
 * when the form left it empty, so saving does not add empty keys that the form
 * filled in as defaults; a slot the user cleared is kept, and the save path
 * turns its empty value into an empty string as before.
 */
export function buildSavedRecord(
  seeded: NexusRecord,
  submitted: Record<string, unknown>,
  schema: Schema,
): NexusRecord {
  const record: NexusRecord = { ...seeded };
  for (const slot of Object.keys(schema.properties ?? {})) {
    const value = submitted[slot];
    if (isEmptyValue(value) && !(slot in seeded)) {
      continue;
    }
    record[slot] = value;
  }
  return record;
}

export type SuggestionContext = {
  /** The endpoint whose records each slot points at. */
  fieldEndpoints: Record<string, string>;
  /** Records loaded from the API, as dataState.items. */
  items: RecordList[];
  /** Records loaded from your files, as dataState.yourItems. */
  yourItems: RecordList[];
  /** The endpoint being edited. */
  endpoint: string;
  /** The record being edited, which is not offered as its own relation. */
  currentId?: string;
  /** When set, only records of this taxonomy are offered. */
  taxonomy?: string;
};

function recordsOf(lists: RecordList[], key: string): NexusRecord[] {
  return lists.find((list) => list.key === key)?.items ?? [];
}

function stringsOf(value: unknown): string[] {
  const values = Array.isArray(value) ? value : [value];
  return values.filter(
    (item): item is string => typeof item === "string" && item !== "",
  );
}

/**
 * The values to suggest for one slot, chosen as the hand-built form chose its
 * dropdown options: the identifiers of the records at the endpoint the slot
 * points at, from the API and from your files. When that endpoint has no
 * records, the values the slot already holds across the current endpoint are
 * offered instead.
 */
export function suggestedValues(
  slot: string,
  context: SuggestionContext,
): string[] {
  const target = context.fieldEndpoints[slot];
  if (target === undefined) {
    return [];
  }
  const records = [
    ...recordsOf(context.items, target),
    ...recordsOf(context.yourItems, `${target}&byod`),
  ];
  if (records.length === 0) {
    const current = [
      ...recordsOf(context.items, context.endpoint),
      ...recordsOf(context.yourItems, `${context.endpoint}&byod`),
    ];
    return [...new Set(current.flatMap((record) => stringsOf(record[slot])))];
  }
  const ids = records
    .filter(
      (record) =>
        typeof record.id === "string" &&
        record.id !== "" &&
        record.id !== context.currentId &&
        (context.taxonomy === undefined ||
          record.isDefinedByTaxonomy === context.taxonomy),
    )
    .map((record) => record.id as string);
  return [...new Set(ids)];
}
