<script lang="ts">
  import { tick } from "svelte";
  import "$components/ui/rightaside.css";
  import {
    UI_WANTED_FILTERS,
    ENDPOINTS,
    ASIDE_TOP_OFFSET_RIGHT,
    ASIDE_HEIGHT,
    ASIDE_WIDTH_RIGHT,
    FOOTER_HEIGHT,
  } from "$lib/constants";
  import { DROPDOWN_FIELDS } from "$states/index";
  import SelectDropdown from "$components/ui/SelectDropdown.svelte";
  import RelatedCheckbox from "$components/ui/Button/RelatedCheckbox.svelte";
  import { Button } from "$components/ui/Button/index";
  import { endpoint, filters, filtered, schemaState } from "$states/index";
  import { resetFiltered, hasAnyActiveFilter } from "$utils/index";

  // local state for related parameter inputs
  let localFilterRisk: string = $state("");
  let localFilterAction: string = $state("");

  // Input refs for focus
  let searchInputRef: HTMLInputElement | null = null;

  // Derived state for active filters check
  const hasActiveFilters = $derived(
      hasAnyActiveFilter(filters as unknown as Record<string, unknown>, false),
  );

  // Derived state for related-record checkbox.
  // Note for /risk paramId: enable when paramId exists and eactly 1 record filtered.
  const canEnableParamIdRelated = $derived(
    endpoint.current === "risk" && filters.paramId && filtered.items.length === 1,
  );

  // For hasRelatedRisk checkbox (all endpoints): enable when 'local filter risk' has value
  const canEnableParamRiskRelated = $derived(localFilterRisk.trim().length > 0);

  // For hasRelatedAction checkbox (/risk endpoint): enable when 'local filter action' has value.
  const canEnableParamActionRelated = $derived(
    // disable temporarily until we have use case
    localFilterAction.trim().length > 0 && endpoint.current !== "risk"
  );

  // Configuration for related parameters sections
  const relatedParamConfigs = [
    {
        param: "hasRelatedRisk",
        localVar: () => localFilterRisk,
        setLocalVar: (val: string) => localFilterRisk = val,
        canEnable: () => canEnableParamRiskRelated,
        label: "Risk ID",
        checkboxLabel: "related risks",
        sectionTitle: "Relations",
    },
    {
        param: "hasRelatedAction",
        localVar: () => localFilterAction,
        setLocalVar: (val: string) => localFilterAction = val,
        canEnable: () => canEnableParamActionRelated,
        label: "Action ID",
        checkboxLabel: "related actions",
        sectionTitle: "Relations",
    },
  ]

  // Derived state for param-id-input disabled state
  const isParamIdDisabled = $derived(filters.isRelatedMode);

  // Get dynamic type label
  const getTypeLabel = $derived(
    `${ENDPOINTS.find((e) => e.key === endpoint.current)?.label || ""} Type`
  )

  // Filter configurations for dropdowns
  const filterConfigs = $derived(
    DROPDOWN_FIELDS.filter((field) => field.param !== "schemaField")  // Exclude search field
    .map((field) => {
      const backendKey = field.param;

      const config: {
        key: string
        id: string;
        label: string;
        param: string;
        disabledExtra: () => boolean;
        onSelect?: (value: string) => void;
      } = {
        key: backendKey,
        id: field.key,
        label: field.param === "type" ? getTypeLabel : field.label,
        param: field.param,
        disabledExtra: () => false,  // All all filter combinations
      }

      // Special onSelect handler for taxonomy.
      if (field.param === "isDefinedByTaxonomy") {
        config.onSelect = (value: string) => {
          if (endpoint.current === "taxonomy") {
            // For taxonomy endpoint, populate 'id' with value selected from taxonomy dropdown.
            filters.setParam("paramId", value);
          } else {
            // Otherwise just set the taxonomy filter param as usual.
            filters.setParam("isDefinedByTaxonomy", value);
          }
        }
      }

      return config;
    }),
  );

  // Active filter display items
  const activeFilterItems = $derived([
    // standard fields
    ...DROPDOWN_FIELDS.filter((field) => field.param !== "schemaField").map(
      (field) => {
        const backendKey = field.param;
        const paramValue = filters.getParam(field.param);

        return {
          key: backendKey,
          label: field.label,
          value: paramValue,
          show: UI_WANTED_FILTERS[String(endpoint.current)]?.includes(backendKey) && !!paramValue,
        }
      }
    ),

    // Special filter items
    {
      key: "id",
      label: `${endpoint.getLabel()} ID`,
      value: filters.paramId,
      show: !!filters.paramId,
    },
    {
      key: "related",
      label: "Related mode",
      value: "fetch",
      show: filters.isRelatedMode,
    },
    {
      key: "search",
      label: "Search",
      value: `${filters.schemaField}: ${filters.searchText}`,
      show: !!filters.searchText,
    },
  ]);

  // Reactive dropdownSearch
  $effect(() => {
    let fields: string[] = [];
    const schema = schemaState.endpoints[String(endpoint.current)];
    if (!schema) {
      if (filters.dropdownSearch.length !== 0) {
        filters.dropdownSearch = [];
      }
      return;
    }

    if (Array.isArray(schema.displayFields)) {
      fields = schema.displayFields;
    }

    const newOptions = fields.map((field) => ({
      label: field,
      value: field,
    }));

    if (JSON.stringify(filters.dropdownSearch) !== JSON.stringify(newOptions)) {
      filters.dropdownSearch = newOptions;
    }
  });
</script>

{#snippet clearButtonIcon()}
  <svg
    xmlns="http://www.w3.org/2000/svg"
    width="18"
    height="18"
    fill="none"
    viewBox="0 0 24 24"
  >
    <circle cx="12" cy="12" r="10" fill="#e5e7eb" />
    <path
      stroke="#555"
      stroke-width="2"
      stroke-linecap="round"
      d="M9 9l6 6m0-6l-6 6"
    />
  </svg>
{/snippet}
 
<aside
  id="right-aside"
  itemscope
  itemtype="https://schema.org/WebPageElement"
  class="fixed right-0 bg-transparent backdrop-blur-lg shadow-2xl py-2 pb-[30px] z-40 flex flex-col gap-1 rounded-2xl font-sans text-lg responsive-right-aside h-auto transition-[right] duration-200 box-border max-w-full overflow-y-auto pl-8 pr-6 mt-0"
  style="top: {ASIDE_TOP_OFFSET_RIGHT}; min-height: {ASIDE_HEIGHT}; max-height: {ASIDE_HEIGHT}; width: {ASIDE_WIDTH_RIGHT}; margin-bottom: {FOOTER_HEIGHT};"
> 
  <!-- Search bar -->
  <div
    id="search-section"
    itemscope
    itemtype="https://schema.org/SearchAction"
    itemprop="potentialAction"
    class="flex flex-col gap-0 w-full bg-linear-to-br from-blue-200/90 via-blue-100/90 to-blue-50/80 border-2 border-blue-400 rounded-2xl px-2 py-1 pb-1.5 items-start mb-0 shadow-sm text-black box-border self-end"
  >
    <h3
      itemprop="title"
      class="text-sm font-bold text-black tracking-wide mb-0 w-full"
    >
      Search
    </h3>
 
    <div
      itemprop="additionalProperty"
      itemscope
      itemtype="https://schema.org/PropertyValue"
      class="w-full"
    >
      <meta itemprop="propertyID" content="schemaField" />
      <div class="w-full">
        <SelectDropdown
          key={`${endpoint.current}-schemaField`}
          id="schema-field-select"
          label="Schema field"
          value={filters.schemaField}
          placeholder="description"
          clearable={true}
          getOptions={() => filters.getOptions("schemaField")}
          on:select={async (event: CustomEvent) => {
            filters.setParam("schemaField", event.detail);
            await tick();
          }}
          on:clear={() => {
            filters.setParam("schemaField", "description");
          }}
        />
      </div>
      <meta itemprop="value" content={filters.schemaField} />
    </div>
 
    <div
      itemprop="additionalProperty"
      itemscope
      itemtype="https://schema.org/PropertyValue"
      class="relative w-full flex items-center"
    >
      <meta itemprop="propertyID" content="searchText" />
      <input
        id="param-search-text"
        itemprop="value"
        type="text"
        class="input input-sm w-full max-w-full pl-3 rounded-lg bg-white text-black placeholder-black font-normal pr-8"
        style="height: 32px; min-height: 32px; font-size: 0.875rem;"
        placeholder="text to find"
        bind:value={filters.searchText}
        bind:this={searchInputRef}
        oninput={(e) =>
          filters.setParam(
            "searchText",
            (e.target as HTMLInputElement).value,
          )}
        autocomplete="off"
      />
      {#if filters.searchText}
        <button
          type="button"
          aria-label="Clear search"
          class="absolute right-2 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-700 focus:outline-none bg-transparent border-0 p-0 m-0 cursor-pointer"
          onclick={() => {
            filters.setParam("searchText", "");
            searchInputRef?.focus();
          }}
        >
          {@render clearButtonIcon()}
        </button>
      {/if}
    </div>
  </div>
 
  <!-- Filtering and Related Risk grouped together -->
  <div
    id="filtering-section"
    itemscope
    itemtype="https://schema.org/WebPageElement"
    class="flex flex-col gap-0 w-full bg-linear-to-br from-blue-200/90 via-blue-100/90 to-blue-50/80 border-2 border-blue-400 rounded-2xl px-2 py-1 items-start shadow-sm text-black"
    style="width:100%;padding-bottom: 0.5rem;box-sizing:border-box;align-self:flex-end;"
  >
    <h3
      itemprop="title"
      class="text-sm font-bold text-black tracking-wide mb-0"
    >
      Filtering
    </h3>
    <div
      itemprop="additionalProperty"
      itemscope
      itemtype="https://schema.org/PropertyValue"
      class="flex flex-col gap-0 w-full box-border"
    >
      <div
        class="flex flex-row justify-between items-center w-full"
        style="min-height: auto; padding-top: 0.25rem; padding-bottom: 0.125rem; margin-bottom: 0.25rem;"
      >
        <meta itemprop="propertyID" content="paramId" />
        <label
          for="param-id-input"
          itemprop="name"
          class="label label-text text-sm pl-1 text-black leading-tight"
          style="min-height: auto; padding: 0; margin: 0;"
        >
          {endpoint.getLabel()} ID
        </label>
        {#if endpoint.current === "risk"}
          <RelatedCheckbox
            id="param-id-related-checkbox"
            bind:checked={filters.isRelatedMode}
            disabled={!canEnableParamIdRelated && !filters.isRelatedMode}
            label="get related risks"
            onchange={(checked) => {
              if (checked) {
                // For risk endpoint with paramId, just enable related mode
                // The fetch will use paramId with related=true
                filters.setParam("isRelatedMode", true);
              } else {
                filters.setParam("isRelatedMode", false);
              }
            }}
          />
        {/if}
      </div>
      <input
        id="param-id-input"
        itemprop="value"
        type="text"
        bind:value={filters.paramId}
        placeholder="id ..."
        class="input input-sm w-full max-w-full pl-3 rounded-lg bg-white text-black placeholder-black font-normal {filters.isRelatedMode
          ? 'opacity-50 cursor-not-allowed'
          : ''}"
        style="height: 32px; min-height: 32px; font-size: 0.875rem; width:100%;"
        disabled={isParamIdDisabled}
        oninput={(e) => {
          const val = (e.target as HTMLInputElement).value;
          filters.setParam("paramId", val.trim());
          if (!val || (val.trim() === "" && filters.isRelatedMode)) {
            // If clearing the ID, uncheck related checkbox
            filters.setParam("isRelatedMode", false);
          }
        }}
        autocomplete="off"
      />
 
      {#each filterConfigs.filter( (config) => UI_WANTED_FILTERS[String(endpoint.current)]?.includes(config.key), ) as config (config.id)}
        {#if config.param !== "hasRelatedRisk" && config.param !== "hasRelatedAction"}
          <div
            itemprop="additionalProperty"
            itemscope
            itemtype="https://schema.org/PropertyValue"
            class="w-full"
          >
            <meta itemprop="propertyID" content={config.param} />
            <div class="w-full">
              <SelectDropdown
                key={`${endpoint.current}-${config.param}`}
                id={config.id}
                label={config.label}
                value={String(filters.getParam(config.param) || "")}
                clearable={true}
                disabled={config.disabledExtra() ||
                  (!filters.isRelatedMode &&
                    filters.getOptions(config.param).length === 0)}
                getOptions={() => filters.getOptions(config.param)}
                on:select={async (event: CustomEvent) => {
                  if (config.onSelect) {
                    config.onSelect(event.detail);
                  } else {
                    filters.setParam(config.param, event.detail);
                  }
                  await tick();
                }}
                on:clear={() => {
                  filters.setParam(config.param, "");
                }}
              />
            </div>
            <meta
              itemprop="value"
              content={String(filters.getParam(config.param) || "")}
            />
          </div>
        {/if}
      {/each}
    </div>
  </div>
 
  <!-- Related Section, separate from Filters -->
  {#each relatedParamConfigs as relatedConfig (relatedConfig.param)}
    {#if UI_WANTED_FILTERS[String(endpoint.current)]?.includes(relatedConfig.param)}
      {@const paramConfig = filterConfigs.find((config) => config.param === relatedConfig.param)}
      <div
        id="{relatedConfig.param}-section"
        class="flex flex-col gap-0 w-full bg-linear-to-br from-blue-200/90 via-blue-100/90 to-blue-50/80 border-2 border-blue-400 rounded-2xl px-2 py-1 items-start shadow-sm text-black"
        style="width:100%;padding-bottom: 0.5rem;box-sizing:border-box;"
      >
        <h3 class="text-sm font-bold text-black tracking-wide mb-0">{relatedConfig.sectionTitle}</h3>
        <div
          class="flex flex-row justify-between items-center w-full"
          style="min-height: auto; padding-top: 0.25rem; padding-bottom: 0.125rem; margin-bottom: 0.25rem;"
        >
          <div
            itemprop="additionalProperty"
            itemscope
            itemtype="https://schema.org/PropertyValue"
            class="w-full flex flex-row justify-between items-center"
          >
            <meta itemprop="propertyID" content="isRelatedMode" />
            <label
              for="param-{relatedConfig.param}-input"
              itemprop="name"
              class="label label-text text-sm pl-1 text-black leading-tight"
              style="min-height: auto; padding: 0; margin: 0;"
              >{relatedConfig.label}
            </label>
              <RelatedCheckbox
                id="param-{relatedConfig.param}-related-checkbox"
                bind:checked={filters.isRelatedMode}
                disabled={!relatedConfig.canEnable() && !filters.isRelatedMode}
                label={relatedConfig.checkboxLabel}
                onchange={(checked) => {
                  if (checked) {
                    // Set the related param from input field and enable related mode
                    filters.setParam(relatedConfig.param, relatedConfig.localVar().trim());
                    filters.setParam("isRelatedMode", true);
                  } else {
                    // Disable related mode
                    filters.setParam(relatedConfig.param, relatedConfig.localVar());  // reactivity
                    filters.setParam("isRelatedMode", false);
                  }
                }}
              />
          </div>
        </div>
        {#if paramConfig}
          <div
            itemprop="additionalProperty"
            itemscope
            itemtype="https://schema.org/PropertyValue"
            class="w-full"
          >
            <meta itemprop="propertyID" content={paramConfig.param} />
            <div class="w-full">
              <SelectDropdown
                key={`${endpoint.current}-${paramConfig.param}`}
                id={paramConfig.id}
                label=""
                value={String(filters.getParam(paramConfig.param) || "")}
                clearable={true}
                creatable={true}
                disabled={paramConfig.disabledExtra() ||
                  (!filters.isRelatedMode &&
                    filters.getOptions(paramConfig.param).length === 0)}
                getOptions={() => filters.getOptions(paramConfig.param)}
                on:select={async (event: CustomEvent) => {
                  if (paramConfig.onSelect) {
                    paramConfig.onSelect(event.detail);
                  } else {
                    filters.setParam(paramConfig.param, event.detail);
                  }
                  relatedConfig.setLocalVar(event.detail);
                  await tick();
                }}
                on:clear={() => {
                  filters.setParam(paramConfig.param, "");
                  relatedConfig.setLocalVar("");
                  filters.setParam("isRelatedMode", false);
                }}
              />
            </div>
            <meta
              itemprop="value"
              content={String(filters.getParam(paramConfig.param) || "")}
            />
          </div>
        {/if}
      </div>
    {/if}
  {/each}
 
  <!-- Information container for active/display filters -->
  {#if hasActiveFilters}
    <div
      id="active-filters"
      class="px-2 py-0.5 rounded-2xl bg-linear-to-br from-blue-200/90 via-blue-100/90 to-blue-50/80 border-2 border-blue-400 shadow-lg text-xs text-black font-normal flex flex-col gap-0"
      style="width:100%;box-sizing:border-box;padding-top:0.25rem;"
    >
      <div class="flex items-center gap-1 mb-0">
        <span class="tracking-wide text-sm font-normal text-black"
          >Active Filters</span
        >
        <svg
          class="w-4 h-4 text-blue-400"
          fill="none"
          stroke="currentColor"
          stroke-width="2"
          viewBox="0 0 24 24"
          ><circle
            cx="12"
            cy="12"
            r="10"
            stroke="#2563eb"
            stroke-width="2"
            fill="#2563eb"
            fill-opacity="0.10"
          /><path
            d="M12 8v4l3 2"
            stroke="#2563eb"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          /></svg
        >
      </div>
      <ul class="list-disc pl-4 mb-0 text-xs leading-tight">
        {#each activeFilterItems.filter((item) => item.show) as item (item.key)}
          <li
            class="py-0"
            itemprop="additionalProperty"
            itemscope
            itemtype="https://schema.org/PropertyValue"
          >
            <meta itemprop="propertyID" content={item.key} />
            {#if item.label}
              <span class="font-normal text-black" itemprop="name"
                >{item.label}:</span
              >
            {/if}
            <span class="font-normal text-black" itemprop="value"
              >{item.value || item.label}</span
            >
          </li>
        {/each}
      </ul>
      <div class="flex flex-row items-center justify-center w-full mt-2">
        <Button
          variant="info"
          size="xs"
          on:click={() => {
            resetFiltered(endpoint.current, endpoint.isCurateMode);
            localFilterRisk = "";
            localFilterAction = "";
          }}
          ariaLabel="Reset all fields"
          style="font-size: 0.8rem; min-height: 24px; height: 24px;"
        >
          Reset
        </Button>
      </div>
    </div>
  {/if}
</aside>
