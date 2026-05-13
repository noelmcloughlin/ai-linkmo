// Define the state from card operations

import type { NexusRecord} from "$types/yaml";

class CardState {
  // "add", "edit", "display", "notify"
  type: "add" | "edit" | "display" | "notify" = $state("display");
  item = $state(0);
  editRecord = $state<NexusRecord>({ id: "" });

  setEditRecord(record: NexusRecord = { id: "" } as NexusRecord) {
    this.editRecord = record;
  }

  setType(type: "add" | "edit" | "display" | "notify") {
    this.type = type;
  }

  reset() {
    this.type = "display";
    this.editRecord = {} as NexusRecord;
  }
}
export const cardState = new CardState();