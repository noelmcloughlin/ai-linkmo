<script lang="ts">
    import { onMount } from 'svelte';
    import { endpoint } from "$states/endpoint.svelte";
    import { schemaState } from "$states/schema.svelte";
    import { notify } from "$states/notify.svelte";
    import { uiState } from "$states/ui.svelte";
    import { initializeSchemaState } from "$utils/schema";
    import { devLog, devError } from "$utils/misc";
    import { NotifyCard } from "$components/ui/Card/index";
    import type { NexusRecord, ComputedSchemaFields } from "$types/index";
    import { RecordForm } from '.';

    // Props
    let {
        endpointKey = "",
        recordId = "",
        onRecordLoaded = (title: string) => { void title; }
    } = $props();

    let record = $state<NexusRecord | null>(null);
    let isLoading = $state(true);
    let error = $state<string | null>(null);
    let schemaLoaded = $state(false);
    let fieldSchema = $derived(schemaState.endpoints[endpointKey] as unknown as ComputedSchemaFields);

    async function fetchRecord() {
        if (!endpointKey || !recordId) {
            error = "Missing endpoint key or record ID.";
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
                    onRecordLoaded(record.name || record.id || "Record");
                }
            } else if (data.items && data.items.length > 0) {
                const foundRecord = data.items.find((item: NexusRecord) => item.id === recordId);
                if (foundRecord) {
                    devLog(`[RecordViewer] Record found in items array`, foundRecord);
                    record = foundRecord;
                } else {
                    devError(`[RecordViewer] Record '${recordId}' not found. Available IDs:`, data.items.map((item: NexusRecord) => item.id));
                    throw new Error(`Record with ID '${recordId}' not found.`);
                }
            } else {
                throw new Error(`No record found with ID '${recordId}'.`);
            }
        } catch (err) {
            error = err instanceof Error ? err.message : "Failed to load record";
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

<div class="min-h-screen flex flex-col items-center justify-start pt-8 px-4">
    <div class="w-full max-w-7xl">
        <div class="mb-5 relative" style="z-index: 100;">
            <!-- eslint-disable svelte/no-navigation-without-resolve -->
             <a href="/"
             class="text-white hover:text-green-300 transition-colors text-lg font-semibold inline-block px-4 py-2 rounded-lg bg-black/20 hover:bg-black/30">
                Back to Browse
            </a>
        </div>

        {#if isLoading}
            <NotifyCard type="info" message="Loading record..." />
        {:else if error}
            <NotifyCard type="error" message={error} />
        {:else if record && fieldSchema}
            <!-- Card Holder styling - same as CardHolder.svelte -->
            <div class={`p-[2.5px] rounded-3xl bg-linear-to-br from-[#43b02a] via-blue-100 to-blue-400 w-full mx-auto mb-8 px-2 sm:px-4 ${uiState.cardWidthClass}`}>
                <div class="relative w-full rounded-[calc(1.5rem-2.5px)] overflow-hidden shadow-3xl bg-white/70 backdrop-blur-lg transition-transform hover:scale[1.018] hover:shadow-green-200/80 duration-200 group border-2 border-transparent mx-auto flex items-start justify-center">
                    <!-- Vertical Accent bar -->
                    <div class="absolute left-0 top-0 h-full w-2 bg-linear-to-b from-[#43b02a] via-green-200 to-green-100 rounded-l-3xl">
                    </div>
                    <!-- Glassmorphism background layer with inner glow -->
                    <div class="absolute inset-0 bg-linear-to-br from-white/90 via-green-50/60 to-green-100/70 backdrop-blur-2xl z-0 shadow-[0_0_32px_8px_#bbf7d0_inset]"></div>
                    
                    <div class="relative z-10 px-6 sm:px-8 md:px-10 py-6 sm:py-8 flex flex-col gap-4 w-full">
                        <!-- Fields Grid - same layout as RecordForm -->
                        <div class="grid grid-cols-1 sm:grid-cols-1 gap-x-6 gap-y-4 w-full">
                            {#if fieldSchema?.displayFields && Array.isArray(fieldSchema.displayFields) && fieldSchema.displayFields.length > 0}
                                {#each fieldSchema.displayFields as key (key)}
                                    <div class="flex flex-col items-start gap-1 w-full">
                                        <!-- Field label with icon - same as RecordForm -->
                                        <div class="flex items-center gap-2">
                                            <span class="inlie-flex items-center justify-center w-7 h-7 rounded-full bg-white shadow border border-green-200">
                                                <svg class="w-5 h-5" fill="none" stroke="#176a2a" stroke-width="2.2" viewBox="0 0 24 24">
                                                    <circle cx="12" cy="12" r="10" />
                                                    <line x1="12" y1="8" x2="12" y2="12" />
                                                    <circle cx="12" cy="16" r="1" />
                                                </svg>
                                            </span>

                                            <span class="text-gray-900 text-left text-lg tracking-wide drop-shadow-sm">
                                                {key}
                                                {#if fieldSchema?.fieldTypes?.[key] && !fieldSchema.fieldTypes[key].includes("null")}
                                                    <span class="text-orange-500 font-bold ml-1" title="Required">*</span>
                                                {/if}

                                                {#if fieldSchema?.fieldTypes?.[key]}
                                                    {#if !fieldSchema.fieldTypes[key].includes("null")}
                                                        <span class="italic text-orange-500 font-bold text-base ml-2">(type: {fieldSchema.fieldTypes[key]})</span>
                                                    {:else}
                                                        <span class="italic text-gray-400 text-base ml-2">(type: {fieldSchema.fieldTypes[key]})</span>
                                                    {/if}
                                                {/if}
                                            </span>
                                        </div>

                                        <!-- Field value -->
                                        {#if record?.[key] && record[key] !== "" && (!Array.isArray(record[key]) || record[key].length > 0)}
                                            {#if Array.isArray(record[key])}
                                                <div class="text-gray-900 text-lg wrap-break-words text-left bg-white/90 rounded-lg px-4 py-2 shadow border border-gray-100 w-full">
                                                    <ul class="list-disc list-inside space-y-1">
                                                        {#each record[key] as item, index (index)}
                                                            <li class="ml-2">
                                                                {#if typeof item === "object" && item !== null}
                                                                    <pre class="inline text-lg bg-gray-50 px-2 py-1 rounded">{JSON.stringify(item, null, 2)}</pre>
                                                                {:else}
                                                                    <span>{item}</span>
                                                                {/if}
                                                            </li>
                                                        {/each}
                                                    </ul>
                                                </div>
                                            {:else}
                                                <div class="text-gray-1100 text-lg wrap-break-words text-left bg-white/90 rounded-lg px-4 py-2 shadow border border-gray-100 w-full">
                                                    {#if key === "url" && typeof record[key] === "string"}
                                                        <a href="{record[key]}" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline break-all hover:text-blue-800">
                                                            {record[key]}
                                                        </a>
                                                    {:else}
                                                        {record[key]}
                                                    {/if}
                                                </div>
                                            {/if}
                                        {:else}
                                            <span class="text-gray-600 text-lg italic bg-white/90 rounded-lg px-4 py-2 shadow border border-gray-100 w-full">
                                                (empty)
                                            </span>
                                        {/if}

                                        <!-- Field Description -- same as RecordForm -->
                                        {#if fieldSchema?.fieldDescriptions?.[key]}
                                             <span class="text-blue-400 text-md ml-2">{fieldSchema.fieldDescriptions[key]}</span>
                                        {/if}
                                    </div>
                                {/each}
                            {:else}
                                <!-- Fallback: display all fields if displayFields not avaialble -->
                                {#each Object.entries(record).filter(([key]) => key !== "_filenameKey") as [key, value] (key)}
                                    {#if value && value !== "" && (!Array.isArray(value) || value.length > 0)}
                                        <div class="flex flex-col items-start gap-1 w-full">
                                            <div class="flex items-center gap-2">
                                                <span class="inline-flex items-center justify-center w-7 h-7 rounded-full bg-white shadow border border-green-200">
                                                    <svg class="w-5 h-5" fill="none" stroke="#176a2a" stroke-width="2.2" viewBox="0 0 24 24">
                                                        <circle cx="12" cy="12" r="10" />
                                                        <line x1="12" y1="8" x2="12" y2="12" />
                                                        <circle cx="12" cy="16" r="1" />
                                                    </svg>
                                                </span>
                                                <span class="text-gray-900 text-left text-lg tracking-wide drop-shadow-sm capitalize">
                                                    {key}
                                                </span>
                                            </div>

                                            {#if Array.isArray(value)}
                                                <div class="text-gray-700 text-log wrap-break-words text-left bg-white/90 roundede-lg px-4 py-2 shadow border border-gray-100 w-full">
                                                    <ul class="list-disc list-inside space-y-1">
                                                        {#each value as item, index (index)}
                                                            <li class="ml-2">
                                                                {#if typeof item === "object" && item !== null}
                                                                    <pre class="inline text-base bg-gray-50 px-2 py-1 rounded">{JSON.stringify(item, null, 2)}</pre>
                                                                {:else}
                                                                    <span>{item}</span>
                                                                {/if}
                                                            </li>
                                                        {/each}
                                                    </ul>
                                                </div>
                                            {:else}
                                                <div class="text-gray-700 text-lg wrap-break-words text-left bg-white/90 rounded-lg px-4 py-2 shadow border border-gray-100 w-full">
                                                    {#if key === "url" && typeof value === "string"}
                                                        <a href="{value}" target="_blank" rel="noopener noreferrer" class="text-blue-600 underline break-all hover:text-blue-800">
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