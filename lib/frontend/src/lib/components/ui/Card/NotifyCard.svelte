<script lang="ts">
  import { onDestroy } from 'svelte';
  import { createEventDispatcher } from 'svelte';
  import type { NotificationType } from '$types/notify';
  import { NOTIFICATION_COLORS, NOTIFICATION_DEFAULT_DURATION } from '$lib/constants';

  const dispatch = createEventDispatcher();

  let {
    type = 'info' as NotificationType,
    message = 'Default message',
    duration = NOTIFICATION_DEFAULT_DURATION,
    actions = []
  } = $props();

  let visible = $state(true);
  let timer: ReturnType<typeof setTimeout> | null = null;

  // Computed styles based on type using constants
  const borderColor = $derived(NOTIFICATION_COLORS[type].border);
  const backgroundColor = $derived(NOTIFICATION_COLORS[type].background);

  // Action button styles
  const actionButtonClass =
    'bg-green-100 border border-green-400 text-green-800 hover:bg-green-200 hover:text-green-900 focus:ring-green-400 py-2 px-6 text-base sm:text-lg font-semibold transition-all duration-150 focus:outline-none focus:ring-2 focus:ring-offset-1 inline-flex items-center justify-center gap-2 text-center rounded-full';

  $effect(() => {
    if (duration > 0 && visible) {
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        visible = false;
        dispatch('dismiss');
      }, duration);
    }
  });

  function handleClose() {
    visible = false;
    dispatch('dismiss');
  }

  onDestroy(() => {
    if (timer) clearTimeout(timer);
  });
</script>

{#if visible}
  <div
    class="mx-auto w-full max-w-xl"
    style="text-align: center;"
    role={type === 'error' ? 'alert' : 'status'}
    aria-live={type === 'error' ? 'assertive' : 'polite'}
  >
    <div
      class="notification-card"
      style="border: 2px solid {borderColor}; background: {backgroundColor}; padding: 1.5rem; border-radius: 1rem; min-height: 3rem; margin: 1rem 0; position: relative;"
    >
      <button
        class="close-btn"
        style="position: absolute; top: 8px; right: 8px; background: transparent; border: none; font-size: 1.5rem; cursor: pointer;"
        onclick={handleClose}
        aria-label="Dismiss notification"
        >X
      </button>

      {#if type === 'error'}
        <div class="alert alert-error w-full max-w-xl shadow-lg">
          <span class="font-semibold">{message}</span>
        </div>
      {:else if message}
        <div class="alert alert-{type} flex w-full max-w-xl flex-col items-center gap-4 shadow-lg">
          <span class="font-semibold">{message}</span>
        </div>
      {:else}
        <span style="color: #2563eb; font-weight: bold;"
          >NotifyCard rendered, but no message or error provided.</span
        >
      {/if}

      {#if actions && actions.length > 0}
        <div class="mt-4 flex flex-row justify-center gap-2">
          {#each actions as action (action.label)}
            <button class={actionButtonClass} onclick={action.callback}>
              {action.label}
            </button>
          {/each}
        </div>
      {/if}
    </div>
  </div>
{/if}
