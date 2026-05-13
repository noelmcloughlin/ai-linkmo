<script lang="ts">
  import LeftAside from './LeftAside.svelte';
  import RightAside from './RightAside.svelte';
  import { ToggleButton } from './Button/index';
  import { CardHolder, NotifyCard } from './Card/index';
  import { onMount } from 'svelte';
  import debounce from 'debounce';
  import { initializeSchemaState, handleResponsiveUI } from '$utils/index';
  import { handleDisplaycardAddButton } from '$utils/card';
  import { endpoint, filtered, asides, uiState, cardState } from '$states/index';
  import { HEADER_HEIGHT } from '$lib/constants';
  import "./middle.css";

  // Synchronize right-aside state with UI-state
  $effect(() => {
    uiState.rightAsideOpen = asides.rightOpen;
  });

  onMount(() => {
    asides.leftToggle(true); // Open left aside on mount
    // Initialize responsive UI
    handleResponsiveUI();

    // Initialize schema state
    initializeSchemaState();

    // Debounce resize handler to update uiState.windowWidth and responsive UI
    const onResize = debounce(() => {
      uiState.windowWidth = window.innerWidth;
      handleResponsiveUI();
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

<div class="main-content-container">
  <div class="main-flex-container relative flex w-full flex-1 flex-row items-stretch">
    <ToggleButton
      position="left"
      color="green"
      icon={asides.leftOpen ? '✕' : '☰'}
      ariaLabel={asides.leftOpen ? 'Close left navigation' : 'Open navigation'}
      style="top: calc({HEADER_HEIGHT}); background: green; left: 1rem; position: fixed; transition: background 0.4s;"
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
      style="top: calc({HEADER_HEIGHT}); right: 1rem; position: fixed; transition: background 0.2s;"
      px={asides.rightOpen ? '2' : '3'}
      py={asides.rightOpen ? '1' : '2'}
      textSize={asides.rightOpen ? 'base' : 'lg'}
      onClick={() => asides.rightToggle(!asides.rightOpen)}
    />

    <main class="mx-auto flex w-full flex-row">
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
  </div>
</div>
