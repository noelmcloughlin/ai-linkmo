// Drives RecordForm in Chromium: it fills the generated fields, presses the
// buttons, and reads what the form hands to its callers. The JSON Schema comes
// from static/, which the test server serves as the app's server does.
import { page } from "vitest/browser";
import { beforeEach, describe, expect, it, vi, type Mock } from "vitest";
import { render } from "vitest-browser-svelte";
import RecordForm from "./RecordForm.svelte";
import { dataState } from "$states/data.svelte";
import { endpoint } from "$states/endpoint.svelte";
import { computeSchemaFieldsAndDisplayOrder } from "$utils/schema";
import type { FieldType } from "$types/ui";
import type { NexusRecord } from "$types/yaml";

const today = new Date().toISOString().split("T")[0];

// The fieldSchema CardHolder passes, computed as utils/schema.ts computes it.
async function fieldSchemaFor(endpointKey: string, className: string) {
  const response = await fetch("/schema/ai-risk-ontology.json");
  const jsonSchema = await response.json();
  const definition = jsonSchema.$defs[className];
  const fields: FieldType[] = Object.entries(definition.properties).map(
    ([key, value]) => ({ key, value: value as FieldType["value"] }),
  );
  return computeSchemaFieldsAndDisplayOrder(
    { [endpointKey]: fields },
    endpointKey,
  );
}

function savedRecord(onSave: Mock): NexusRecord {
  return onSave.mock.calls[0][0].detail.record;
}

beforeEach(() => {
  endpoint.reset();
  dataState.reset();
});

describe("RecordForm in the browser", () => {
  it("saves a new record with the slots the app fills in", async () => {
    endpoint.setCurrent("risk");
    const onSave = vi.fn();
    render(RecordForm, {
      fieldSchema: await fieldSchemaFor("risk", "Risk"),
      mode: "add",
      onSave,
    });

    const id = page.getByRole("textbox", { name: /^id/ });
    await expect.element(id).toBeInTheDocument();
    await id.fill("risk-new");
    await page.getByRole("textbox", { name: /^name/ }).fill("A new risk");
    await page.getByRole("button", { name: "Save" }).click();

    await vi.waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(savedRecord(onSave)).toEqual({
      id: "risk-new",
      name: "A new risk",
      type: "Risk",
      _filenameKey: "finos-aigf",
      isDefinedByTaxonomy: "finos-aigf",
      dateCreated: today,
      dateModified: today,
    });
  });

  it("shows a missing identifier instead of saving", async () => {
    endpoint.setCurrent("risk");
    const onSave = vi.fn();
    render(RecordForm, {
      fieldSchema: await fieldSchemaFor("risk", "Risk"),
      mode: "add",
      onSave,
    });

    await expect
      .element(page.getByRole("textbox", { name: /^id/ }))
      .toBeInTheDocument();
    await page.getByRole("button", { name: "Save" }).click();

    await expect
      .element(page.getByText("must have required property 'id'"))
      .toBeInTheDocument();
    expect(onSave).not.toHaveBeenCalled();
  });

  it("keeps what the form does not show when an edit is saved", async () => {
    endpoint.setCurrent("group");
    const onSave = vi.fn();
    const record = {
      id: "group-1",
      name: "Old",
      type: "RiskGroup",
      _filenameKey: "eu_ai_act",
      isDefinedByTaxonomy: "eu_ai_act",
      dateCreated: "2025-01-01",
      author: "someone",
    };
    render(RecordForm, {
      fieldSchema: await fieldSchemaFor("group", "Group"),
      record,
      mode: "edit",
      onSave,
    });

    const name = page.getByRole("textbox", { name: /^name/ });
    await expect.element(name).toHaveValue("Old");
    await name.fill("New");
    await page.getByRole("button", { name: "Save" }).click();

    await vi.waitFor(() => expect(onSave).toHaveBeenCalledOnce());
    expect(savedRecord(onSave)).toEqual({
      ...record,
      name: "New",
      dateModified: today,
    });
  });

  it("cancels, and offers Delete when editing", async () => {
    endpoint.setCurrent("risk");
    const onCancel = vi.fn();
    const onDelete = vi.fn();
    render(RecordForm, {
      fieldSchema: await fieldSchemaFor("risk", "Risk"),
      record: { id: "risk-1" },
      mode: "edit",
      onCancel,
      onDelete,
    });

    await page.getByRole("button", { name: "Cancel" }).click();
    await page.getByRole("button", { name: "Delete" }).click();
    expect(onCancel).toHaveBeenCalledOnce();
    expect(onDelete).toHaveBeenCalledOnce();
  });
});
