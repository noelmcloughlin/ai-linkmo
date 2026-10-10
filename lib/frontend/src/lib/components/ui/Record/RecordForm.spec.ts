// Renders RecordForm on the server, in node, from the JSON Schema the app
// serves, to check what the generated form shows for an endpoint's class.
// Clicks and typing need a browser, so what saving produces is tested on the
// helpers in utils/recordForm.spec.ts.
import { describe, it, expect, beforeAll, beforeEach, vi } from "vitest";
import { readFileSync } from "node:fs";
import { render } from "svelte/server";
import RecordForm from "./RecordForm.svelte";
import { dataState } from "$states/data.svelte";
import { endpoint } from "$states/endpoint.svelte";
import { computeSchemaFieldsAndDisplayOrder } from "$utils/schema";
import { loadJsonSchema } from "$utils/recordForm";
import type { FieldType } from "$types/ui";

const schemaText = readFileSync(
  new URL(
    "../../../../../static/schema/ai-risk-ontology.json",
    import.meta.url,
  ),
  "utf8",
);
const defs = JSON.parse(schemaText).$defs;

// The fieldSchema CardHolder passes, computed from the class as utils/schema.ts
// computes it at start-up.
function fieldSchemaFor(endpointKey: string, className: string) {
  const fields: FieldType[] = Object.entries(defs[className].properties).map(
    ([key, value]) => ({ key, value: value as FieldType["value"] }),
  );
  return computeSchemaFieldsAndDisplayOrder(
    { [endpointKey]: fields },
    endpointKey,
  );
}

// The markup without the comments Svelte leaves for hydration.
function renderForm(props: Record<string, unknown>) {
  return render(RecordForm, { props }).body.replace(/<!--[^>]*-->/g, "");
}

beforeAll(async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response(schemaText)),
  );
  await loadJsonSchema();
  vi.unstubAllGlobals();
});

beforeEach(() => {
  endpoint.reset();
  dataState.reset();
});

describe("RecordForm", () => {
  it("renders the endpoint's class as generated fields", () => {
    endpoint.setCurrent("risk");
    const body = renderForm({
      fieldSchema: fieldSchemaFor("risk", "Risk"),
      mode: "add",
    });
    expect(body).toContain("Add New Record");
    expect(body).toMatch(/<label class="fieldset-legend" for="root_id">id \*/);
    expect(body).toContain('<textarea class="textarea');
    expect(body).toMatch(/<input value="Risk"[^>]*id="root_type"[^>]*readonly/);
    expect(body).not.toContain('id="root_dateCreated"');
    expect(body).not.toContain('id="root_isDefinedByTaxonomy"');
    // The prominent slots come first, in the order the cards use.
    const order = ["root_id", "root_name", "root_description", "root_concern"];
    const positions = order.map((id) => body.indexOf(`for="${id}"`));
    expect(positions.every((p) => p >= 0)).toBe(true);
    expect([...positions].sort((a, b) => a - b)).toEqual(positions);
  });

  it("renders an enumeration as a select labelled by its slot", () => {
    endpoint.setCurrent("obligation");
    const body = renderForm({
      fieldSchema: fieldSchemaFor("obligation", "ControlActivityObligation"),
      mode: "add",
    });
    expect(body).toContain('for="root_hasRequirementType">hasRequirementType');
    expect(body).toContain(">PREVENTATIVE</option>");
  });

  it("keeps the designator of a subclass record", () => {
    endpoint.setCurrent("group");
    const body = renderForm({
      fieldSchema: fieldSchemaFor("group", "Group"),
      record: { id: "group-1", type: "RiskGroup" },
      mode: "edit",
    });
    expect(body).toMatch(/<input value="RiskGroup"[^>]*id="root_type"/);
  });

  it("offers related records as suggestions", () => {
    endpoint.setCurrent("risk");
    dataState.setItems([
      { key: "action", items: [{ id: "act-1" }, { id: "act-2" }] },
    ]);
    const body = renderForm({
      fieldSchema: fieldSchemaFor("risk", "Risk"),
      record: { id: "risk-1", hasRelatedAction: ["act-1"] },
      mode: "edit",
    });
    expect(body).toMatch(/<datalist id="root_hasRelatedAction_0__examples">/);
    expect(body).toContain('<option value="act-2">');
  });

  it("offers Delete only when editing with a delete handler", () => {
    endpoint.setCurrent("risk");
    const fieldSchema = fieldSchemaFor("risk", "Risk");
    const onDelete = () => {};
    expect(renderForm({ fieldSchema, mode: "edit", onDelete })).toContain(
      "Delete",
    );
    expect(renderForm({ fieldSchema, mode: "add", onDelete })).not.toContain(
      "Delete",
    );
    expect(renderForm({ fieldSchema, mode: "edit" })).not.toContain("Delete");
  });

  it("locks the taxonomy file once a record is being edited", () => {
    endpoint.setCurrent("risk");
    const fieldSchema = fieldSchemaFor("risk", "Risk");
    const select = /<select id="record-form-taxonomy-file"[^>]*>/;
    expect(
      renderForm({ fieldSchema, mode: "add" }).match(select)?.[0],
    ).not.toContain("disabled");
    expect(
      renderForm({ fieldSchema, record: { id: "r" }, mode: "edit" }).match(
        select,
      )?.[0],
    ).toContain("disabled");
  });
});
