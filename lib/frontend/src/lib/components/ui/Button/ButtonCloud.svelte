<script lang="ts">
    /**
     * ButtonCloud - A component for displaying buttons in a flowing, wrapped layout,
     * like tags or chips. Supports random distributon for more organic appearances.
    */
   import type { Snippet } from 'svelte';
   import { onMount } from 'svelte';

   let {
    class: className = '',
    gap = '0.5rem',
    padding = '0.5rem 0.75rem',
    background = 'rgba(0, 0, 0, 0.15)',
    justifyContent = 'center',
    randomize = false,
    children
   }: {
    class?: string;
    gap?: string;
    padding?: string;
    background?: string;
    justifyContent?: "flex-start" | "center" | "flex-end" | "space-between" | "space-around";
    randomize?: boolean;
    children: Snippet;
   } = $props();

   let containerRef: HTMLDivElement;
   let buttonCount = $state(0);

   // Generate random justification if randomize is true
   const cloudJustify = $derived(
    randomize ? ([
        'flex-start',
        'center',
        'flex-end',
        'space-around'
    ] as const)[Math.floor(Math.random() * 4)] : justifyContent
   );

   // Apply extra spacing for small button counts to create visual interest
   const hasSmallButtonCount = $derived(buttonCount > 0 && buttonCount < 4);

    onMount(() => {
     // Count the number of buttons after the component has mounted
     buttonCount = containerRef.querySelectorAll('button').length;
    });
</script>

<div
    bind:this={containerRef}
    class={`button-cloud ${className}`}
    class:randomize={randomize}
    class:small-button-count={hasSmallButtonCount}
    style="
        display: flex;
        flex-direction: row;
        flex-wrap: wrap;
        gap: {gap};
        padding: {padding};
        background: {background};
        align-items: center;
        justify-content: {cloudJustify};
        {hasSmallButtonCount ? 'gap: 1rem;' : ''};
    "
    >
    {@render children()}    
</div>

<style>
    .button-cloud {
        box-sizing: border-box;
    }

    .button-cloud :global(button) {
        width: fit-content;
        flex-shrink: 0;
    }

    /* Enhanced spacing for small button counts (<4)) for visual interest */
    .button-cloud.small-count :global(button) {
        margin: 0.5rem 0.75rem;
    }

    .button-cloud.small-count :global(button:nth-child(2n)) {
        margin-top: 2rem;
    }

    .button-cloud.small-count :global(button:nth-child(2n + 1)) {
        margin-bottom: 1.5rem;
    }

    /* Randomized cloud effects */
    .button-cloud.randomized {
        justify-content: space-around;
    }

    .button-cloud.randomized :global(button:nth-child(3n+1)) {
        order: 2;
    }

    .button-cloud.randomized :global(button:nth-child(3n+2)) {
        order: 1;
    }

    .button-cloud.randomized :global(button:nth-child(3n)) {
        order: 3;
    }

    .button-cloud.randomized :global(button:nth-child(5n+1)) {
        margin-left: 0.25rem;
    }

    .button-cloud.randomized :global(button:nth-child(5n+3)) {
        margin-right: 0.5rem;
    }

    .button-cloud.randomized :global(button:nth-child(7n+2)) {
        margin-right: 0.75rem;
    }

    .button-cloud.randomized :global(button:nth-child(7n+4)) {
        margin-left: 0.5rem;
    }
</style>