# The AI-LinkMO website

This folder builds the site that the Knowledge website workflow publishes to GitHub Pages at `https://noelmcloughlin.github.io/ai-linkmo/`. Every page comes from a file the repository already holds, so a change to the site is a change to that file.

## Preview it

You need bash, git and [uv](https://docs.astral.sh/uv/). Run these from this folder:

```bash
scripts/build.sh          # dist/, with the search index, then checks every link between its pages
scripts/build.sh serve    # http://localhost:1313/ai-linkmo/, rebuilt as you edit
scripts/build.sh preview  # the site as it will be published, at http://localhost:1313/
```

`PORT=1400 scripts/build.sh serve` uses another port.

Hugo and Pagefind come from PyPI, at the versions `pyproject.toml` names and the hashes `uv.lock` holds. The PyPI package `hugo` is a rebuild of Hugo by another maintainer, [hugo-python-distributions](https://github.com/agriyakhetarpal/hugo-python-distributions). The first build fetches Cytoscape and Mermaid, once, and checks each against the hash in `hugo.toml`. Where PyPI or the CDN is blocked, point uv at a mirror, and give `params.vendor.cytoscape.url` and `params.vendor.mermaid.url` a mirror's address in `site.toml`.

`serve` shows raw HTML as written and leaves the security policy off, since Hugo's reload script would break it, and its search index is the one built when it started.

## What the site shows

No setting names any of these. The build looks for each and shows what it finds.

| Repository file | On the site |
| --- | --- |
| `.lokf/knowledge/` | a page per concept under `knowledge/`, with its trust label from `knowledge-report.sh`, its sources and its relations both ways; the health page; the graph; the four files `lokf export` writes, each concept's Markdown and JSON-LD, and the bundle log as an Atom feed, `knowledge/log.xml` |
| `README.md` | the home page, and its Markdown at `index.md`. With none, the home page opens with the bundle's own introduction |
| `docs/**.md` | a page each under `docs/`, and its Markdown at `docs/<name>.md`, with every address made full |
| `docs/<page>.<language>-simple.md` | a retelling of `docs/<page>.md`. Both pages offer each other above their titles, and the retelling has no line in the navigation. A concept tagged `audience-13-18` retells the one concept it is `derivedFrom` in the same way |
| `docs/architecture.md` | the home page's Architecture button |
| `CHANGELOG.md` | a page per release under `changelog/`, which search leaves out |
| `.assets/` | the figures, under `assets/` |
| `.lokf/ingest.lock.yaml` | where each source the ingest mirrored came from, on its concept's card |
| `src/<name>/schema/<name>.yaml`, or the same under `.linkml/`, or the file `site.toml`'s `schema` names | the Schema part: a page per class, slot, enumeration and type, written by LinkML's `gen-doc`, each also at `elements/<Name>/`, where a schema's w3id rules point. The home page then leads with the schema |
| `.lokf/schema/domain.yaml`, else `.lokf/schema/lokf.yaml` or the copy in the `lokf` package | with no schema of the repository's own, the Schema part shows the schema the bundle is written in: its domain vocabulary, or else LOKF core. Neither has `elements/` addresses, and the home page does not lead with either |
| `.github/workflows/knowledge-federation.yaml` | on the graph page, the workspace a domain host's federation serves |

One part is set, never found: the data. `browse` in `site.toml` names a folder of SQLite databases, which the site serves under `browse/` with a page that opens each in Datasette Lite.

The home page has the same five buttons on every site: the schema, the bundle, the architecture page, the glossary and the quick start. One whose page is not there is greyed. The glossary is the bundle's `glossary` group or `docs/glossary.md`. The quick start is a docs page named `quick-start`, `quickstart` or `getting-started`, or the first heading of one of those names.

A release page links the repository, the docs and the bundle at the release's tag. The commit that promotes a release's changelog skips CI, so its page appears with the next build: the workflow's weekly run at the latest, or a run by hand.

## What to edit

- **A page's words:** the file it comes from: the README, a page under `docs/`, the schema, or a concept, through the librarian and the curator like any other change to the bundle.
- **The site's own values:** `site.toml`: its address, title and description, the repository, and optionally a logo, the docs pages' groups, more docs folders to leave out, old addresses to redirect, and the data to publish. A comment above each says what it takes.
- **Its look:** `assets/css/custom.css`, loaded last, is this repository's own. The colours and the trust tones are custom properties at the top of `assets/css/site.css`.

Those two files and this one are the repository's own. Every other file here is a copy of the ktl-website skill's template, and the skill's repair replaces it, so change one of those in the skill's repository.

## Security

Raw HTML in the repository's Markdown is cleaned after the build to the tags GitHub allows in a README, by `scripts/clean-html.py`. Any other markup, such as a `<meta>` refresh or a `<style>`, is shown as text, and an event handler, a style or a `javascript:` address is dropped. A Content-Security-Policy in every page stays as a second guard: a script loads only from the site's own `js/` and `pagefind/` folders, where no repository file is served. `scripts/prepare.sh` stops the build on an SVG that holds a script, and no HTML or XML document, and no file or folder whose name starts with a dot, is served. Raw HTML that GitHub allows can still mislead, such as a link whose words name another address, so review still matters.

The two typefaces, Source Serif 4 for headings and Atkinson Hyperlegible Next for text, are served from the site under the SIL Open Font License 1.1, whose text is beside them in `static/fonts/`.
