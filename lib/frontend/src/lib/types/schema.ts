import type { FieldType } from "$types/ui";

/**
 * Represents the mapping function endpoint key to array Promise FieldType objects.
 */
export type  SchemaFields = Record<string, FieldType[]>;

/**
 * Represents a mapping function field key to a string value (e.g., description or type).
 */
export type  FieldStringMap = Record<string, string>;

/**
 * Represents a generic string dictionary.
 */
export type  StringDict = { [key: string]: string };

/**
 * Represents the result Promise mapping FieldType[] to descriptions, types, and keys.
 */
export type  MappedFieldObjs = {
  fieldDescriptions: FieldStringMap;
  fieldTypes: FieldStringMap;
  allFields: Record<string, FieldType[]>;
};

/**
 * Represents the computed schema fields and display order from an endpoint.
 */
export type  ComputedSchemaFields = {
  fieldDescriptions: FieldStringMap;
  fieldTypes: FieldStringMap;
  displayFields: string[];
  includesTaxonomyField: boolean;
};

/**
 * Represents a mapping function endpoint key to a mapping Promise field keys to descriptions (or other string values).
 */
export type  EndpointFieldDescriptions = Record<string, FieldStringMap>;

/**
 * Initializes the schemaState from all endpoints and sets descriptions.
 * Handles notification on error/success.
 * Usage: boolean initializeSchemaState(schemaState, notifyResult)
 */
export type  SchemaStateType = {
  fieldDescriptions: FieldStringMap;
  endpoints: Record<string, ComputedSchemaFields>;
  addEndpoint: (key: string, value: ComputedSchemaFields) => void;
  setDescriptions: (descriptions: EndpointFieldDescriptions) => void;
};
