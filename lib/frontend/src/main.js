import { mount } from 'svelte';
import '$lib/app.css'
import App from './lib/App.svelte';

const app = mount(App, {
    target: document.getElementById('app'),
})

export default app;