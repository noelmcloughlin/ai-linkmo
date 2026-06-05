import type { FieldType } from "$types/ui";

/**
 * Maps an endpoint key to its array of FieldType objects.
 */
export type SchemaFields = Record<string, FieldType[]>;

/**
 * Maps a field key to a string value (e.g., description or type).
 */
export type FieldStringMap = Record<string, string>;

/**
 * A generic string-keyed string dictionary.
 */
export type StringDict = { [key: string]: string };

/**
 * Result of mapping FieldType[] to descriptions, types, and keys.
 */
export type MappedFieldObjs = {
  fieldDescriptions: FieldStringMap;
  fieldTypes: FieldStringMap;
  allFields: Record<string, FieldType[]>;
};

/**
 * Computed schema fields and display order for an endpoint.
 */
export type ComputedSchemaFields = {
  fieldDescriptions: FieldStringMap;
  fieldTypes: FieldStringMap;
  displayFields: string[];
  includesTaxonomyField: boolean;
};

/**
 * Maps an endpoint key to its mapping of field keys to descriptions
 * (or other string values).
 */
export type EndpointFieldDescriptions = Record<string, FieldStringMap>;

/**
 * Shape used to initialize schemaState across all endpoints and to set
 * descriptions. Handles notification on error/success in the caller.
 */
export type SchemaStateType = {
  fieldDescriptions: FieldStringMap;
  endpoints: Record<string, ComputedSchemaFields>;
  addEndpoint: (key: string, value: ComputedSchemaFields) => void;
  setDescriptions: (descriptions: EndpointFieldDescriptions) => void;
};
