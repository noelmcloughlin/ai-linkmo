<script lang="ts">
  import { untrack } from 'svelte';
  import Button from '$components/ui/Button/Button.svelte';
  import SelectDropdown from '$components/ui/SelectDropdown.svelte';
  import '$components/ui/Card/shared-input.css';

  import { YOUR_FILES, ENDPOINTS, YOUR_DEFAULT_DATA_FILE, TEXTAREA_FIELDS } from '$lib/constants';

  import { FIELD_ENDPOINT_MAP_STATIC } from '$lib/states/filters.svelte';
  import { dataState } from '$states/data.svelte';
  import { endpoint } from '$states/endpoint.svelte';
  import type { NexusRecord } from '$types/yaml';

  // CSS class constants
  const FIELD_CONTAINER_CLASS = 'flex flex-col items-start gap-1 w-full';
  const FIELD_LABEL_WRAPPER_CLASS = 'flex items-center gap-2';
  const FIELD_ICON_CLASS =
    'inline-flex items-center justify-center w-7 h-7 rounded-full bg-white shadow border border-green-200';
  const FIELD_LABEL_TEXT_CLASS = 'text-gray-900 text-left text-base tracking-wide drop-shadow-sm';
  const FIELD_INPUT_CLASS = 'input input-bordered input-sm w-full pl-4';
  const REQUIRED_INDICATOR_CLASS = 'text-orange-500 font-bold ml-1';
  const FIELD_TYPE_OPTIONAL_CLASS = 'italic text-gray-400 text-sm ml-2';
  const FIELD_TYPE_REQUIRED_CLASS = 'italic text-orange-500 font-bold text-sm ml-2';
  const FIELD_DESCRIPTION_CLASS = 'text-gray-400 text-xs mt-2';

  // Props
  let {
    fieldSchema = {}, // Schema for the record form
    record = {} as NexusRecord, // Record data, can be empty
    mode = '', // Mode of the form (e.g., "add", "edit")
    onSave = () => {}, // Callback for saving the record
    onCancel = () => {}, // Callback for canceling the form
    onDelete = null // Optional for edit-mode
  } = $props();

  // Local reactive copy for editing, avoids mutating the record prop
  let localRecord = $state<NexusRecord>({} as NexusRecord);

  // Re-seed the local copy whenever the incoming record/mode/schema changes.
  // The seeded copy is written inside untrack so the effect only re-runs on
  // prop changes, not on its own writes.
  $effect(() => {
    const displayFields: string[] = fieldSchema.displayFields || [];
    const seeded: NexusRecord = record ? { ...record } : ({} as NexusRecord);

    // Initialize _filenameKey for new records if not set
    if (mode === 'add' && !seeded._filenameKey) {
      seeded._filenameKey = YOUR_DEFAULT_DATA_FILE;
    }

    // Auto-populate 'type' field from ENDPOINTS if fieldSchema.type is defined
    // and the record's type is not already set
    if (displayFields.includes('type') && !seeded.type) {
      const endpointConfig = ENDPOINTS.find((e) => e.key === endpoint.current);
      if (endpointConfig?.type) {
        seeded.type = endpointConfig.type;
      }
    }

    // Auto-populate 'isDefinedByTaxonomy' field from _filenameKey if it exists in schema
    if (displayFields.includes('isDefinedByTaxonomy') && seeded._filenameKey) {
      seeded.isDefinedByTaxonomy = seeded._filenameKey;
    }

    // Auto-populate 'dateCreated' for new records if available in schema
    if (mode === 'add' && displayFields.includes('dateCreated') && !seeded.dateCreated) {
      seeded.dateCreated = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    }

    // Auto-populate 'dateModified' for add/edit mode if available in schema
    if ((mode === 'add' || mode === 'edit') && displayFields.includes('dateModified')) {
      seeded.dateModified = new Date().toISOString().split('T')[0]; // YYYY-MM-DD
    }

    untrack(() => {
      localRecord = seeded;
    });
  });

  // Mapping fields that depend on the current endpoint selection.
  // These wil be merged with static mappings at runtime.
  const dynamicMappings: Record<string, string> = {
    broad_mappings: endpoint.current,
    close_mappings: endpoint.current,
    exact_mappings: endpoint.current,
    narrow_mappings: endpoint.current,
    related_mappings: endpoint.current
  };
  const FIELD_ENDPOINT_MAP: Record<string, string> = {
    ...FIELD_ENDPOINT_MAP_STATIC,
    ...dynamicMappings
  };

  // Get options for fields based on its mapping
  function getOptionsForField(fieldKey: string): Array<{ label: string; value: string }> {
    // only provide options for fields that have a mapping defined in the schema
    if (!Object.prototype.hasOwnProperty.call(FIELD_ENDPOINT_MAP, fieldKey)) {
      return [];
    }

    const targetEndpoint = FIELD_ENDPOINT_MAP[fieldKey];

    // Get records for both base endpoint and byod
    const allRecords: NexusRecord[] = [];

    // Base data - look for exact key match
    const baseData = dataState.items.find((nc) => nc.key === targetEndpoint);
    if (baseData?.items) {
      allRecords.push(...baseData.items);
    }

    // BYOD data - look for key with '&byod' suffix
    const byodKey = `${targetEndpoint}&byod`;
    const byodData = dataState.yourItems.find((nc) => nc.key === byodKey);
    if (byodData?.items) {
      allRecords.push(...byodData.items);
    }

    // Fallback: if not records found from target endpoint, extract unique values from current endpoint.
    if (allRecords.length === 0) {
      const currentData = dataState.items.find((nc) => nc.key === endpoint.current);
      const currentByodData = dataState.yourItems.find(
        (nc) => nc.key === `${endpoint.current}&byod`
      );

      const uniqueValues = [] as string[];
      const valueSet: Record<string, boolean> = {};

      [currentData, currentByodData].forEach((data) => {
        if (data?.items) {
          data.items.forEach((record: NexusRecord) => {
            const value = record[fieldKey];
            if (Array.isArray(value)) {
              value.forEach((v) => {
                if (v && !valueSet[v as string]) {
                  valueSet[v as string] = true;
                  uniqueValues.push(v as string);
                }
              });
            } else if (value && typeof value === 'string' && !valueSet[value]) {
              valueSet[value] = true;
              uniqueValues.push(value);
            }
          });
        }
      });
      return uniqueValues.map((id) => ({
        label: id,
        value: id
      }));
    }

    // Filter out current record ID when editing
    const currentRecordId = mode === 'edit' ? localRecord.id : null;

    // De-duplicate by ID
    const uniqueRecords: Record<string, NexusRecord> = {};
    allRecords
      .filter((r) => !currentRecordId || r.id !== currentRecordId)
      .forEach((r) => {
        uniqueRecords[r.id as string] = r;
      });

    // Filter by taxonomy when in curate mode
    let filteredRecords = Object.values(uniqueRecords).filter((r) => r.id);

    if (endpoint.isCurateMode && localRecord.isDefinedByTaxonomy) {
      const recordTaxonomy = localRecord.isDefinedByTaxonomy as string;
      filteredRecords = filteredRecords.filter((r) => r.isDefinedByTaxonomy === recordTaxonomy);
    }

    return filteredRecords.map((r) => {
      const desc = typeof r.description === 'string' ? r.description.substring(0, 50) : '';
      return {
        label: (r.id as string) + (desc ? ` - ${desc}...` : ''),
        value: r.id as string
      };
    });
  }

  // Check if field is an array type based on schema
  function isArrayField(fieldKey: string): boolean {
    const fieldType = fieldSchema.fieldTypes?.[fieldKey];
    return fieldType && fieldType.includes('array');
  }

  function handleInput(key: string, value: string | string[]) {
    const updates: Record<string, string | string[]> = { [key]: value };

    // when _filenameKey changes, also update isDefinedByTaxonomy if it exists in the schema
    if (key === '_filenameKey' && fieldSchema.displayFields?.includes('isDefinedByTaxonomy')) {
      updates.isDefinedByTaxonomy = value as string;
    }

    localRecord = { ...localRecord, ...updates };
  }

  function handleArraySelect(key: string, event: CustomEvent) {
    const selectedValue = event.detail;
    localRecord = { ...localRecord, [key]: selectedValue };
  }

  function save(event: Event) {
    event.preventDefault();
    if (typeof onSave === 'function') {
      onSave({ detail: { record: localRecord } });
    }
  }
</script>

<!-- Content-only: CardHolder provides the card shell (background, border,
     accent, padding), so no nested card wrapper is rendered here. -->
<div class="text-center text-base font-medium text-green-700">
  {mode === 'add' ? 'Add New Record' : 'Edit Record'}
</div>
<div class="flex w-full flex-row gap-3">
  <Button type="submit" variant="success" size="sm" className="flex-1 min-w-[100px]" on:click={save}>
    Save
  </Button>
  <Button
    type="button"
    variant="edit"
    size="sm"
    className="flex-1 min-w-[100px]"
    on:click={() => onCancel()}
  >
    Cancel
  </Button>
  {#if mode === 'edit' && typeof onDelete === 'function'}
    <Button
      type="button"
      variant="curate"
      size="sm"
      className="flex-1 min-w-[100px]"
      on:click={onDelete}
    >
      Delete
    </Button>
  {/if}
</div>

<form onsubmit={save} class="flex flex-col gap-4">
  <div class="grid w-full grid-cols-1 gap-x-6 gap-y-4 sm:grid-cols-1">
    {#if fieldSchema.includesTaxonomyField}
      <div class={FIELD_CONTAINER_CLASS}>
        <div class={FIELD_LABEL_WRAPPER_CLASS}>
          <span class={FIELD_ICON_CLASS}>
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
          <span class={FIELD_LABEL_TEXT_CLASS}>
            Taxonomy file <span class={REQUIRED_INDICATOR_CLASS} title="Required">*</span>
          </span>
        </div>

        {#if YOUR_FILES.length > 1}
          <select
            class="{FIELD_INPUT_CLASS} {mode === 'edit'
              ? 'cursor-not-allowed bg-gray-100'
              : ''}"
            value={localRecord._filenameKey}
            disabled={mode === 'edit'}
            required
            style="width:100%; min-width:0;"
            onchange={(e) => handleInput('_filenameKey', e.currentTarget.value)}
          >
            <option value="" disabled>Select taxonomy...</option>
            {#each YOUR_FILES as tax (tax.key)}
              <option value={tax.key}>{tax.key}</option>
            {/each}
          </select>
        {:else}
          <input class={FIELD_INPUT_CLASS} type="text" value={YOUR_FILES[0]?.key} readonly />
        {/if}
      </div>
    {/if}

    {#if Array.isArray(fieldSchema.displayFields)}
      {#each fieldSchema.displayFields.filter((k: string) => k !== 'dateCreated' && k !== 'dateModified' && k !== 'isDefinedByTaxonomy') as key (key)}
        <div class={FIELD_CONTAINER_CLASS}>
          <div class={FIELD_LABEL_WRAPPER_CLASS}>
            <span class={FIELD_ICON_CLASS}>
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
            <span class={FIELD_LABEL_TEXT_CLASS}>
              {key}
              {#if fieldSchema.fieldTypes && fieldSchema.fieldTypes[key] && !fieldSchema.fieldTypes[key].includes('null')}
                <span class={REQUIRED_INDICATOR_CLASS} title="Required">*</span>
              {/if}
              {#if fieldSchema.fieldTypes && fieldSchema.fieldTypes[key]}
                {#if !fieldSchema.fieldTypes[key].includes('null')}
                  <span class={FIELD_TYPE_REQUIRED_CLASS}
                    >(type: {fieldSchema.fieldTypes[key]})</span
                  >
                {:else}
                  <span class={FIELD_TYPE_OPTIONAL_CLASS}
                    >(type: {fieldSchema.fieldTypes[key]})</span
                  >
                {/if}
              {/if}
            </span>
          </div>

          {#if key === 'type'}
            <input
              class="{FIELD_INPUT_CLASS} cursor-not-allowed bg-gray-100"
              type="text"
              value={localRecord[key]}
              readonly
              disabled
              placeholder="Auto-populated from endpoint selection"
              style="width:100%; min-width:0;"
            />
          {:else if isArrayField(key) && getOptionsForField(key).length > 0}
            <SelectDropdown
              id={`field-${key}`}
              {key}
              multiple={true}
              options={getOptionsForField(key)}
              value={localRecord[key] as string}
              placeholder={`Select ${key}...`}
              clearable={true}
              on:select={(e: CustomEvent) => handleArraySelect(key, e)}
            />
          {:else if TEXTAREA_FIELDS.includes(key)}
            <textarea
              class="{FIELD_INPUT_CLASS} min-h-[100px] resize-y"
              value={localRecord[key] as string}
              oninput={(e) => handleInput(key, e.currentTarget.value)}
              required={key === 'id'}
              placeholder={fieldSchema.fieldDescriptions[key]
                ? fieldSchema.fieldDescriptions[key]
                : key == 'description'
                  ? 'Enter description...'
                  : `Enter ${key}...`}
              style="width:100%; min-width:0;"
            ></textarea>
          {:else}
            <input
              class={FIELD_INPUT_CLASS}
              type="text"
              value={localRecord[key] as string}
              oninput={(e) => handleInput(key, e.currentTarget.value)}
              required={key === 'id'}
              placeholder={fieldSchema.fieldDescriptions[key]
                ? fieldSchema.fieldDescriptions[key]
                : key === 'description'
                  ? 'Enter description...'
                  : `Enter ${key}...`}
              style="width:100%; min-width:0;"
            />
          {/if}
          {#if fieldSchema.fieldDescriptions && fieldSchema.fieldDescriptions[key]}
            <span class={FIELD_DESCRIPTION_CLASS}>
              {fieldSchema.fieldDescriptions[key]}
            </span>
          {/if}
        </div>
      {/each}
    {/if}
  </div>
</form>
