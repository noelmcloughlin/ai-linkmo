<script lang="ts">
    import { BYO_ICON_TEXT, APP_NAME, APP_LOGO_PATH, BYO_LOGO_PATH, ACME_LOGO_URL, FINOS_LOGO_URL } from '$lib/constants';
    import Button from "$components/ui/Button/Button.svelte";
    import PersonaMenu from "$components/ui/PersonaMenu.svelte";
    import { endpoint, authState, filtered, asides } from '$states/index';
    import { login, logout, personas, selectPersona } from '$utils/auth';
    import './header.css';

    // Props (runes)
    let {
        isRelatedMode = false,
        isRecordViewer = false,
        recordViewerTitle = ''
    } = $props();

    // Zenmode
    let zenMode = $state(false);

    function toggleZenMode() {
        zenMode = !zenMode;
        if (zenMode) {
            asides.hideAll();
        } else {
            asides.restore();
        }
    }

    $effect(() => {
        if (!authState.loggedIn && endpoint.isCurateMode) {
            // logout disables curation mode
            endpoint.setCurateMode(false);
        }
    })
</script>

<div class="header-container w-full">
    <div class="header-content bg-linear-to-r from-[#43b02a] via-blue-100 to-blue-400 shadow-md">

        <!-- Section 0: Bring your own Logo -->
        <div class="header-logo-section">
            {#if endpoint.isCurateMode}
                <img
                    src={BYO_ICON_TEXT === 'ACME' ? ACME_LOGO_URL : BYO_ICON_TEXT === 'FINOS' ? FINOS_LOGO_URL : BYO_LOGO_PATH}
                    alt="{BYO_ICON_TEXT} Logo"
                    class="header-logo"
                />
            {:else}
                <img src={APP_LOGO_PATH} alt="{APP_NAME} Logo" class="header-logo" />
            {/if}
            <span class="header-title">{APP_NAME}</span>
        </div>

        <!-- Section 1: Middle -->
        <div class="header-center">
            <span class="header-center-text flex items-center gap-2">
                {#if isRecordViewer}
                    <span class="text-green-1100 font-bold">[{endpoint.getLabel().toUpperCase()}]:</span>
                    <span class="text-gray-900">{recordViewerTitle || "Loading..."}</span>
                {:else}
                    {#if authState.loggedIn && endpoint.isCurateMode}
                        <span class="header-badge">{BYO_ICON_TEXT}</span>
                    {/if}
                    {isRelatedMode ? "RELATED" : ""}{endpoint.getLabel().toUpperCase()}

                    <span class="header-count">
                        {#key `${endpoint.isLoading ? "isLoading" : filtered.items.length}`}
                            {#if endpoint.isLoading}
                                <svg
                                    class="header-spinner"
                                    xmlns="http://www.w3.org/2000/svg"
                                    fill="none"
                                    viewBox="0 0 24 24"
                                >
                                    <circle
                                        class="opacity-25"
                                        cx="12"
                                        cy="12"
                                        r="10"
                                        stroke="currentColor"
                                        stroke-width="4"
                                    ></circle>
                                    <path
                                        class="opacity-75"
                                        fill="currentColor"
                                        d="M4 12a8 8 0 018-8V04a4 4 0 00-4 4H4z"
                                    ></path>
                                </svg>
                            {:else if filtered.items.length > 0}
                                <span class="header-count-badge">
                                    ({filtered.items.length})
                                </span>
                            {:else}
                                <span class="header-count-badge">
                                    (0)
                                </span>
                            {/if}
                        {/key}
                    </span>
                {/if}
            </span>
        </div>

        <!-- Section 3: Right -->
        <div class="header-user-section">
            <div class="flex items-center justify-between w-full gap-3">
                {#if !isRecordViewer}
                    <!-- Zen Mode Toggle -->
                    <button
                        onclick={toggleZenMode}
                        class="flex items-center gap-2 px-3 py-2 rounded-lg transition-all duration-200 {zenMode
                            ? 'bg-purple-600 hover:bg-purple-700 text-white shadow-lg'
                            : 'bg-white/80 hover:bg-white text-gray-700 shadow'}"
                        title={zenMode ? "Exit Zen Mode" : "Enter Zen Mode"}
                    >
                        <svg
                            class="w-5 h-5" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
                            {#if zenMode}
                                <path d="M8 3v3a2 2 0 0 1-2 2H3m18 0h-3a2 2  0 1-2-2V3m0 18v-3a2 2 0 0 1 2-2h3M3 16h3a2 2 0 0 1 2 2v3"/>
                            {:else}
                                <path d="M8 3H5a2 2 0 0 0-2 2v3m18 0V5a2 2 0 0-2-2h-3m0 18h3a2 2 0 0 0 2-2v-3M3 16v3a2 2 0 0 0 2 2h3"/>
                            {/if}
                        </svg>
                        <span class="text-sm font-medium">Zen</span>
                    </button>

                    {#if !authState.loggedIn}
                        <Button
                            variant="login"
                            size="lg"
                            on:click={() => {
                                login();
                            }}>Login
                        </Button>
                    {:else if authState.user}
                        <div class="persona-menu-wrapper">
                            <PersonaMenu
                                {personas}
                                user={authState.user}
                                onSelectPersona={selectPersona}
                                onLogout={() => { logout(); }}
                            />
                        </div>
                    {/if}
                {/if}
            </div>
        </div>
    </div>
</div>