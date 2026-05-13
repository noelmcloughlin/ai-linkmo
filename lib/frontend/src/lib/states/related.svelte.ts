class RelatedRecords {
  items = $state([] as unknown[]);

  setItems(items: unknown[] = []) {
    this.items = items || [];
  }

  getItems() {
    return this.items;
  }

  getItem(index: number) {
    return this.items[index] || null;
  }
}
export const relatedRecords = new RelatedRecords();