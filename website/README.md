# The AI-LinkMO website

This folder builds the site that the Knowledge website workflow publishes to GitHub Pages at `https://noelmcloughlin.github.io/ai-linkmo/`. Every page comes from a file the repository already holds, so a change to the site is a change to that file:

- each concept in `.lokf/knowledge/` becomes a page under `knowledge/`, with its trust label from `knowledge-report.sh`, its sources and its typed relations both ways;
- the four files `lokf export` writes are served under `knowledge/`, beside each concept's own Markdown file and its JSON-LD;
- the README becomes the home page, each page under `docs/` a page under `docs/`, and `CHANGELOG.md` a page per release under `changelog/`, which search leaves out. `site.config.mjs` says which of these the site shows and where each sits in the sidebar. The commit that promotes a release's changelog skips CI, so its page appears with the next build: the workflow's weekly run at the latest, or a run by hand;
- the LinkML schema's pages, which `gen-doc` writes, become a page each under `schema/`, with their class diagrams drawn in the browser;
- SQLite databases, when `site.config.mjs` names their folder, are served under `browse/` with a page that opens each in Datasette Lite. Neither this folder nor the schema's is committed, so the sync runs the command that builds each when it is missing.

## Preview it

You need Node.js 22.12 or later and [uv](https://docs.astral.sh/uv/).

```bash
cd website
npm ci
npm run dev        # http://localhost:4321/ai-linkmo/
npm run build      # dist/, then checks every link between its pages
```

Both commands run `npm run sync` first, which runs `lokf export` from the sidecar's own environment in `.lokf/` and writes the generated pages. Nothing it writes is committed. Run `astro` commands through `npm run`, or run `npm run sync` first. `node scripts/config.mjs` prints what the sync will read.

`package.json` overrides the Astro that starlight-changelogs' loader helper asks for with the site's own. Without the override npm installs Astro 5 beside it, and the build fails.

## What to edit

- **A page's words:** the file it comes from: the README, a page under `docs/`, or a concept, through the librarian and the curator like any other change to the bundle. A schema page's words come from the schema, and the data page's from the databases' metadata.
- **The site's values and options:** `site.config.mjs`: the addresses, the title, the logo, the home page's tagline and buttons, the docs groups, the extra pages. A comment above each option says what it takes.
- **Its look:** `src/styles/custom.css`, loaded last, is this repository's own. `theme.css` and `catalogue.css` are the house style; the trust colours are in `theme.css`.
- **How a concept page looks:** `src/components/ConceptCard.astro` and `src/styles/catalogue.css`; the map in the right-hand column is `src/components/Neighbourhood.astro`.
- **The health page:** `src/pages/health.astro` and its chart, `src/components/TrustChart.astro`; the trust states' words are in `src/trust.ts`.
- **A page's link preview:** `src/pages/og/[...route].ts` draws its social card, and `src/routeData.ts` points the page at it.
- **How a link is rewritten:** `scripts/routes.mjs`, which the sync and the Markdown plugin both use.
- **How a diagram is drawn:** `src/components/Mermaid.astro`.

The graph explorer is adapted from the LOKF toolkit's own site under Apache-2.0; see [NOTICE](NOTICE).

The two typefaces, Source Serif 4 for headings and Atkinson Hyperlegible Next for text, are self-hosted from Fontsource under the SIL Open Font License 1.1.
