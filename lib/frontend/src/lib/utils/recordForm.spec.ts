import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { Ajv } from "ajv";
import { addFormComponents, createFormValidator } from "@sjsf/ajv8-validator";
import type { FormValue, Schema } from "@sjsf/form";
import { ENDPOINTS } from "$lib/constants";
import type { NexusRecord } from "$types/yaml";
import {
  APP_MANAGED_SLOTS,
  READ_ONLY_SLOTS,
  addSchemaFormats,
  applyTaxonomyFile,
  buildFormSchema,
  buildSavedRecord,
  buildUiSchema,
  findClassName,
  formValueOf,
  normaliseSlot,
  seedRecord,
  suggestedValues,
} from "./recordForm";

// The JSON Schema the app serves, as gen-jsonschema wrote it.
const jsonSchema = JSON.parse(
  readFileSync(
    new URL("../../../static/schema/ai-risk-ontology.json", import.meta.url),
    "utf8",
  ),
);

function endpointFor(key: string) {
  const found = ENDPOINTS.find((e) => e.key === key);
  if (!found) throw new Error(`No endpoint ${key}`);
  return found;
}

function formSchemaFor(
  key: string,
  suggestions: Record<string, string[]> = {},
): Schema {
  const schema = buildFormSchema(jsonSchema, endpointFor(key), {
    hidden: APP_MANAGED_SLOTS,
    readOnly: READ_ONLY_SLOTS,
    suggestions,
  });
  if (!schema) throw new Error(`No form schema for ${key}`);
  return schema;
}

function slotOf(schema: Schema, slot: string): Record<string, unknown> {
  return schema.properties?.[slot] as Record<string, unknown>;
}

// Validates as the form does on submit, with the ajv8 validator.
function errorsOf(schema: Schema, value: NexusRecord) {
  const validator = createFormValidator({
    ajvPlugins: (ajv) => addSchemaFormats(addFormComponents(ajv)),
  });
  const result = validator.validateFormValue(schema, value as FormValue);
  return "errors" in result && result.errors ? result.errors : [];
}

describe("findClassName", () => {
  it("finds an endpoint's class by its type", () => {
    expect(findClassName(jsonSchema, endpointFor("risk"))).toBe("Risk");
  });

  it("falls back to the items of the endpoint's Container slot", () => {
    expect(findClassName(jsonSchema, { key: "nothing", byo: "actions" })).toBe(
      "Action",
    );
    expect(findClassName(jsonSchema, { key: "nothing", byo: "groups" })).toBe(
      "RiskControlGroup",
    );
  });

  it("returns undefined when the schema has no such class", () => {
    expect(findClassName(jsonSchema, { key: "nothing" })).toBeUndefined();
  });
});

describe("normaliseSlot", () => {
  it("turns a reference to Any into a string", () => {
    expect(normaliseSlot({ $ref: "#/$defs/Any" })).toEqual({ type: "string" });
    expect(
      normaliseSlot({
        items: { $ref: "#/$defs/Any" },
        type: ["array", "null"],
      }),
    ).toEqual({ items: { type: "string" }, type: ["array", "null"] });
  });

  it("collapses a union of strings into one string type", () => {
    expect(
      normaliseSlot({
        items: {
          anyOf: [{ type: "string" }, { type: "string" }],
          type: "string",
        },
        type: ["array", "null"],
      }),
    ).toEqual({ items: { type: "string" }, type: ["array", "null"] });
    expect(
      normaliseSlot({
        anyOf: [{ $ref: "#/$defs/Any" }, { type: "null" }],
        description: "Domain",
      }),
    ).toEqual({ description: "Domain", type: ["string", "null"] });
  });

  it("leaves a reference to an enumeration alone", () => {
    const slot = { $ref: "#/$defs/AdapterType" };
    expect(normaliseSlot(slot)).toEqual(slot);
  });
});

describe("buildFormSchema", () => {
  it("copies the class without the slots the app manages", () => {
    const schema = formSchemaFor("risk");
    expect(schema.title).toBe("Risk");
    expect(schema.required).toEqual(["id"]);
    expect(schema.additionalProperties).toBeUndefined();
    for (const slot of APP_MANAGED_SLOTS) {
      expect(schema.properties).not.toHaveProperty(slot);
    }
    expect(schema.properties).toHaveProperty("name");
  });

  it("makes the class designator read-only and drops its enum", () => {
    const type = slotOf(formSchemaFor("group"), "type");
    expect(type.readOnly).toBe(true);
    expect(type).not.toHaveProperty("enum");
  });

  it("carries only the definitions its slots refer to", () => {
    expect(Object.keys(formSchemaFor("obligation").$defs ?? {}).sort()).toEqual(
      [
        "AIUC1ControlApplicationCategory",
        "AIUC1EvidenceCategory",
        "AIUC1RequirementType",
      ],
    );
    expect(formSchemaFor("risk").$defs).toBeUndefined();
  });

  it("builds every endpoint's class with no reference to Any left", () => {
    for (const endpoint of ENDPOINTS) {
      const schema = formSchemaFor(endpoint.key);
      expect(JSON.stringify(schema)).not.toContain("#/$defs/Any");
    }
  });

  it("offers suggestions on list items and on single strings", () => {
    const schema = formSchemaFor("risk", {
      hasRelatedAction: ["act-1", "act-1", "act-2"],
      isPartOf: ["group-1"],
      type: ["Other"],
    });
    const related = slotOf(schema, "hasRelatedAction");
    expect(related.items).toEqual({
      type: "string",
      examples: ["act-1", "act-2"],
    });
    expect(slotOf(schema, "isPartOf").examples).toEqual(["group-1"]);
    expect(slotOf(schema, "type")).not.toHaveProperty("examples");
  });
});

describe("buildUiSchema", () => {
  const options = {
    order: ["id", "name", "notASlot", "description"],
    textarea: ["description", "concern"],
  };

  it("orders the prominent slots first and the rest after them", () => {
    const uiSchema = buildUiSchema(formSchemaFor("risk"), options);
    expect(uiSchema["ui:options"]?.order).toEqual([
      "id",
      "name",
      "description",
      "*",
    ]);
    expect(uiSchema["ui:globalOptions"]).toEqual({ orderable: false });
  });

  it("edits the long text slots in a textarea", () => {
    const uiSchema = buildUiSchema(formSchemaFor("risk"), options);
    expect(uiSchema.description).toEqual({
      "ui:components": { textWidget: "textareaWidget" },
    });
    expect(uiSchema.concern).toEqual({
      "ui:components": { textWidget: "textareaWidget" },
    });
  });

  it("labels a slot that is only a $ref with the slot's name", () => {
    const uiSchema = buildUiSchema(formSchemaFor("obligation"), options);
    expect(uiSchema.hasRequirementType).toEqual({
      "ui:options": { title: "hasRequirementType" },
    });
  });
});

describe("validation of the form schema", () => {
  it("accepts a seeded record, keys outside the class included", () => {
    const record = {
      id: "risk-1",
      name: "A risk",
      type: "Risk",
      hasRelatedAction: ["act-1"],
      _filenameKey: "finos-aigf",
      author: "someone",
    };
    expect(errorsOf(formSchemaFor("risk"), record)).toEqual([]);
  });

  it("accepts the designator of a subclass listed under its parent", () => {
    const record = { id: "group-1", type: "RiskGroup" };
    expect(errorsOf(formSchemaFor("group"), record)).toEqual([]);
  });

  it("reports a missing identifier and a malformed URI on their slots", () => {
    const paths = errorsOf(formSchemaFor("risk"), {
      name: "No id",
      url: "not a uri",
    }).map((error) => error.path);
    expect(paths).toContainEqual(["id"]);
    expect(paths).toContainEqual(["url"]);
  });

  it("checks the date and uri formats the schema uses", () => {
    const ajv = addSchemaFormats(new Ajv());
    const isDate = ajv.compile({ type: "string", format: "date" });
    const isUri = ajv.compile({ type: "string", format: "uri" });
    expect(isDate("2026-10-10")).toBe(true);
    expect(isDate("10/10/2026")).toBe(false);
    expect(isUri("https://example.org/a")).toBe(true);
    expect(isUri("Paul/XSTest")).toBe(false);
  });
});

describe("seedRecord", () => {
  const fields = [
    "id",
    "type",
    "isDefinedByTaxonomy",
    "dateCreated",
    "dateModified",
  ];

  it("seeds a new record as the hand-built form did", () => {
    expect(seedRecord({}, "add", fields, "Risk", "2026-10-10")).toEqual({
      _filenameKey: "finos-aigf",
      type: "Risk",
      isDefinedByTaxonomy: "finos-aigf",
      dateCreated: "2026-10-10",
      dateModified: "2026-10-10",
    });
  });

  it("keeps an edited record's values and stamps the modification date", () => {
    const record = {
      id: "risk-1",
      type: "RiskGroup",
      dateCreated: "2025-01-01",
    };
    expect(seedRecord(record, "edit", fields, "Group", "2026-10-10")).toEqual({
      id: "risk-1",
      type: "RiskGroup",
      dateCreated: "2025-01-01",
      dateModified: "2026-10-10",
    });
  });

  it("stamps only the slots the class has", () => {
    expect(
      seedRecord({ id: "x" }, "add", ["id"], "Risk", "2026-10-10"),
    ).toEqual({ id: "x", _filenameKey: "finos-aigf" });
  });
});

describe("merging the submitted value", () => {
  const schema = formSchemaFor("risk");

  it("gives the form only the slots it renders", () => {
    const value = formValueOf(
      { id: "r", name: "n", _filenameKey: "f", dateCreated: "2025-01-01" },
      schema,
    );
    expect(value).toEqual({ id: "r", name: "n" });
  });

  it("keeps what the form does not edit and takes what it does", () => {
    const seeded = {
      id: "r",
      name: "Old",
      concern: "Gone",
      _filenameKey: "f",
      dateCreated: "2025-01-01",
    };
    const submitted = {
      id: "r",
      name: "New",
      concern: undefined,
      hasRelatedAction: [],
      phase: undefined,
    };
    // toStrictEqual, because the cleared slot must stay as a key.
    expect(buildSavedRecord(seeded, submitted, schema)).toStrictEqual({
      id: "r",
      name: "New",
      concern: undefined,
      _filenameKey: "f",
      dateCreated: "2025-01-01",
    });
  });

  it("saves to the chosen taxonomy file", () => {
    expect(applyTaxonomyFile({ id: "r" }, "eu_ai_act", true)).toEqual({
      id: "r",
      _filenameKey: "eu_ai_act",
      isDefinedByTaxonomy: "eu_ai_act",
    });
    expect(applyTaxonomyFile({ id: "r" }, "eu_ai_act", false)).toEqual({
      id: "r",
      _filenameKey: "eu_ai_act",
    });
    expect(applyTaxonomyFile({ id: "r" }, "", true)).toEqual({ id: "r" });
  });
});

describe("suggestedValues", () => {
  const context = {
    fieldEndpoints: { hasRelatedAction: "action", isPartOf: "group" },
    items: [
      {
        key: "action",
        items: [
          { id: "act-1", isDefinedByTaxonomy: "t1" },
          { id: "act-2", isDefinedByTaxonomy: "t2" },
        ],
      },
      {
        key: "risk",
        items: [
          { id: "risk-1", isPartOf: "group-a" },
          { id: "risk-2", isPartOf: ["group-b", "group-a"] },
        ],
      },
    ],
    yourItems: [
      {
        key: "action&byod",
        items: [{ id: "act-3" }, { id: "act-1" }],
      },
    ],
    endpoint: "risk",
  };

  it("offers the identifiers at the endpoint a slot points at", () => {
    expect(suggestedValues("hasRelatedAction", context)).toEqual([
      "act-1",
      "act-2",
      "act-3",
    ]);
  });

  it("leaves out the record being edited and other taxonomies", () => {
    expect(
      suggestedValues("hasRelatedAction", { ...context, currentId: "act-2" }),
    ).toEqual(["act-1", "act-3"]);
    expect(
      suggestedValues("hasRelatedAction", { ...context, taxonomy: "t1" }),
    ).toEqual(["act-1"]);
  });

  it("falls back to the values the slot already holds", () => {
    expect(suggestedValues("isPartOf", context)).toEqual([
      "group-a",
      "group-b",
    ]);
  });

  it("offers nothing for a slot that points nowhere", () => {
    expect(suggestedValues("name", context)).toEqual([]);
  });
});
