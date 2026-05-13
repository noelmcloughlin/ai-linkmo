<script lang="ts">
    import { logInvalidEntry, isValidRecord } from "$utils/card";

    let { fieldSchema, record, showSchemaTips } = $props();

    const FIELD_LABEL_CLASS = "font-semibold text-gray-900 text-left text-base capitalize tracking-wide drop-shadow-sm";
    const FIELD_VALUE_CLASS = "text-gray-700 text-base break-words text-left bg-white/90 rounded-lg px-3 py-2 shadow border border-gray-100 group-hover:bg-blue-50/80 transition-colors duration-150";
    const FIELD_PLACEHOLDER_CLASS = "text-gray-400 text-base italic bg-white/90 rounded-lg px-3 py-2 shadow border border-gray-100 group-hover:bg-blue-50/80 transition-colors duration-150";
    const FIELD_TYPE_OPTIONAL_CLASS = "italic text-gray-400 text-sm ml-2";
    const FIELD_TYPE_REQUIRED_CLASS = "italic text-orange-500 font-bold text-sm ml-2";
    const FIELD_DESCRIPTION_CLASS = "text-blue-400 text-md ml-2";
</script>

{#if showSchemaTips && fieldSchema?.displayFields?.length > 0}
    {#each fieldSchema.displayFields as key (key)}
        <div class={FIELD_LABEL_CLASS}>
            {key}
            {#if fieldSchema?.fieldTypes?.[key]}
                {#if fieldSchema.fieldTypes[key].includes("null")}
                    <span class={FIELD_TYPE_REQUIRED_CLASS}>(type: {fieldSchema.fieldTypes[key]})</span>
                {:else}
                    <span class={FIELD_TYPE_OPTIONAL_CLASS}>(type: {fieldSchema.fieldTypes[key]})</span>
                {/if}
            {/if}
        </div>

        <div class="flex flex-col gap-1">
            {#if record?.[key] && record[key] !== "" && (!Array.isArray(record[key]) || record[key].length > 0)}
                {#if Array.isArray(record[key])}
                    <div class={FIELD_VALUE_CLASS}>
                        <ul class="list-disc list-inside space-y-1">
                            {#each record[key] as item, index (index)}
                                <li class="ml-2">
                                    {#if typeof item === 'object' && item !== null}
                                        <pre class="inline text-xs bg-gray-50 px-2 py-1 rounded">{JSON.stringify(item, null, 2)}</pre>
                                    {:else}
                                        <span>{item}</span>
                                    {/if}
                                </li>
                            {/each}
                        </ul>
                    </div>

                {:else}
                    <span class={FIELD_VALUE_CLASS}>
                        {#if key === 'url' && fieldSchema?.fieldTypes?.[key]?.includes('string') && typeof record[key] === 'string'}
                        <!-- eslint-disable svelte/no-navigation-without-resolve -->
                            <a href={record[key]}
                                 target="_blank"
                                 rel="noopener noreferrer"
                                 data-sveltekit-reload
                                 class="text-blue-600 underline break-all hover:text-blue-800"
                            >
                                {record[key]}
                            </a>
                        {:else}
                            {record[key]}
                        {/if}
                    </span>
                {/if}
            {:else}
                <span class={FIELD_PLACEHOLDER_CLASS}>
                    (empty)
                </span>
            {/if}

            {#if fieldSchema?.fieldDescriptions?.[key]}
                <span class={FIELD_DESCRIPTION_CLASS}>
                    {fieldSchema.fieldDescriptions[key]}
                </span>
            {/if}
        </div>
    {/each}
{:else if isValidRecord(record)}
        {#each Object.entries(record).filter(([key, value]) => {
            const isValid = typeof key === "string" && key !== "_filenameKey" && value !== undefined;
            if (!isValid && key !== "_filenameKey") {
                logInvalidEntry(key, value);
            }
            return isValid;
        }) as [key, value] (key)}

        {#if value && value !== "" && (!Array.isArray(value) || value.length > 0)}
            <div class={FIELD_LABEL_CLASS}>
                {key}
                {#if fieldSchema?.fieldTypes?.[key] && !fieldSchema.fieldTypes[key].includes("null")}
                    <span class="text-orange-500 font-bold ml-1" title="Required">*</span>
                {/if}
            </div>
            {#if Array.isArray(value)}
                <div class={FIELD_VALUE_CLASS}>
                    <ul class="list-disc list-inside space-y-1">
                        {#each value as item, index (index)}
                            <li class="ml-2">
                                {#if typeof item === 'object' && item !== null}
                                    <pre class="inline text-xs bg-gray-50 px-2 py-1 rounded">{JSON.stringify(item, null, 2)}</pre>
                                {:else}
                                    <span>{item}</span>
                                {/if}
                            </li>
                        {/each}
                    </ul>
                </div>
            {:else}
                <span class={FIELD_VALUE_CLASS}>
                    {#if key === 'url' && fieldSchema?.fieldTypes?.[key]?.includes('string') && typeof value === 'string'}
                        <a href={value}
                             target="_blank"
                             rel="noopener noreferrer"
                             data-sveltekit-reload
                             class="text-blue-600 underline break-all hover:text-blue-800"
                        >
                            {value}
                        </a>
                    {:else}
                        {value}
                    {/if}
                </span>
            {/if}
        {/if}
    {/each}
{:else}
    <span class="italic text-red-500">Invalid record</span>
    <!-- Just in case: do not access record.id or other properties here -->
{/if}