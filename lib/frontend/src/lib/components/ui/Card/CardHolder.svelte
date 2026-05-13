<script lang="ts">
    import { DisplayCard, NotifyCard } from '$components/ui/Card/index';
    import { RecordForm } from '$components/ui/Record/index';
    import { untrack } from 'svelte';
    import {
        endpoint,
        cardState,
        schemaState,
        filtered,
        notify,
        uiState,
    } from "$states/index";
    import {
        handleFormAction,
        handleDisplaycardEditButton,
        handleDisplaycardAddButton,
        handleFormDelete,
        resetCardAndAsides,
    } from "$utils/card";
    import type { ComputedSchemaFields, NexusRecord } from '$types/index';

    // $derived gives synchronous reactivity — updates the moment schemaState.endpoints changes
    const fieldSchema = $derived(schemaState.endpoints[endpoint.current] as unknown as ComputedSchemaFields);

    // Ensure cardState.item is always valid for filteredResults
    $effect(() => {
        untrack(() => {
            cardState.item =
                filtered.items.length === 0
                    ? 0
                    : Math.min(cardState.item, filtered.items.length - 1);
        });
    });
</script>

<div class={`p-[2.5px] rounded-3xl bg-linear-to-br from-[#43b02a] via-blue-100 to-blue-400 w-full mx-auto mb-8 px-2 sm:px-4 ${uiState.cardWidthClass}`}>
    <div class="relative w-full rounded-[calc(1.5rem-2.5px)] overflow-hidden shadow-3xl bg-white/70 backdrop-blur-lg transition-transform hover:scale[1.018] hover:shadow-green-200/80 duration-200 group border-2 border-transparent mx-auto flex items-start justify-center">
        <!-- Vertical Accent bar -->
        <div class="absolute left-0 top-0 h-full w-2 bg-linear-to-b from-[#43b02a] via-green-200 to-green-100 rounded-l-3xl">
        </div>
        <!-- Glassmorphism background layer with inner glow -->
        <div
            class="absolute inset-0 bg-linear-to-br from-white/90 via-green-50/60 to-green-100/70 backdrop-blur-2xl z-0 shadow-[0_0_32px_8px_#bbf7d0_inset]"
        ></div>
        <div class="relative z-10 px-6 sm:px-8 md:px-10 py-6 sm:py-8 flex flex-col gap-4 w-full">
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
                    on:edit={(e: CustomEvent<{ record: NexusRecord }>) =>
                        handleDisplaycardEditButton(e)}
                    on:add={() => handleDisplaycardAddButton()}
                />
            {:else if cardState.type === 'notify' || notify.getAll().length > 0}
                {#each notify.getAll() as notification, i (notification.id ?? i)}
                    <NotifyCard
                        type={notification.typeof}
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