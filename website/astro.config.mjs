// @ts-check
// The site. Every page is built from a file the repository already holds.
// Each concept in the knowledge bundle becomes a page with its trust label,
// and the four files `lokf export` writes are served beside them. The README,
// the docs pages, the changelog, the schema's pages and the data become
// pages when site.config.mjs shows them. scripts/sync.mjs writes the
// generated sources before every build; nothing it writes is committed.
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import { satteri } from "@astrojs/markdown-satteri";
import markdownKtl from "./scripts/markdown-ktl.mjs";
import starlightChangelogs, { makeChangelogsSidebarLinks } from "starlight-changelogs";
import starlightImageZoom from "starlight-image-zoom";
import starlightSidebarTopics from "starlight-sidebar-topics";
import {
  BASE,
  BROWSE,
  CHANGELOG,
  DESCRIPTION,
  DOCS,
  FAVICON,
  LOGO_FILES,
  PAGES,
  REPO_URL,
  SCHEMA,
  SCHEMA_KINDS,
  SITE,
  TITLE,
  bundleGroups,
  conceptIds,
  groupLabel,
  schemaPages,
} from "./scripts/config.mjs";

// The docs pages' place in the Guide sidebar: the groups site.config.mjs
// gives, or one group of every page, nested folders as subgroups.
const docsSidebar = !DOCS
  ? []
  : DOCS.groups
    ? DOCS.groups.map((group) => ({ label: group.label, items: group.pages.map((page) => `docs/${page}`) }))
    : [{ label: "Guides", items: [{ autogenerate: { directory: "docs" } }] }];

// The schema's pages in the sidebar: the overview, then a group per kind in
// gen-doc's own order, each page under its element's name.
const schemaSidebar = [
  { label: "Overview", link: "/schema/" },
  ...Object.entries(SCHEMA_KINDS)
    .map(([kind, label]) => ({
      label,
      collapsed: true,
      items: schemaPages()
        .filter((page) => page.kind === kind)
        .map((page) => ({ label: page.label, link: `/schema/${page.name}/` })),
    }))
    .filter((group) => group.items.length > 0),
];

// The guide, the bundle, the schema and the releases each get a sidebar of
// their own, with a switch between them at its top.
const topics = [
  {
    label: "Guide",
    link: "/",
    icon: "open-book",
    items: [
      { label: "Home", link: "/" },
      ...PAGES.map((page) => ({ label: page.label, link: `/${page.slug}/` })),
      ...(BROWSE ? [{ label: "Browse the data", link: "/browse/" }] : []),
      ...docsSidebar,
    ],
  },
  {
    label: "Knowledge bundle",
    link: "/knowledge/",
    icon: "list-format",
    items: [
      { label: "About the bundle", link: "/knowledge/" },
      { label: "Bundle health", link: "/health/" },
      { label: "Knowledge graph", link: "/graph/" },
      ...bundleGroups().map((group) => ({
        label: groupLabel(group),
        collapsed: true,
        items: [{ autogenerate: { directory: `knowledge/${group}` } }],
      })),
      { label: "Bundle log", link: "/knowledge/log/" },
    ],
  },
];
if (SCHEMA) {
  topics.push({ label: "Schema", id: "schema", link: "/schema/", icon: "puzzle", items: schemaSidebar });
}
if (CHANGELOG) {
  topics.push({
    label: "Releases",
    id: "releases",
    link: "/changelog/",
    icon: "rocket",
    items: makeChangelogsSidebarLinks([
      { type: "all", base: "changelog", label: "All releases" },
      { type: "recent", base: "changelog", count: 8 },
    ]),
  });
}

export default defineConfig({
  site: SITE,
  base: BASE || "/",
  markdown: {
    processor: satteri({ mdastPlugins: [markdownKtl({ conceptIds: conceptIds() })] }),
  },
  integrations: [
    starlight({
      title: TITLE,
      description: DESCRIPTION,
      ...(LOGO_FILES
        ? { logo: { light: `./src/generated/${LOGO_FILES.light}`, dark: `./src/generated/${LOGO_FILES.dark}` } }
        : {}),
      ...(FAVICON === "/favicon.svg" ? {} : { favicon: FAVICON }),
      social: [{ icon: "github", label: "GitHub", href: REPO_URL }],
      // Every page names the bundle log's feed, which the sync writes, so a
      // feed reader given any of the site's addresses finds it.
      head: [
        {
          tag: "link",
          attrs: {
            rel: "alternate",
            type: "application/atom+xml",
            title: `${TITLE}: bundle log`,
            href: `${BASE}/knowledge/log.xml`,
          },
        },
      ],
      // The two typefaces are self-hosted, so no page calls a font service.
      // custom.css comes last and is the host's own: a rule there wins.
      customCss: [
        "@fontsource-variable/atkinson-hyperlegible-next",
        "@fontsource-variable/source-serif-4",
        "./src/styles/theme.css",
        "./src/styles/catalogue.css",
        "./src/styles/custom.css",
      ],
      components: {
        PageTitle: "./src/components/PageTitle.astro",
        PageSidebar: "./src/components/PageSidebar.astro",
        MarkdownContent: "./src/components/MarkdownContent.astro",
      },
      // The generated sources are untracked, so git cannot date them; a
      // concept page shows its own `generated` and `verified` times instead.
      lastUpdated: false,
      routeMiddleware: "./src/routeData.ts",
      plugins: [
        // Click a figure to see it at full size: a diagram is dense at the
        // page's width.
        starlightImageZoom(),
        // A page per release, read from the changelog through the sync.
        ...(CHANGELOG ? [starlightChangelogs()] : []),
        // The sidebar lists the eight newest releases; the topics option puts
        // every release page under the Releases topic, the older ones and the
        // comparisons too, and every schema page under the Schema topic, the
        // schema's own page among them.
        starlightSidebarTopics(topics, {
          topics: {
            ...(CHANGELOG ? { releases: ["/changelog/**"] } : {}),
            ...(SCHEMA ? { schema: ["/schema/**"] } : {}),
          },
        }),
      ],
    }),
  ],
});
