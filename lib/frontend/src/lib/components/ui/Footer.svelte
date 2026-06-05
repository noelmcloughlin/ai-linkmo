<script lang="ts">
  import {
    GITHUB_REPO_URL,
    AI_ATLAS_NEXUS_URL,
    AI_ONTOLOGY_URL,
    SVELTE_URL,
    VITE_URL,
    LINKML_URL,
    FINOS_URL,
    APP_LOGO_PATH,
    APP_NAME
  } from '$lib/constants';

  // CSS class constants for links
  const LINK_CLASS = 'flex items-center gap-2 group text-white';
  const LINK_TEXT_CLASS = 'text-sm font-normal';
  const LINK_TEXT_CLASS_BOLD = 'text-sm font-semibold';
</script>

<footer
  class="relative z-40 mt-auto w-full border-t border-blue-200 bg-linear-to-r from-[#43b02a] via-blue-100 to-blue-400 py-4 text-white"
>
  <div class="w-full px-4">
    <!-- single row layout is fine -->
    <div class="flex flex-col items-start justify-between gap-4 lg:flex-row lg:items-center">
      <!-- Left side -->
      <div class="flex flex-row items-center gap-4">
        <a
          href={FINOS_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-blue-300"
          aria-label="FINOS website (Fintech Open Source Foundation)"
        >
          <svg
            class="h-6 w-6"
            viewBox="0 0 200 200"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <circle cx="100" cy="100" r="95" fill="#0086bf" />
            <path d="M60 70h80v15H60zm0 25h60v15H60zm0 25h40v15H60z" fill="white" />
          </svg>
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">FINOS</span>
        </a>

        <a
          href={AI_ATLAS_NEXUS_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-gray-800"
          aria-label="AI Atlas Nexus website"
        >
          <img
            src={APP_LOGO_PATH}
            alt="AI Atlas Nexus logo"
            class="h-8 w-8 rounded-full border border-gray-700"
          />
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">AI Atlas Nexus</span>
        </a>

        <a
          href="https://linkml.io/linkml/get-involved/Community-Meetings.html"
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-blue-300"
          aria-label="LinkML Community"
        >
          <svg
            class="h-6 w-6"
            viewBox="0 0 24 24"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M10.59 13.41c.41.39.41 1.03 0 1.42-.39.39-1.03.39-1.42 0a5.003 5.003 0 0 1 0-7.07l3.54-3.54a5.003 5.003 0 0 1 7.07 0 5.003 5.003 0 0 1 0 7.07l-1.49 1.49c.01-.82-.12-1.64-.4-2.42l.47-.48a2.982 2.982 0 0 0 0-4.24 2.982 2.982 0 0 0-4.24 0l-3.53 3.53a2.982 2.982 0 0 0 0 4.24zm2.82-4.24c.39-.39 1.03-.39 1.42 0a5.003 5.003 0 0 1 0 7.07l-3.54 3.54a5.003 5.003 0 0 1-7.07 0 5.003 5.003 0 0 1 0-7.07l1.49-1.49c-.01.82.12 1.64.4 2.43l-.47.47a2.982 2.982 0 0 0 0 4.24 2.982 2.982 0 0 0 4.24 0l3.53-3.53a2.982 2.982 0 0 0 0-4.24.973.973 0 0 1 0-1.42z"
            />
          </svg>
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">LinkML Community Meetings</span>
        </a>
      </div>

      <!-- Center -->
      <div class="flex flex-row items-center gap-4">
        <a
          href={GITHUB_REPO_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-green-100"
          aria-label="GitHub Repository"
        >
          <svg
            class="h-6 w-6 transition-colors group-hover:text-green-100"
            fill="#1a202c"
            viewBox="0 0 24 24"
          >
            <path
              d="M12 2C6.477 2 2 6.484 2 12.021c0 4.428 2.865 8.184 6.839 9.504.5.092.682-.217.682-.482 0-.237-.009-.868-.014-1.703-2.782.605-3.369-1.342-3.369-1.342-.454-1.155-1.11-1.463-1.11-1.463-.908-.62.069-.608.069-.608 1.004.07 1.532 1.032 1.532 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.339-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.987 1.029-2.686-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.025A9.564 9.564 0 0 1 12 6.844c.85.004 1.705.115 2.504.337 1.909-1.295 2.748-1.025 2.748-1.025.546 1.378.202 2.397.1 2.65.64.699 1.028 1.593 1.028 2.686 0 3.847-2.338 4.695-4.566 4.944.359.309.678.919.678 1.852 0 1.336-.012 2.417-.012 2.747 0 .267.18.577.688.48C19.138 20.2 22 16.447 22 12.021 22 6.484 17.523 2 12 2Z"
            />
          </svg>
          <span class={LINK_TEXT_CLASS_BOLD} style="color: #1a202c;">LinkMO</span>
        </a>
      </div>

      <!-- Right side -->
      <div class="flex flex-row items-center gap-4">
        <a
          href={AI_ONTOLOGY_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-gray-800"
          aria-label="AI Ontology"
        >
          <img
            src={APP_LOGO_PATH}
            alt="{APP_NAME} logo"
            class="h-8 w-8 rounded-full border border-gray-700"
          />
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">AI Ontology</span>
        </a>

        <a
          href={LINKML_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-blue-300"
          aria-label="LinkML website"
        >
          <svg
            class="h-6 w-6"
            viewBox="0 0 24 24"
            fill="currentColor"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M10.59 13.41c.41.39.41 1.03 0 1.42-.39.39-1.03.39-1.42 0a5.003 5.003 0 0 1 0-7.07l3.54-3.54a5.003 5.003 0 0 1 7.07 0 5.003 5.003 0 0 1 0 7.07l-1.49 1.49c.01-.82-.12-1.64-.4-2.42l.47-.48a2.982 2.982 0 0 0 0-4.24 2.982 2.982 0 0 0-4.24 0l-3.53 3.53a2.982 2.982 0 0 0 0 4.24zm2.82-4.24c.39-.39 1.03-.39 1.42 0a5.003 5.003 0 0 1 0 7.07l-3.54 3.54a5.003 5.003 0 0 1-7.07 0 5.003 5.003 0 0 1 0-7.07l1.49-1.49c-.01.82.12 1.64.4 2.43l-.47.47a2.982 2.982 0 0 0 0 4.24 2.982 2.982 0 0 0 4.24 0l3.53-3.53a2.982 2.982 0 0 0 0-4.24.973.973 0 0 1 0-1.42z"
            />
          </svg>
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">LinkML</span>
        </a>

        <a
          href={SVELTE_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-orange-400"
          aria-label="Svelte website"
        >
          <svg
            class="h-7 w-7"
            viewBox="0 0 98.1 118"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              fill="#FF3E00"
              d="M91.8 15.6C80.9-0.1 59.2-4.7 43.6 5.2L16.1 22.8C8.6 27.5 3.4 35.2 1.9 43.9c-1.3 7.3-0.2 14.8 3.3 21.3c-2.4 3.6-4 7.6-4.7 11.8c-1.6 8.9 0.5 18.1 5.7 25.4c11 15.7 32.6 20.3 48.2 10.4l27.5-17.5c7.5-4.7 12.7-12.4 14.2-21.1c1.3-7.3 0.2-14.8-3.3-21.3c2.4-3.6 4-7.6 4.7-11.8C99.2 32.1 97.1 22.9 91.8 15.6"
            />
            <path
              fill="#FFFFFF"
              d="M40.9 103.9c-8.9 2.3-18.2-1.2-23.4-8.7c-3.2-4.4-4.4-9.9-3.5-15.3c0.2-0.9 0.4-1.7 0.6-2.6l0.5-1.6l1.4 1c3.3 2.4 6.9 4.2 10.8 5.4l1 0.3l-0.1 1c-0.1 1.4 0.3 2.9 1.1 4.1c1.6 2.3 4.4 3.4 7.1 2.7c0.6-0.2 1.2-0.4 1.7-0.7L65.5 72c1.4-0.9 2.3-2.2 2.6-3.8c0.3-1.6-0.1-3.3-1-4.6c-1.6-2.3-4.4-3.3-7.1-2.6c-0.6 0.2-1.2 0.4-1.7 0.7l-10.5 6.7c-1.7 1.1-3.6 1.9-5.6 2.4c-8.9 2.3-18.2-1.2-23.4-8.7c-3.1-4.4-4.4-9.9-3.4-15.3c0.9-5.2 4.1-9.9 8.6-12.7l27.5-17.5c1.7-1.1 3.6-1.9 5.6-2.5c8.9-2.3 18.2 1.2 23.4 8.7c3.2 4.4 4.4 9.9 3.5 15.3c-0.2 0.9-0.4 1.7-0.7 2.6l-0.5 1.6l-1.4-1c-3.3-2.4-6.9-4.2-10.8-5.4l-1-0.3l0.1-1c0.1-1.4-0.3-2.9-1.1-4.1c-1.6-2.3-4.4-3.3-7.1-2.6c-0.6 0.2-1.2 0.4-1.7 0.7L32.4 46.1c-1.4 0.9-2.3 2.2-2.6 3.8s0.1 3.3 1 4.6c1.6 2.3 4.4 3.3 7.1 2.6c0.6-0.2 1.2-0.4 1.7-0.7l10.5-6.7c1.7-1.1 3.6-1.9 5.6-2.5c8.9-2.3 18.2 1.2 23.4 8.7c3.2 4.4 4.4 9.9 3.5 15.3c-0.9 5.2-4.1 9.9-8.6 12.7l-27.5 17.5C44.8 102.5 42.9 103.3 40.9 103.9"
            />
          </svg>
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">Svelte</span>
        </a>

        <a
          href={VITE_URL}
          target="_blank"
          rel="noopener noreferrer"
          class="{LINK_CLASS} hover:text-purple-400"
          aria-label="Vite website"
        >
          <svg
            class="h-6 w-6"
            viewBox="0 0 410 404"
            xmlns="http://www.w3.org/2000/svg"
            aria-hidden="true"
          >
            <path
              fill="#41B883"
              d="M399.641 59.525L215.643 388.545c-3.799 6.789-13.559 6.829-17.415.073L10.812 59.556c-4.205-7.368 2.114-16.339 10.475-14.849l184.213 32.916a10.04 10.04 0 0 0 3.546-.005l180.343-32.87c8.334-1.519 14.673 7.404 10.252 14.777Z"
            />
            <path
              fill="#FFD028"
              d="M292.965 1.574l-136.39 26.73a4.96 4.96 0 0 0-4.01 4.57l-8.39 141.622a4.965 4.965 0 0 0 6.063 5.137l37.974-8.769a4.965 4.965 0 0 1 5.965 5.816l-11.275 55.243a4.965 4.965 0 0 0 6.299 5.748l23.454-7.124c3.358-1.021 6.668 1.928 5.978 5.391l-17.928 86.825c-1.058 5.18 5.81 8.013 8.691 3.566l1.924-2.974 111.131-221.75c1.722-3.434-1.246-7.385-5.057-6.653l-39.082 7.546c-3.435.66-6.359-2.535-5.421-5.91l25.495-88.349c.938-3.385-1.999-6.586-5.422-5.917Z"
            />
          </svg>
          <span class={LINK_TEXT_CLASS} style="color: #1a202c;">Vite</span>
        </a>
      </div>
    </div>
  </div>
</footer>
