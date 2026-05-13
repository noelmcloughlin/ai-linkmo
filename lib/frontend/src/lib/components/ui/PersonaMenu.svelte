<script lang="ts">
  import { DEFAULT_AVATAR } from "$lib/constants";
  import { onMount } from "svelte";

  // Props: Runes
  const { personas, user, onSelectPersona, onLogout } = $props();

  let showPersonaMenu = $state(false);

  function togglePersonaMenu() {
    showPersonaMenu = !showPersonaMenu;
  }

  // Utility function to handle clicks outside a specific element
  function handleClick(event: MouseEvent, selector: string, callback: () => void) {
    if (!(event.target as Element).closest(selector)) {
      callback();
    }
  }

  onMount(() => {
    const handleOutsideClick = (event: MouseEvent) => {
      handleClick(event, ".persona-menu-container", () => {
        showPersonaMenu = false;
      });
    }

    document.addEventListener("click", handleOutsideClick);
    return () => {
      document.removeEventListener("click", handleOutsideClick);
    };
  })

  function handlePersonaClick(persona: { name: string; avatar?: string }) {
    onSelectPersona(persona);
    showPersonaMenu = false;   // Close menu after selection
  }

  function handleLogoutClick() {
    togglePersonaMenu();
    onLogout();
  }
</script>

<div class="persona-menu-container">
  <button
    class="persona-toggle"
    onclick={togglePersonaMenu}
    aria-haspopup="true"
    aria-expanded={showPersonaMenu}
  >
    <img
      src={user.avatar || DEFAULT_AVATAR}
      alt="avatar"
      class="rounded-full w-8 h-8 border border-blue-200 shadow"
    />
    <span class="text-white font-semibold text-base">{user.name}</span>
    <svg
      class="w-4 h-4 text-white ml-1"
      fill="none"
      stroke="currentColor"
      stroke-width="2"
      viewBox="0 0 24 24"
    >
      <path d="M19 9l-7 7-7-7" />
    </svg>
  </button>
 
  {#if user && showPersonaMenu}
    <div class="persona-menu">
      <div class="persona-menu-wrapper">
        {#each personas as p (p.name)}
          <button class="persona-item" onclick={() => handlePersonaClick(p)}>
            <img
              src={p.avatar || DEFAULT_AVATAR}
              alt={p.name}
              class="rounded-full w-6 h-6 border border-blue-200"
            />
            <span class="text-base">{p.name}</span>
            {#if p.name === user.name}
              <svg
                class="w-4 h-4 text-green-500 ml-auto"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                viewBox="0 0 24 24"
              >
                <path d="M5 13l4 4L19 7" />
              </svg>
            {/if}
          </button>
        {/each}
        <div class="persona-divider"></div>
        <button class="persona-logout" onclick={handleLogoutClick}>
          <svg
            class="w-4 h-4"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            viewBox="0 0 24 24"
          >
            <path d="M17 16l4-4m0 0l-4-4m4 4H7" />
            <path d="M3 12a9 9 0 1 1 18 0 9 9 0 0 1-18 0z" />
          </svg>
          Logout
        </button>
      </div>
    </div>
  {/if}
</div>
 
<style>
  .persona-menu-container {
    position: relative;
  }
 
  .persona-toggle {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    background: none;
    border: none;
    cursor: pointer;
  }
 
  .persona-menu {
    position: absolute;
    top: 100%;
    right: 0;
    min-width: 20rem;
    width: 20rem;
    background: white;
    border-radius: 0.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    z-index: 1000;
    box-sizing: border-box;
    overflow: hidden;
  }
 
  .persona-menu-wrapper {
    display: flex;
    flex-direction: column;
    width: 100%;
    padding: 0.25rem 0;
    box-sizing: border-box;
    align-items: stretch;
  }
 
  .persona-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    width: 100%;
    min-width: 0;
    background: none;
    border: none;
    cursor: pointer;
    text-align: left;
    box-sizing: border-box;
    justify-content: flex-start;
    flex-shrink: 0;
  }
 
  .persona-item:hover {
    background: #f0f0f0;
    width: 100%;
  }
 
  .persona-divider {
    width: 100%;
    height: 1px;
    background-color: #e5e7eb;
    margin: 0.25rem 0;
  }
 
  .persona-logout {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 1rem;
    width: 100%;
    min-width: 0;
    background: none;
    border: none;
    color: red;
    cursor: pointer;
    text-align: left;
    font-size: 1rem;
    box-sizing: border-box;
    justify-content: flex-start;
    flex-shrink: 0;
  }
 
  .persona-logout:hover {
    background: #ffe5e5;
    width: 100%;
  }
</style>
