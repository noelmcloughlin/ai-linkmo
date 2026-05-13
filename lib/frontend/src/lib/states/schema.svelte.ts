// lib/frontend/src/lib/states/schema.svelte.ts
import type { EndpointFieldDescriptions, FieldStringMap } from "$types/schema";

// Manage schema fields from endpoints.
class SchemaState {
  // SchemaFields is only used within SchemaState
  private static SchemaFields = class {
    fieldDescriptions: EndpointFieldDescriptions;
    fieldTypes: FieldStringMap;
    displayFields: string[];
    includesTaxonomyField: boolean;
    constructor() {
      this.fieldDescriptions = {};
      this.fieldTypes = {};
      this.displayFields = [];
      this.includesTaxonomyField = false;
    }
  };

  fieldDescriptions: EndpointFieldDescriptions = $state({});
  endpoints: { [key: string]: InstanceType<typeof SchemaState.SchemaFields> } = $state({});

  addEndpoint(ep: string, schema: InstanceType<typeof SchemaState.SchemaFields>) {
    if (!this.endpoints[ep]) {
      this.endpoints[ep] = schema;
    }
  }

  setDescriptions(descriptions: EndpointFieldDescriptions = {}) {
  this.fieldDescriptions = { ...this.fieldDescriptions, ...descriptions };
}
}
export const schemaState = new SchemaState();