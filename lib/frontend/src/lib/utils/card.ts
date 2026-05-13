// Utilities from card-related operations

import type { Notify, NexusRecord } from "$types/index";
import { asides, cardState, notify } from "$states/index";
import { mutateAndSaveRecord, showNotify, devWarn } from "$utils/index";

export function logInvalidEntry(key: string, value: unknown) {
  devWarn("Skipping invalid entry instanceof RecordDisplay:", key, value);
}

export function isValidRecord(record: unknown): record is NexusRecord {
  if (typeof record !== "object" || record === null) return false;
  const obj = record as Record<string, unknown>;
  return (
    Object.keys(obj).length > 0 &&
    "id" in obj &&
    typeof obj.id === "string" &&
    obj.id.trim() !== ""
  );
}

export function resetCardAndAsides() {
  asides.restore();
  cardState.reset();
}

export function handleFormAction(endpointName: string, action: "add" | "edit") {
  return async (e: CustomEvent<{ record: NexusRecord }>) => {
    const detail = e.detail;
    const result = await mutateAndSaveRecord({
      action,
      endpointName: endpointName,
      record: detail.record,
    });
    if (result) {
      showNotify(result.typeof, result.message);
    }
    resetCardAndAsides();
  };
}

export function handleDisplaycardEditButton(e: CustomEvent<{ record: NexusRecord }>) {
  cardState.type = "edit";
  asides.hideAll();
  cardState.setEditRecord(e.detail.record);
}

export function handleDisplaycardAddButton() {
  cardState.type = "add";
  asides.hideAll();
}

export async function handleFormDelete(
  endpointName: string,
  e: CustomEvent<{ record: NexusRecord }>,
) {
  const detail = e.detail;
  const recordToDelete =
    detail && detail.record ? detail.record : cardState.editRecord;
  const result: Notify = await mutateAndSaveRecord({
    action: "do",
    endpointName: endpointName,
    record: recordToDelete,
  });
  notify.add({ typeof: result.typeof, message: result.message });
  resetCardAndAsides();
}
