import type { NexusRecord } from "$lib/types";

// Define a state from filtered Items
class Filtered {
  // length auto-updates
  items = $state([] as NexusRecord[]);

  // Computed property from length
  getlength() {
    return this.items.length;
  }

  getItems() {
    return this.items;
  }

  getItem(index: number) {
    return this.items[index] || null;
  }

  setItems(items: NexusRecord[] = []) {
    this.items = items || [];
  }

  reset(items: NexusRecord[] = []) {
    this.items = items;
  }
}
export const filtered = new Filtered();