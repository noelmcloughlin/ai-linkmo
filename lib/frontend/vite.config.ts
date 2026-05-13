
import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { fileURLToPath, URL } from 'node:url';

import { playwright } from '@vitest/browser-playwright';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
	plugins: [tailwindcss(), svelte()],
	resolve: {
		alias: {
			$lib: fileURLToPath(new URL('./src/lib', import.meta.url)),
			$components: fileURLToPath(new URL('./src/lib/components', import.meta.url)),
			$states: fileURLToPath(new URL('./src/lib/states', import.meta.url)),
			$types: fileURLToPath(new URL('./src/lib/types', import.meta.url)),
			$utils: fileURLToPath(new URL('./src/lib/utils', import.meta.url))
		},
	},
	server: {
		proxy: {
			// Proxy API requests (with query params or that don't have a second path segement)
			// This allows /risks?id=foo to proxy while /risk/foo routes client-side
			'^/(classes|risk|action|control|incident|benchmarkcard|evaluation|document|dataset|adapter|stakeholder|intrinsic|questionpolicy|principle|obligation|recommendation|vocabulary|model|task|taxonomy|graph|crosswalk|inference|schemaview|byo|ares|organization|group|health)(\\?.*)?$': {
				target: 'http://localhost:8000',
				changeOrigin: true,
			},
		},
	},
	// Ensure SPA routing works in production builds
	build: {
		rollupOptions: {
			output: {
				manualChunks: undefined,
			},
		},
	},
});
