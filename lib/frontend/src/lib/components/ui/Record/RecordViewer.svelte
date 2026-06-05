<script lang="ts">
  import { onMount } from 'svelte';
  import { endpoint } from '$states/endpoint.svelte';
  import { schemaState } from '$states/schema.svelte';
  import { notify } from '$states/notify.svelte';
  import { uiState } from '$states/ui.svelte';
  import { initializeSchemaState } from '$utils/schema';
  import { devLog, devError } from '$utils/misc';
  import { NotifyCard } from '$components/ui/Card/index';
  import type { NexusRecord, ComputedSchemaFields } from '$types/index';

  // Props
  let {
    endpointKey = '',
    recordId = '',
    onRecordLoaded = (title: string) => {
      void title;
    }
  } = $props();

  let record = $state<NexusRecord | null>(null);
  let isLoading = $state(true);
  let error = $state<string | null>(null);
  let schemaLoaded = $state(false);
  let fieldSchema = $derived(schemaState.endpoints[endpointKey] as unknown as ComputedSchemaFields);

  async function fetchRecord() {
    if (!endpointKey || !recordId) {
      error = 'Missing endpoint key or record ID.';
      isLoading = false;
      return;
    }

    isLoading = true;
    error = null;

    try {
      // Fetch from API
      const url = `/${endpointKey}?id=${encodeURIComponent(recordId)}&byod=true`;
      devLog(`[RecordViewer] Fetching record from ${url}`);
      const response = await fetch(url);
      if (!response.ok) {
        throw new Error(`Failed to fetch record: ${response.status} ${response.statusText}`);
      }

      const data = await response.json();
      devLog(`[RecordViewer] Record data received:`, data);

      // API returns { item: {...} } when querying by ID (single record)
      // or { items: [...] } when querying multiple records;
      if (data.item) {
        devLog(`[RecordViewer] Single record found, using data.item`);
        record = data.item;
        if (record) {
          onRecordLoaded(record.name || record.id || 'Record');
        }
      } else if (data.items && data.items.length > 0) {
        const foundRecord = data.items.find((item: NexusRecord) => item.id === recordId);
        if (foundRecord) {
          devLog(`[RecordViewer] Record found in items array`, foundRecord);
          record = foundRecord;
        } else {
          devError(
            `[RecordViewer] Record '${recordId}' not found. Available IDs:`,
            data.items.map((item: NexusRecord) => item.id)
          );
          throw new Error(`Record with ID '${recordId}' not found.`);
        }
      } else {
        throw new Error(`No record found with ID '${recordId}'.`);
      }
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed to load record';
      notify.error(error);
    } finally {
      isLoading = false;
    }
  }

  onMount(async () => {
    // Set endpoint to match URL
    endpoint.current = endpointKey;

    // Initialize schema state if not already loaded
    if (!schemaState.endpoints[endpointKey]) {
      await initializeSchemaState();
    }
    schemaLoaded = true;

    // Fetch the record data
    await fetchRecord();
  });

  // Refetch when params change
  $effect(() => {
    if (endpointKey && recordId && schemaLoaded) {
      fetchRecord();
    }
  });
</script>

<div class="flex min-h-screen flex-col items-center justify-start px-4 pt-8">
  <div class="w-full max-w-7xl">
    <div class="relative mb-5" style="z-index: 100;">
      <a
        href="/"
        class="inline-block rounded-lg bg-black/20 px-4 py-2 text-lg font-semibold text-white transition-colors hover:bg-black/30 hover:text-green-300"
      >
        Back to Browse
      </a>
    </div>

    {#if isLoading}
      <NotifyCard type="info" message="Loading record..." />
    {:else if error}
      <NotifyCard type="error" message={error} />
    {:else if record && fieldSchema}
      <!-- Card Holder styling - same as CardHolder.svelte -->
      <div
        class={`mx-auto mb-8 w-full rounded-3xl bg-linear-to-br from-[#43b02a] via-blue-100 to-blue-400 p-[2.5px] px-2 sm:px-4 ${uiState.cardWidthClass}`}
      >
        <div
          class="shadow-3xl hover:scale[1.018] group relative mx-auto flex w-full items-start justify-center overflow-hidden rounded-[calc(1.5rem-2.5px)] border-2 border-transparent bg-white/70 backdrop-blur-lg transition-transform duration-200 hover:shadow-green-200/80"
        >
          <!-- Vertical Accent bar -->
          <div
            class="absolute top-0 left-0 h-full w-2 rounded-l-3xl bg-linear-to-b from-[#43b02a] via-green-200 to-green-100"
          ></div>
          <!-- Glassmorphism background layer with inner glow -->
          <div
            class="absolute inset-0 z-0 bg-linear-to-br from-white/90 via-green-50/60 to-green-100/70 shadow-[0_0_32px_8px_#bbf7d0_inset] backdrop-blur-2xl"
          ></div>

          <div class="relative z-10 flex w-full flex-col gap-4 px-6 py-6 sm:px-8 sm:py-8 md:px-10">
            <!-- Fields Grid - same layout as RecordForm -->
            <div class="grid w-full grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-1">
              {#if fieldSchema?.displayFields && Array.isArray(fieldSchema.displayFields) && fieldSchema.displayFields.length > 0}
                {#each fieldSchema.displayFields as key (key)}
                  <div class="flex w-full flex-col items-start gap-1">
                    <!-- Field label with icon - same as RecordForm -->
                    <div class="flex items-center gap-2">
                      <span
                        class="inline-flex h-7 w-7 items-center justify-center rounded-full border border-green-200 bg-white shadow"
                      >
                        <svg
                          class="h-5 w-5"
                          fill="none"
                          stroke="#176a2a"
                          stroke-width="2.2"
                          viewBox="0 0 24 24"
                          aria-hidden="true"
                        >
                          <circle cx="12" cy="12" r="10" />
                          <line x1="12" y1="8" x2="12" y2="12" />
                          <circle cx="12" cy="16" r="1" />
                        </svg>
                      </span>

                      <span class="text-left text-lg tracking-wide text-gray-900 drop-shadow-sm">
                        {key}
                        {#if fieldSchema?.fieldTypes?.[key] && !fieldSchema.fieldTypes[key].includes('null')}
                          <span class="ml-1 font-bold text-orange-500" title="Required">*</span>
                        {/if}

                        {#if fieldSchema?.fieldTypes?.[key]}
                          {#if !fieldSchema.fieldTypes[key].includes('null')}
                            <span class="ml-2 text-base font-bold text-orange-500 italic"
                              >(type: {fieldSchema.fieldTypes[key]})</span
                            >
                          {:else}
                            <span class="ml-2 text-base text-gray-400 italic"
                              >(type: {fieldSchema.fieldTypes[key]})</span
                            >
                          {/if}
                        {/if}
                      </span>
                    </div>

                    <!-- Field value -->
                    {#if record?.[key] && record[key] !== '' && (!Array.isArray(record[key]) || record[key].length > 0)}
                      {#if Array.isArray(record[key])}
                        <div
                          class="wrap-break-words w-full rounded-lg border border-gray-100 bg-white/90 px-4 py-2 text-left text-lg text-gray-900 shadow"
                        >
                          <ul class="list-inside list-disc space-y-1">
                            {#each record[key] as item, index (index)}
                              <li class="ml-2">
                                {#if typeof item === 'object' && item !== null}
                                  <pre
                                    class="inline rounded bg-gray-50 px-2 py-1 text-lg">{JSON.stringify(
                                      item,
                                      null,
                                      2
                                    )}</pre>
                                {:else}
                                  <span>{item}</span>
                                {/if}
                              </li>
                            {/each}
                          </ul>
                        </div>
                      {:else}
                        <div
                          class="wrap-break-words w-full rounded-lg border border-gray-100 bg-white/90 px-4 py-2 text-left text-lg text-gray-900 shadow"
                        >
                          {#if key === 'url' && typeof record[key] === 'string'}
                            <a
                              href={record[key]}
                              target="_blank"
                              rel="noopener noreferrer"
                              class="break-all text-blue-600 underline hover:text-blue-800"
                            >
                              {record[key]}
                            </a>
                          {:else}
                            {record[key]}
                          {/if}
                        </div>
                      {/if}
                    {:else}
                      <span
                        class="w-full rounded-lg border border-gray-100 bg-white/90 px-4 py-2 text-lg text-gray-600 italic shadow"
                      >
                        (empty)
                      </span>
                    {/if}

                    <!-- Field Description -- same as RecordForm -->
                    {#if fieldSchema?.fieldDescriptions?.[key]}
                      <span class="text-md ml-2 text-blue-400"
                        >{fieldSchema.fieldDescriptions[key]}</span
                      >
                    {/if}
                  </div>
                {/each}
              {:else}
                <!-- Fallback: display all fields if displayFields not avaialble -->
                {#each Object.entries(record).filter(([key]) => key !== '_filenameKey') as [key, value] (key)}
                  {#if value && value !== '' && (!Array.isArray(value) || value.length > 0)}
                    <div class="flex w-full flex-col items-start gap-1">
                      <div class="flex items-center gap-2">
                        <span
                          class="inline-flex h-7 w-7 items-center justify-center rounded-full border border-green-200 bg-white shadow"
                        >
                          <svg
                            class="h-5 w-5"
                            fill="none"
                            stroke="#176a2a"
                            stroke-width="2.2"
                            viewBox="0 0 24 24"
                            aria-hidden="true"
                          >
                            <circle cx="12" cy="12" r="10" />
                            <line x1="12" y1="8" x2="12" y2="12" />
                            <circle cx="12" cy="16" r="1" />
                          </svg>
                        </span>
                        <span
                          class="text-left text-lg tracking-wide text-gray-900 capitalize drop-shadow-sm"
                        >
                          {key}
                        </span>
                      </div>

                      {#if Array.isArray(value)}
                        <div
                          class="wrap-break-words w-full rounded-lg border border-gray-100 bg-white/90 px-4 py-2 text-left text-lg text-gray-700 shadow"
                        >
                          <ul class="list-inside list-disc space-y-1">
                            {#each value as item, index (index)}
                              <li class="ml-2">
                                {#if typeof item === 'object' && item !== null}
                                  <pre
                                    class="inline rounded bg-gray-50 px-2 py-1 text-base">{JSON.stringify(
                                      item,
                                      null,
                                      2
                                    )}</pre>
                                {:else}
                                  <span>{item}</span>
                                {/if}
                              </li>
                            {/each}
                          </ul>
                        </div>
                      {:else}
                        <div
                          class="wrap-break-words w-full rounded-lg border border-gray-100 bg-white/90 px-4 py-2 text-left text-lg text-gray-700 shadow"
                        >
                          {#if key === 'url' && typeof value === 'string'}
                            <a
                              href={value}
                              target="_blank"
                              rel="noopener noreferrer"
                              class="break-all text-blue-600 underline hover:text-blue-800"
                            >
                              {value}
                            </a>
                          {:else}
                            {value}
                          {/if}
                        </div>
                      {/if}
                    </div>
                  {/if}
                {/each}
              {/if}
            </div>
          </div>
        </div>
      </div>
    {/if}
  </div>
</div>
