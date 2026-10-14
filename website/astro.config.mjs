// @ts-check
// The site. Every page is built from a file the repository already holds:
// each concept in the knowledge bundle becomes a page with its trust label,
// the four files `lokf export` writes are served beside them, and the README,
// the docs pages and the changelog become pages when site.config.mjs shows
// them. scripts/sync.mjs writes the generated sources before every build;
// nothing it writes is committed.
import { defineConfig } from "astro/config";
import starlight from "@astrojs/starlight";
import { satteri } from "@astrojs/markdown-satteri";
import markdownKtl from "./scripts/markdown-ktl.mjs";
import starlightChangelogs, { makeChangelogsSidebarLinks } from "starlight-changelogs";
import starlightImageZoom from "starlight-image-zoom";
import starlightSidebarTopics from "starlight-sidebar-topics";
import {
  BASE,
  CHANGELOG,
  DESCRIPTION,
  DOCS,
  FAVICON,
  LOGO_FILES,
  PAGES,
  REPO_URL,
  SITE,
  TITLE,
  bundleGroups,
  conceptIds,
  groupLabel,
} from "./scripts/config.mjs";

// The docs pages' place in the Guide sidebar: the groups site.config.mjs
// gives, or one group of every page, nested folders as subgroups.
const docsSidebar = !DOCS
  ? []
  : DOCS.groups
    ? DOCS.groups.map((group) => ({ label: group.label, items: group.pages.map((page) => `docs/${page}`) }))
    : [{ label: "Guides", items: [{ autogenerate: { directory: "docs" } }] }];

// The guide, the bundle and the releases each get a sidebar of their own,
// with a switch between them at its top.
const topics = [
  {
    label: "Guide",
    link: "/",
    icon: "open-book",
    items: [
      { label: "Home", link: "/" },
      ...PAGES.map((page) => ({ label: page.label, link: `/${page.slug}/` })),
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
        // comparisons too.
        CHANGELOG
          ? starlightSidebarTopics(topics, { topics: { releases: ["/changelog/**"] } })
          : starlightSidebarTopics(topics),
      ],
    }),
  ],
});
