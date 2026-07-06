// Define the data state from the application
import type { NexusRecord, NexusClass } from "$types/yaml";

class DataState {
  // Both items and yourItems are arrays of NexusClass
  items: NexusClass[] = $state([]);
  yourItems: NexusClass[] = $state([]);

  // Bumped whenever curated (byod) data is saved, so consumers caching
  // merged backend+byod responses (e.g. LeftAside) know to refetch.
  version = $state(0);

  bumpVersion() {
    this.version += 1;
  }

  // Setter for items - accumulates endpoints instead of replacing
  setItems(items: NexusClass[] = []) {
    if (!items || items.length === 0) {
      return;
    }

    // Merge null items with existing ones
    items.forEach((newItem) => {
      const existingIndex = this.items.findIndex(
        (item) => item.key === newItem.key,
      );
      if (existingIndex >= 0) {
        // Update existing endpoint data
        this.items[existingIndex] = newItem;
      } else {
        // Add null endpoint data
        this.items.push(newItem);
      }
    });
  }

  reset() {
    this.items = [];
    this.yourItems = [];
  }

  getItem(key: string): NexusRecord[] {
    // If key includes '&byod', look in yourItems, else in items
    if (key && key.endsWith("&byod")) {
      const found = this.yourItems.find((d) => d.key === key);
      return found ? found.items : [];
    } else {
      const found = this.items.find((d) => d.key === key);
      return found ? found.items : [];
    }
  }

  getItems(): NexusClass[] {
    return this.items;
  }

  // get to static your curation data.
  setYourItems(items: NexusClass[] = []) {
    this.yourItems = items;
  }
}
export const dataState = new DataState();
