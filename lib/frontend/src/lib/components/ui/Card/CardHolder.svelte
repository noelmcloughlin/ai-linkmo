<script lang="ts">
  import { DisplayCard, NotifyCard } from '$components/ui/Card/index';
  import { RecordForm } from '$components/ui/Record/index';
  import { untrack } from 'svelte';
  import { endpoint, cardState, schemaState, filtered, notify, uiState } from '$states/index';
  import {
    handleFormAction,
    handleDisplaycardEditButton,
    handleDisplaycardAddButton,
    handleFormDelete,
    resetCardAndAsides
  } from '$utils/card';
  import type { ComputedSchemaFields, NexusRecord } from '$types/index';

  // $derived gives synchronous reactivity — updates the moment schemaState.endpoints changes
  const fieldSchema = $derived(
    schemaState.endpoints[endpoint.current] as unknown as ComputedSchemaFields
  );

  // Ensure cardState.item is always valid for filteredResults
  $effect(() => {
    untrack(() => {
      cardState.item =
        filtered.items.length === 0 ? 0 : Math.min(cardState.item, filtered.items.length - 1);
    });
  });
</script>

<div
  class={`mx-auto mb-8 w-full rounded-3xl bg-linear-to-br from-[#43b02a] via-blue-100 to-blue-400 p-[2.5px] px-2 sm:px-4 ${uiState.cardWidthClass}`}
>
  <!-- Glassmorphism background + inner glow on the container itself -->
  <div
    class="group relative mx-auto flex w-full items-start justify-center overflow-hidden rounded-[calc(1.5rem-2.5px)] border-2 border-transparent bg-linear-to-br from-white/90 via-green-50/60 to-green-100/70 shadow-[0_0_32px_8px_#bbf7d0_inset] backdrop-blur-lg transition-shadow duration-200 hover:shadow-green-200/80"
  >
    <!-- Vertical Accent bar -->
    <div
      class="absolute top-0 left-0 h-full w-2 rounded-l-3xl bg-linear-to-b from-[#43b02a] via-green-200 to-green-100"
    ></div>
    <div class="flex w-full flex-col gap-4 px-6 py-6 sm:px-8 sm:py-8 md:px-10">
      {#if endpoint.isLoading}
        <NotifyCard type="info" message="Loading data..." />
      {:else if cardState.type === 'add' || cardState.type === 'edit'}
        <RecordForm
          {fieldSchema}
          record={cardState.editRecord}
          mode={cardState.type}
          onSave={handleFormAction(endpoint.current, cardState.type)}
          onCancel={resetCardAndAsides}
          onDelete={(e: CustomEvent<{ record: NexusRecord }>) =>
            handleFormDelete(endpoint.current, e)}
        />
      {:else if cardState.type === 'display'}
        <DisplayCard
          {fieldSchema}
          filteredItems={filtered.items}
          on:edit={(e: CustomEvent<{ record: NexusRecord }>) => handleDisplaycardEditButton(e)}
          on:add={() => handleDisplaycardAddButton()}
        />
      {:else if cardState.type === 'notify' || notify.getAll().length > 0}
        {#each notify.getAll() as notification, i (notification.id ?? i)}
          <NotifyCard
            type={notification.type}
            message={notification.message}
            duration={notification.duration}
            actions={notification.actions}
            on:dismiss={() => notify.dismiss(notification.id ?? i)}
          />
        {/each}
      {:else}
        <NotifyCard type="info" message="No card state defined" duration={0} />
      {/if}
    </div>
  </div>
</div>
