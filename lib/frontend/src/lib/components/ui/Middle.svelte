<script lang="ts">
  import LeftAside from './LeftAside.svelte';
  import RightAside from './RightAside.svelte';
  import { ToggleButton } from './Button/index';
  import { CardHolder, NotifyCard } from './Card/index';
  import { onMount } from 'svelte';
  import debounce from 'debounce';
  import { initializeSchemaState } from '$utils/index';
  import { handleDisplaycardAddButton } from '$utils/card';
  import { endpoint, filtered, asides, uiState, cardState } from '$states/index';
  import './middle.css';

  // Optional lifecycle callback fired after this view mounts (used by App to
  // clear record-viewer state when the user lands on "/").
  let { onMounted = (): void => {} } = $props();

  // Synchronize right-aside state with UI-state
  $effect(() => {
    uiState.rightAsideOpen = asides.rightOpen;
  });

  onMount(() => {
    onMounted();
    // Open left aside on mount, except on small screens where the fixed
    // panels overlay the content instead of sitting beside it.
    // Must match the (max-width: 768px) overlay breakpoint in middle.css.
    const isSmallScreen = window.innerWidth <= 768;
    asides.leftToggle(!isSmallScreen);
    if (isSmallScreen && asides.rightOpen) {
      asides.rightToggle(false);
    }

    // Initialize schema state
    initializeSchemaState();

    // Sizing is CSS-driven; JS only tracks windowWidth for the card width
    // class and auto-closes the right aside on small screens.
    const onResize = debounce(() => {
      uiState.windowWidth = window.innerWidth;
      // Auto-close right aside on small screens to avoid overlapping content
      // (same <=768 breakpoint as the overlay media query in middle.css)
      if (window.innerWidth <= 768 && asides.rightOpen) {
        asides.rightToggle(false);
      }
    }, 100);
    window.addEventListener('resize', onResize);

    // Cleanup listener on component destroy
    return () => {
      window.removeEventListener('resize', onResize);
    };
  });

  // Computed value or whether to show CardHolder
  const shouldShowCardHolder = $derived(
    !endpoint.isLoading || cardState.type === 'add' || cardState.type === 'edit'
  );

  // Computed value for whether to show empty state
  const shouldShowEmptyState = $derived(
    filtered.items.length === 0 &&
      !endpoint.isLoading &&
      cardState.type !== 'add' &&
      cardState.type !== 'edit'
  );
</script>

<!-- Toggle buttons are position:fixed, so they need no layout wrapper -->
<ToggleButton
  position="left"
  color="green"
  icon={asides.leftOpen ? '✕' : '☰'}
  ariaLabel={asides.leftOpen ? 'Close left navigation' : 'Open navigation'}
  style="top: var(--header-height); background: green; left: 1rem; position: fixed; transition: background 0.4s;"
  px={asides.leftOpen ? '2' : '3'}
  py={asides.leftOpen ? '1' : '2'}
  textSize={asides.leftOpen ? 'base' : 'lg'}
  onClick={() => asides.leftToggle(!asides.leftOpen)}
/>

<ToggleButton
  position="right"
  color="blue"
  icon={asides.rightOpen ? '✕' : '⚙'}
  ariaLabel={asides.rightOpen ? 'Close right navigation' : 'Open settings'}
  style="top: var(--header-height); right: 1rem; position: fixed; transition: background 0.2s;"
  px={asides.rightOpen ? '2' : '3'}
  py={asides.rightOpen ? '1' : '2'}
  textSize={asides.rightOpen ? 'base' : 'lg'}
  onClick={() => asides.rightToggle(!asides.rightOpen)}
/>

<main class="main-flex-container mx-auto flex w-full flex-1 flex-row items-stretch">
  <div id="left-aside" class="aside-container left {asides.leftOpen ? 'visible' : 'hidden'}">
    <LeftAside />
  </div>
  <div id="results-container" class="results-container">
    {#if endpoint.isLoading}
      <NotifyCard type="info" message="Loading ..." />
    {:else if shouldShowEmptyState}
      <NotifyCard
        type="warning"
        message="No items found"
        duration={0}
        actions={endpoint.isCurateMode
          ? [
              {
                label: 'Add new record',
                callback: () => handleDisplaycardAddButton()
              }
            ]
          : []}
      />
    {:else if shouldShowCardHolder}
      <CardHolder />
    {:else}
      <NotifyCard type="error" message="No items to display" />
    {/if}
  </div>
  <div
    id="right-aside-container"
    class="aside-container right {asides.rightOpen ? 'visible' : 'hidden'}"
  >
    <RightAside />
  </div>
</main>
