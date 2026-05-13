<script lang="ts">
    import { untrack } from 'svelte';
    import Button from "$components/ui/Button/Button.svelte";
    import { ButtonCloud, Checkbox } from "$components/ui/Button/index";
    import { SvelteMap, SvelteSet} from "svelte/reactivity";
    import {
        authState,
        endpoint,
        filters,
        filtered,
        dataState,
        relatedRecords,
    } from "$states/index";
    import { fetchData, resetFiltered } from "$utils/index";
    import { devWarn } from "$utils/misc";
    import type { NexusRecord, DropdownOptionType } from "$types/index";
    import {
        BYO_ICON_TEXT,
        ENDPOINTS,
        ENDPOINT_GROUPS,
        MAX_CACHE_SIZE,
        ASIDE_TOP_OFFSET_LEFT,
        ASIDE_HEIGHT,
        ASIDE_WIDTH_LEFT,
        FOOTER_HEIGHT,
        ASIDE_TRANSITION_DURATION,
    } from '$lib/constants';
    
    // Cache to store fetched data for endpoints (with size limit)
    let dataCache = new SvelteMap<string, NexusRecord[]>();

    // Track ongoing fetches to prevent duplicate requests
    const ongoingFetches = new SvelteSet<string>();
    let prevIncludeByod = false;

    // Accordian state, goverance group open by default
    let expandedGroups = new SvelteSet(['governance']);

    // Derived state - find which group contains the active endpoint
    const activeGroupId = $derived(() => {
        return ENDPOINT_GROUPS.find(group => group.endpoints.includes(endpoint.current),)?.id || null;
    });

    // REACTIVITY //

    // Effect to handle data fetching and caching
    $effect(() => {
        // Explicitly track all values that should trigger fetches
        void endpoint.current;
        void endpoint.includeByod;
        void endpoint.isCurateMode;
        void filters.hasRelatedRisk;
        void filters.hasRelatedAction;
        void filters.isRelatedMode;

        // Check loading state (without tracking to avoid unnecessary re-renders)
        if (untrack(() => endpoint.isLoading)) {
            return; // Skip if already loading
        }

        // force re-fetch if includeByod changes.
        if (prevIncludeByod !== endpoint.includeByod) {
            dataCache.clear();
            prevIncludeByod = endpoint.includeByod;
        }

        // Implement cache size limit
        if (dataCache.size > MAX_CACHE_SIZE) {
            const firstKey = dataCache.keys().next().value;
            if (firstKey) dataCache.delete(firstKey);
        }

        // Snapshot values ONCE to avoid re-reading state and triggering multiple fetches
        const currentEndpoint = endpoint.current;
        const includeByod = endpoint.includeByod;
        const isCurateMode = endpoint.isCurateMode;
        const hasRelatedRisk = filters.hasRelatedRisk;
        const hasRelatedAction = filters.hasRelatedAction;
        const isRelatedMode = filters.isRelatedMode;
        const paramId = filters.paramId;    // Not tracked, but needed or API params

        // Build API params using snapshot values to avoid reactivity issues
        const apiParams: Record<string, string | boolean> = {};
        if (isRelatedMode) {
            apiParams.related = true;  // required for 'related' records
            if (paramId) {
                apiParams.id = paramId;
            }
        }
        if (hasRelatedRisk) {
            apiParams.hasRelatedRisk = hasRelatedRisk;
        }
        if (hasRelatedAction) {
            apiParams.hasRelatedAction = hasRelatedAction;
        }

        // Build cache and fetch keys (paramId is client-side only,
        // hasRelatedRisk/Action trigger backend fetches).
        const cacheKey = `${currentEndpoint}|${hasRelatedRisk}|${hasRelatedAction}|${isRelatedMode}`;
        const fetchKey = `${currentEndpoint}|${includeByod}|${isCurateMode}|${hasRelatedRisk}|${hasRelatedAction}|${isRelatedMode}`;

        if (ongoingFetches.has(fetchKey)) {
            return; // Skip if a fetch is already in progress for this key
        }

        // Check if data already exists
        if (isCurateMode) {
            // In curate mode, check if data is already loaded for this endpoint.
            // Use untrack to avoid triggering reactivity reading dataState.items
            const existingData = untrack(() => dataState.getItem(`${currentEndpoint}&byod`));
            if (existingData && existingData.length > 0) {
                return; // Data already loaded, skip fetch
            }
        } else {
            // In non-curate mode, check cache first
            if (!isRelatedMode) {
                const cachedData = dataCache.get(cacheKey);
                if (cachedData !== undefined) {
                    // Load from cache into dataState for current endpoint
                    // even if empty, to prevent unnecessary fetches.
                    untrack(() => {
                        dataState.setItems([{ key: cacheKey, items: cachedData }]);
                    });
                    return;
                }
            }
        }

        // If we reach here, we need to fetch data
        ongoingFetches.add(fetchKey);
        fetchData(endpoint, includeByod, apiParams)
            .then((fetchedData: NexusRecord[] | undefined) => {
                // Handle undefined return / error case
                if (!fetchedData) {
                    devWarn(`No data returned from fetch for endpoint ${currentEndpoint}`);
                    return;
                }

                // Related mode or hasRelatedRisk or hasRelatedAction - store result in 'relatedRecords.items'
                if (isRelatedMode || hasRelatedRisk || hasRelatedAction) {
                    relatedRecords.setItems(fetchedData);
                } else if (isCurateMode) {
                    // Curate mode - data was already populated by 'fetchYourData()' function.
                    // Just clear related records if needed
                    if (relatedRecords.items && relatedRecords.items.length > 0) {
                        relatedRecords.setItems([]);
                    }
                } else {
                    // Normal mode: store in cache and dataState with cacheKey
                    if (relatedRecords.items && relatedRecords.items.length > 0) {
                        relatedRecords.setItems([]);
                    }

                    const items = fetchedData && fetchedData.length > 0 ? fetchedData : [];

                    // Use cacheKey for local cache (includes filters)
                    dataCache.set(cacheKey, items);

                    // Use endpoint.current for dataState (simple key for compatiblity)
                    dataState.setItems([{ key: currentEndpoint, items }]);
                }
            })
            .catch((error: unknown) => {
                devWarn(`Error in fetchData: ${error}`);
            })
            .finally(() => {
                ongoingFetches.delete(fetchKey);
            });
        });

    // Single $effect for filtering against filtered-items. No backend fetches
    // happen here, just client-side filtering of already fetched data.
    $effect(() => {
        // Track loading so we re-run when fetch completes
        if (endpoint.isLoading) {
            return; // Skip if loading, will re-run when loading state changes
        }

        // Track changes to data sources
        void dataState.items;
        void dataState.yourItems;   // curated data
        void relatedRecords.items;  // related records

        // Track endpoint changes
        void endpoint.current;
        void endpoint.isCurateMode;

        // Track only actual filter parameters - getAllParamValues() trackes
        // param*, searchText, schemaField, isRelatedMode (but not dropdowns).
        void filters.getAllParamValues();   // track for reactivity

        // Snapshot vlaues to avoid reading reactive state multiple times.
        const currentEndpoint = endpoint.current;
        const isCurateMode = endpoint.isCurateMode;
        const isRelatedMode = filters.isRelatedMode;

        // Get data items from source
        const items: NexusRecord[] = (
            isRelatedMode
                ? relatedRecords.items || []
                : isCurateMode
                    ? dataState.getItem(`${currentEndpoint}&byod`) || []
                    : dataState.getItem(currentEndpoint) || []
        ) as NexusRecord[];

        if (!Array.isArray(items) || items.length === 0) {
            // No data to filter, set filtered to empty and exit early
            filtered.setItems([]);
            return;
        }

        // Single filter pass using a 'filtered item'
        const fItems = items.filter((item) =>
            filters.filterItem(currentEndpoint, item as unknown as DropdownOptionType,)
        );
        filtered.setItems(fItems);

        // Use untrack to prevent setDropdownOptions from triggering reactivity
        // (it reads filtered.items)
        untrack(() => filters.setDropdownOptions(fItems));
    })
</script>

<aside
  id="left-aside-content-container"
  class="fixed left-0 bg-linear-to-br from-green-800/90 via-green-700/90 to-green-500/80 backdrop-blur-lg shadow-2xl border-r border-white py-6 px-4 z-30 flex flex-col items-center rounded-2xl"
  style="top: {ASIDE_TOP_OFFSET_LEFT}; height: {ASIDE_HEIGHT}; width: {ASIDE_WIDTH_LEFT}; transition: left {ASIDE_TRANSITION_DURATION}; margin-bottom:{FOOTER_HEIGHT}; overflow-y: auto; box-sizing: border-box;"
  aria-label="Navigation sidebar"
> 
  <nav
    class="flex flex-col w-full mb-2"
    style="gap:0.5rem;"
    aria-label="Main navigation"
  >
    {#each ENDPOINT_GROUPS as group (group.id)}
      <details
        class="group-accordion"
        class:active-group={activeGroupId() === group.id}
        open={expandedGroups.has(group.id)}
        ontoggle={(e) => {
          const details = e.currentTarget as HTMLDetailsElement;
          if (details.open) {
            // When opening, close all others and keep only this one
            expandedGroups.clear();
            expandedGroups.add(group.id);
          } else {
            // When closing, remove from set
            expandedGroups.delete(group.id);
          }
        }}
      >
        <summary class="accordion-header">
          <span class="icon">{group.icon}</span>
          <span class="label">{group.label}</span>
          <span class="chevron">▼</span>
        </summary>
        <ButtonCloud randomize={false} padding="1.5rem 0.5rem">
          {#each group.endpoints as epKey (epKey)}
            {@const ep = ENDPOINTS.find((e) => e.key === epKey)}
            {#if ep}
              <Button
                variant={endpoint.current === ep.key ? "success" : "default"}
                size="sm"
                fullWidth={true}
                ariaLabel={`Navigate to ${ep.label}`}
                on:click={() => {
                  endpoint.setCurrent(ep.key);
                  resetFiltered(ep.key, endpoint.isCurateMode);
                }}
              >
                {ep.label}
              </Button>
            {/if}
          {/each}
        </ButtonCloud>
      </details>
    {/each}
  </nav>
 
  <!-- Divider -->
  <div class="section-divider"></div>
 
  <div class="flex justify-center w-full mt-1 mb-1">
    <Checkbox
      id="include-byod-checkbox"
      bind:checked={endpoint.includeByod}
      disabled={endpoint.isCurateMode}
      label="Include your Data"
      containerClass="flex flex-row items-center gap-2"
    />
  </div>
 
  {#if authState.loggedIn}
    <div class="flex justify-center w-full mt-1 mb-1">
      <Button
        id="curate-button"
        variant={endpoint.isCurateMode ? "curate" : "default"}
        size="md"
        fullWidth={false}
        ariaLabel={endpoint.isCurateMode
          ? "Exit curate mode"
          : "Enter curate mode"}
        on:click={() => {
          endpoint.setCurateMode(!endpoint.isCurateMode);
        }}
      >
        {#if endpoint.isCurateMode}
          {BYO_ICON_TEXT} Data
        {:else}
          Curate
        {/if}
      </Button>
    </div>
  {/if}
  <!-- Divider -->
  <div class="section-divider"></div>
 
  <style>
    /* Checkbox styling */
    .checkbox-scaled {
      transform: scale(1.4);
      margin-right: 0.75rem;
    }
 
    .checkbox-label {
      font-size: 1rem;
    }
 
    /* Section divider */
    .section-divider {
      width: 100%;
      height: 1px;
      background: linear-gradient(
        to right,
        transparent,
        rgba(255, 255, 255, 0.3) 20%,
        rgba(255, 255, 255, 0.3) 80%,
        transparent
      );
      margin: 0.75rem 0;
    }
 
    /* Accordion group styling */
    .group-accordion {
      border: 1px solid rgba(255, 255, 255, 0.25);
      border-radius: 0.5rem;
      background: rgba(0, 0, 0, 0.2);
      overflow: hidden;
      transition: all 0.2s ease;
    }
 
    .group-accordion[open] {
      overflow: visible;
    }
 
    .group-accordion:hover {
      background: rgba(0, 0, 0, 0.25);
      border-color: rgba(255, 255, 255, 0.35);
    }
 
    .group-accordion.active-group {
      border-color: rgba(255, 255, 255, 0.6);
      background: rgba(0, 0, 0, 0.3);
      box-shadow: 0 0 12px rgba(255, 255, 255, 0.2);
    }
 
    .accordion-header {
      display: flex;
      align-items: center;
      gap: 0.5rem;
      padding: 0.75rem 1rem;
      cursor: pointer;
      user-select: none;
      font-weight: 600;
      font-size: 1rem;
      color: white;
      list-style: none;
      transition: background 0.15s ease;
    }
 
    .accordion-header::-webkit-details-marker {
      display: none;
    }
 
    .accordion-header:hover {
      background: rgba(255, 255, 255, 0.1);
    }
 
    .accordion-header .icon {
      font-size: 1.25rem;
      flex-shrink: 0;
    }
 
    .accordion-header .label {
      flex: 1;
    }
 
    .accordion-header .chevron {
      font-size: 0.875rem;
      transition: transform 0.2s ease;
      flex-shrink: 0;
    }
 
    .group-accordion[open] .chevron {
      transform: rotate(-180deg);
    }
 
    /* Button height constraints for different screen sizes */
    @media (max-height: 700px), (max-width: 900px) {
      #left-aside-content-container nav button {
        min-height: 30px;
        max-height: 42px;
      }
    }
    @media (max-height: 500px), (max-width: 600px) {
      #left-aside-content-container nav button {
        min-height: 34px;
        max-height: 44px;
      }
    }
    /* High DPI large screens */
    @media (min-width: 2000px) and (min-resolution: 2dppx) {
      #left-aside-content-container nav button {
        min-height: 54px;
        max-height: 80px;
      }
    }
    /* Mobile responsive */
    @media (max-width: 768px) {
      #left-aside-content-container {
        width: 14rem;
        padding-left: 0.75rem;
        padding-right: 0.75rem;
      }
      .accordion-header {
        font-size: 0.875rem;
        padding: 0.6rem 0.75rem;
      }
      .accordion-header .icon {
        font-size: 1rem;
      }
    }
  </style>
</aside>