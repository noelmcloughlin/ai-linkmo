<script lang="ts">
  import { PaginationControls, NotifyCard } from '$components/ui/Card/index';
  import { RecordDisplay } from '$components/ui/Record/index';
  import { createEventDispatcher } from 'svelte';
  const dispatch = createEventDispatcher();

  import '$components/ui/Card/shared-input.css';
  import { endpoint, filters, notify, cardState } from '$states/index';
  import type { NexusRecord } from '$types/index';
  import Button from '$components/ui/Button/Button.svelte';
  import { Checkbox } from '$components/ui/Button/index';
  import { hasAnyActiveFilter } from '$utils/misc';

  // Props
  let { fieldSchema = {}, filteredItems = [] } = $props();

  ////// LOCAL STATE //////
  let onlyShowIds = $state(false);
  let schemaTipsCheckbox = $state(false);
  let currentPage = $state(0);

  // Number of IDs listed per page in IDs-only mode
  const PAGE_SIZE = 20;

  // function to copy share link to clipboard
  function copyShareLink() {
    const currentRecord = derivedStates.currentRecord;
    if (currentRecord?.id) {
      const url = `${window.location.origin}/${endpoint.current}/${encodeURIComponent(currentRecord.id)}`;
      navigator.clipboard
        .writeText(url)
        .then(() => {
          notify.success('Share link copied to clipboard!');
        })
        .catch((_err) => {
          notify.error('Failed to copy share link.');
        });
    }
  }

  const computeDerivedStates = (
    filteredItems: NexusRecord[],
    onlyShowIds: boolean,
    currentPage: number,
    cardState: typeof import('$states/card.svelte').cardState
  ) => {
    const totalPages = Math.max(
      1,
      onlyShowIds ? Math.ceil(filteredItems.length / PAGE_SIZE) : filteredItems.length
    );
    const paginatedItems = onlyShowIds
      ? filteredItems.slice(currentPage * PAGE_SIZE, (currentPage + 1) * PAGE_SIZE)
      : filteredItems;
    const currentRecord = filteredItems[cardState.item] || {};

    return {
      filteredItems,
      totalPages,
      paginatedItems,
      currentRecord
    };
  };

  const derivedStates = $derived.by(() =>
    computeDerivedStates(filteredItems, onlyShowIds, currentPage, cardState)
  );

  // Check if any filters are active
  const hasActiveFilters = $derived(
    hasAnyActiveFilter(filters as unknown as Record<string, unknown>, onlyShowIds)
  );

  // Show navigation unless filtered items are empty with active filters
  const showNavigation = $derived(
    !(derivedStates.filteredItems.length === 0 && hasActiveFilters)
  );

  ///////// REACTIVE EFFECTS /////////

  function next() {
    if (currentPage === derivedStates.totalPages - 1) {
      // restart from the beginning if we're on the last page
      currentPage = 0;
      cardState.item = 0;
    } else {
      updatePage(1);
    }
  }

  function prev() {
    if (currentPage === 0) {
      // go to the end if we're on the first page
      currentPage = derivedStates.totalPages - 1;
      cardState.item = derivedStates.filteredItems.length - 1;
    } else {
      updatePage(-1);
    }
  }

  function updatePage(direction: number) {
    if (onlyShowIds) {
      currentPage = Math.max(
        0,
        Math.min(derivedStates.totalPages - 1, $state.snapshot(currentPage) + direction)
      );
    } else if (derivedStates.filteredItems.length > 0) {
      cardState.item =
        (cardState.item + direction + derivedStates.filteredItems.length) %
        derivedStates.filteredItems.length;

      // In single-item mode, currentPage tracks cardState.item (one page per item)
      currentPage = cardState.item;
    }
  }

  // Track previous filteredItems length to detect real data changes
  let prevFilteredItemsLength = $state(0);

  // Handle data changes - only reset cardState.item when actual data changes
  $effect(() => {
    void filteredItems; // Track changes to filteredItems

    if (filteredItems.length !== prevFilteredItemsLength) {
      prevFilteredItemsLength = filteredItems.length; // Update previous length
      if (cardState.item >= filteredItems.length && filteredItems.length > 0) {
        cardState.item = 0; // Reset to first item if out of bounds
      }
    }
  });

  // Handle currentPage bounds
  $effect(() => {
    const { totalPages } = derivedStates;
    if (currentPage >= totalPages) {
      currentPage = 0;
    }
  });
</script>

<!-- Content-only: CardHolder provides the card shell (background, border,
     accent, padding), so no nested card wrapper is rendered here. -->

<!-- Navigation controls -->
{#if showNavigation}
  <div class="flex items-center justify-between">
    <!-- IDs-only toggle -->
    <div class="flex gap-4">
      <Checkbox
        id="ids-only-checkbox"
        bind:checked={onlyShowIds}
        label="IDs {onlyShowIds ? `(${filteredItems.length})` : ''}"
        labelClass="label label-text text-gray-700 mb-0 cursor-pointer"
        checkboxClass="form-checkbox h-3 w-3 text-gray-400 border-gray-300"
        containerClass="inline-flex items-center gap-2 cursor-pointer"
        scale={1.4}
      />
      <Checkbox
        id="schema-tips-checkbox"
        bind:checked={schemaTipsCheckbox}
        label="Schema"
        labelClass="label label-text text-gray-700 mb-0 cursor-pointer"
        checkboxClass="form-checkbox h-3 w-3 text-gray-400 border-gray-300"
        containerClass="inline-flex items-center gap-2 cursor-pointer"
        scale={1.4}
      />
    </div>
    <!-- Copy Link Button (center)-->
    {#if derivedStates.filteredItems.length > 0 && derivedStates.currentRecord?.id}
      <div class="flex items-center justify-center">
        <Button variant="success" size="xs" on:click={copyShareLink}>Copy Link</Button>
      </div>
    {/if}
    <!-- Pagination and navigation (right) controls -->
    <div class="flex items-center gap-2">
      <PaginationControls
        {currentPage}
        totalPages={derivedStates.totalPages}
        onPrev={prev}
        onNext={next}
      />
    </div>
  </div>
{/if}

{#if onlyShowIds}
  <ul class="list-disc pl-5">
    {#each derivedStates.paginatedItems as item (item.id)}
      <li>{item.id}</li>
    {/each}
  </ul>
{:else if derivedStates.filteredItems.length === 0}
  <NotifyCard
    type="warning"
    message={hasActiveFilters ? 'No records match the current filters.' : 'No records available.'}
    duration={0}
    actions={endpoint.isCurateMode || endpoint.includeByod
      ? [
          {
            label: 'Add new Record',
            callback: () => dispatch('add', { record: {} })
          }
        ]
      : []}
  />
{:else}
  <div class="grid grid-cols-1 gap-x-6 gap-y-3 sm:grid-cols-[200px_1fr] sm:gap-y-4">
    {#if derivedStates.currentRecord && Object.keys(derivedStates.currentRecord).length > 0}
      <RecordDisplay
        {fieldSchema}
        record={derivedStates.currentRecord}
        showSchemaTips={schemaTipsCheckbox}
      />
    {:else}
      <NotifyCard type="info" message="No record selected." />
    {/if}
  </div>
{/if}

{#if endpoint.isCurateMode}
  <div class="mt-2 flex flex-row gap-3">
    {#if derivedStates.filteredItems.length > 0}
      <Button
        variant="edit"
        size="sm"
        on:click={() =>
          dispatch('edit', {
            record: {
              ...filteredItems[cardState.item]
            }
          })}
      >
        Edit this Record
      </Button>
    {/if}
    <Button
      variant="add"
      size="sm"
      on:click={() =>
        dispatch('add', {
          record:
            derivedStates.filteredItems.length > 0 ? { ...filteredItems[cardState.item] } : {}
        })}
    >
      Add new Record
    </Button>
  </div>
{/if}

<style>
  /* Standardize header element font sizes */
  :global(.label-text) {
    font-size: 0.875rem !important;
  }
</style>
