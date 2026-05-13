/// <reference types="vite/client" />
// brings in Vite's ambient declarations which include
// side-effect CSS imports (*.css, *.scss, etc.),

import type { SvelteComponent } from 'svelte';

declare module '*.svelte' {
  const value: typeof SvelteComponent;
  export default value;
}
