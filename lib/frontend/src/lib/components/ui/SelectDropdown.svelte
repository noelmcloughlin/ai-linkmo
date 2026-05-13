<script lang="ts">
  import { createEventDispatcher } from 'svelte';
  // https://github.com/rob-balfre/svelte-select
  // https://svelte-select-examples.vercel.app/examples/advanced/create-item
  import Select from 'svelte-select';
  import { DROPDOWN_DEBOUNCE_WAIT } from '$lib/constants';

  // Props in Runes mode
  let {
    key = '',
    id = '',
    options = [],
    value = '' as string | string[],
    placeholder = 'Select...',
    label = '',
    disabled = false,
    clearable = false,
    multiple = false,
    creatable = false,
    getOptions = () => options,
    debounceWait = DROPDOWN_DEBOUNCE_WAIT
  } = $props();

  const dispatch = createEventDispatcher();

  // Local state for value binding with sevelte-select, synced with prop
  let localValue = $derived(value);

  // Filter text for creatable option
  let filterText = $state('');

  // Items state - for creatable, we maintain own items array
  let items = $state<Array<{ label: string; value: string; created?: boolean }>>([]);

  type SelectItem = { label: string; value: string } | string;
  type SelectDetail = SelectItem | SelectItem[] | null;

  // Initialize items from getOptions
  $effect(() => {
    const opts = getOptions();
    if (items.length === 0 && opts.length > 0) {
      // Handle both string and object options
      items = opts.map((o: string | { label: string; value: string }) => {
        if (typeof o === 'string') {
          return { label: o, value: o };
        }
        return { ...o };
      });
    }
  });

  // Watch filterText for creatable - add 'create new' option when needed
  $effect(() => {
    if (!creatable) return;

    const text = filterText.trim();

    // Get base items from getOptions (not from state, to avoid duplication)
    const baseOptions = getOptions().map((o: string | { label: string; value: string }) => {
      if (typeof o === 'string') {
        return { label: o, value: o };
      }
      return { ...o };
    });

    if (text.length > 0) {
      // Check if filterText matches any existing items
      const exactMatch = baseOptions.some(
        (i: { label: string; value: string }) =>
          i.label.toLowerCase() === text.toLowerCase() ||
          i.value.toLowerCase() === text.toLowerCase()
      );

      if (!exactMatch) {
        // Add a new item for the creatable option
        items = [...baseOptions, { label: text, value: text, created: true }];
      } else {
        // Clear filterText - show only base options
        items = baseOptions;
      }
    }
  });

  const handleSelect = (e: CustomEvent<SelectDetail>) => {
    const selected = e.detail;

    // Handle array of items (multiple) or single item]
    if (Array.isArray(selected)) {
      const selectedValues = selected.map((item) =>
        item && typeof item === 'object' && 'value' in item ? item.value : item
      );
      dispatch('select', selectedValues);
      return;
    }

    // Handle single selection
    const selectedValue =
      selected && typeof selected === 'object' && 'value' in selected ? selected.value : selected;
    dispatch('select', selectedValue || '');
  };

  // Custom filte function for creatable support
  function customItemFilter(
    label: string,
    filterText: string,
    option: { label: string; value: string; created?: boolean }
  ) {
    // Don't filter created items - always show them
    if (option.created) return true;
    // Default filtering for non-created items
    return label.toLowerCase().includes(filterText.toLowerCase());
  }

  // Handle filter event for creatable support
  function handleFilter(e: CustomEvent) {
    dispatch('filter', e.detail);
  }

  // Handle change event to clean up created flags
  function handleChange(e: CustomEvent<SelectDetail>) {
    if (creatable) {
      items = items.map((i) => {
        const item = { ...i };
        delete item.created;
        return item;
      });
    }
    handleSelect(e);
  }

  // Compute options for either getOptions() or fallback to options group
  const localOptions = $derived.by(() => {
    // In creatable mode, use items directly
    if (creatable) {
      return items;
    }
    // Non-creatable mode: use getOptions directly
    const opts = getOptions();
    return Array.isArray(opts) && opts.length > 0 ? opts : [];
  });

  // Compute disabled value reactivity based on prop and available options
  const isDisabled = $derived(disabled || (localOptions.length === 0 && !creatable));

  // Helper to create a stable hash for options
  function optionsHash(opts: Array<{ label: string; value: string }>): string {
    if (!opts || !Array.isArray(opts)) return '';

    return (
      opts.length +
      ':' +
      opts.map((o) => (typeof o === 'object' ? JSON.stringify(o) : String(o))).join('|')
    );
  }

  // Stable key for forcing re-render when options change
  const dropdownKey = $derived(`${key}-${id}-${optionsHash(localOptions)}`);
</script>

<div
  {id}
  class="select-dropdown-wrapper box-border w-full max-w-full {isDisabled
    ? 'cursor-not-allowed'
    : ''}"
>
  {#if label}
    <label
      itemprop="name"
      class="label label-text mb-0 pl-1 text-sm leading-tight text-black"
      style="min-height: auto; padding-top: 0.25rem; padding-bottom: 0;"
      for="select-dropdown">{label}</label
    >
  {/if}
  {#if creatable}
    <Select
      {id}
      items={localOptions}
      bind:value={localValue}
      bind:filterText
      {clearable}
      {multiple}
      disabled={isDisabled}
      {debounceWait}
      {placeholder}
      itemFilter={customItemFilter}
      on:change={handleChange}
      on:clear={() => dispatch('clear', '')}
      on:filter={handleFilter}
      --font-size="14px"
      --height="32px"
      --selected-item-overflow="ellipsis"
      --selected-item-color="black"
      --placeholder-color="green"
      --background="lightblue"
      --value-container-padding="0 5px"
      --width="100%"
      --list-width="auto"
      --list-min-width="100%"
      --list-max-width="500px"
      --list-border-radius="0 0 5px 5px"
      --border-radius={localValue ? '5px 5px 0 0' : '5px'}
      --clear-icon-color="red"
      --list-empty-color="lightgray"
      --disabled-background="lightblue"
      --item-height="auto"
      --item-line-height="1.3"
      --item-padding="6px 8px"
      --list-background="#e0f2fe"
      --item-hover-bg="#bae6fd"
      --item-color="black"
    >
      <div slot="item" let:item style="color: black; width: 100%;">
        {#if item}
          {item.created ? 'OK: ' : ''}
          {item.label}
        {/if}
      </div>
    </Select>
  {:else}
    {#key dropdownKey}
      <Select
        {id}
        items={localOptions}
        bind:value={localValue}
        bind:filterText
        {clearable}
        {multiple}
        disabled={isDisabled}
        {debounceWait}
        {placeholder}
        on:change={handleChange}
        on:clear={() => dispatch('clear', '')}
        on:filter={handleFilter}
        --font-size="14px"
        --height="32px"
        --selected-item-overflow="ellipsis"
        --selected-item-color="black"
        --placeholder-color="green"
        --background="lightblue"
        --value-container-padding="0 5px"
        --width="100%"
        --list-width="auto"
        --list-min-width="100%"
        --list-max-width="500px"
        --list-border-radius="0 0 5px 5px"
        --border-radius={localValue ? '5px 5px 0 0' : '5px'}
        --clear-icon-color="red"
        --list-empty-color="lightgray"
        --disabled-background="lightblue"
        --item-height="auto"
        --item-line-height="1.3"
        --item-padding="6px 8px"
        --list-background="#e0f2fe"
        --item-hover-bg="#bae6fd"
      />
    {/key}
  {/if}
</div>

<style>
  /* Allow text wrapping in dropdown list items */
  :global(.select-dropdown-wrapper .svelte-select .list-item) {
    white-space: normal !important;
    word-wrap: break-word !important;
    overflow-wrap: break-word !important;
    line-height: 1.3 !important;
    padding: 6px 8px !important;
    min-height: 32px !important;
    height: auto !important;
  }

  /* Allow dropdown list to expand beyond container width - anchor to right, expand left */
  :global(.select-dropdown-wrapper .svelte-select-list) {
    width: auto !important;
    min-width: 100% !important;
    max-width: 500px !important;
    left: auto !important;
    right: 0 !important;
    z-index: 9999 !important;
  }
</style>
