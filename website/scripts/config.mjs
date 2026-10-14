// The site's configuration as astro.config.mjs and the scripts read it:
// site.config.mjs's values with every option it leaves out filled in, each
// "auto" settled against the repository, and the required values checked.
// `node scripts/config.mjs` prints the result, so a person can see what the
// sync will read before it runs. site.config.mjs itself runs no code, so the
// pages that show the title import it directly.
import { execFileSync, spawnSync } from "node:child_process";
import { existsSync, readFileSync, readdirSync, statSync } from "node:fs";
import { dirname, extname, relative, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import * as given from "../site.config.mjs";

export const SITE_DIR = resolve(dirname(fileURLToPath(import.meta.url)), "..");
export const REPO_ROOT = resolve(SITE_DIR, "..");
export const BUNDLE_DIR = resolve(REPO_ROOT, ".lokf", "knowledge");

const fail = (what) => {
  throw new Error(`site.config.mjs: ${what}`);
};
const has = (rel) => existsSync(resolve(REPO_ROOT, rel));
const isDir = (rel) => has(rel) && statSync(resolve(REPO_ROOT, rel)).isDirectory();
const isFile = (rel) => has(rel) && statSync(resolve(REPO_ROOT, rel)).isFile();

/** A required value: a string with no placeholder left in it. */
function required(name) {
  const value = given[name];
  if (typeof value !== "string" || value === "") fail(`${name} must be a string`);
  if (/<[A-Z_]+>/.test(value)) fail(`${name} still holds a placeholder (${value}); ktl-website's Step 1 fills it`);
  return value;
}

// ---- the addresses ---------------------------------------------------------

export const REPO = required("REPO");
export const REPO_URL = `https://github.com/${REPO}`;
export const CUSTOM_DOMAIN = given.CUSTOM_DOMAIN ?? null;
// A custom domain serves the site at its root; a project site lives under
// the owner's Pages domain at /<repository>/.
export const SITE = CUSTOM_DOMAIN ? `https://${CUSTOM_DOMAIN}` : required("SITE").replace(/\/$/, "");
export const BASE = CUSTOM_DOMAIN ? "" : required("BASE").replace(/\/$/, "");
export const SITE_URL = SITE + BASE;
export const TITLE = required("TITLE");
export const DESCRIPTION = required("DESCRIPTION");
export const BRANCH = given.BRANCH ?? "main";

// Links to repository files name the commit the site was built from, so a
// reader lands on the text the page was rendered from.
export const REF = (() => {
  if (process.env.GITHUB_SHA) return process.env.GITHUB_SHA;
  try {
    return execFileSync("git", ["-C", REPO_ROOT, "rev-parse", "HEAD"], { encoding: "utf8" }).trim();
  } catch {
    return BRANCH;
  }
})();

// ---- what the site shows beside the bundle ---------------------------------

/** An option left out or set to "auto" takes `fallback` when the repository has it, and null otherwise. */
function settle(name, fallback, present) {
  const value = given[name] === undefined ? "auto" : given[name];
  if (value === "auto") return present(fallback) ? fallback : null;
  if (value !== null && !present(value)) fail(`${name} names ${value}, which is not in the repository`);
  return value;
}

export const ASSETS = settle("ASSETS", ".assets", isDir);

// The Knowledge Trust Ladder logo, which "auto" takes: a copy the repository
// already holds, outside this site and outside a skill's templates, the one
// nearest the root first, or else the copy this site carries in src/assets/.
// The -dark.svg file beside it is the dark version when there is one.
const KTL_LOGO = "knowledge-trust-ladder-logo.svg";
function ktlLogo() {
  const site = relative(REPO_ROOT, SITE_DIR).replaceAll("\\", "/");
  const ls = spawnSync("git", ["-C", REPO_ROOT, "ls-files", "--cached", "--others", "--exclude-standard", "--", `*${KTL_LOGO}`], {
    encoding: "utf8",
  });
  const own = (ls.status === 0 ? ls.stdout.split("\n") : [KTL_LOGO, `.assets/${KTL_LOGO}`])
    .filter((f) => (f === KTL_LOGO || f.endsWith(`/${KTL_LOGO}`)) && !f.startsWith(`${site}/`) && !f.includes("templates/website/"))
    .filter(isFile)
    .sort((a, b) => a.split("/").length - b.split("/").length || (a < b ? -1 : a > b ? 1 : 0));
  const light = own[0] ?? `${site}/src/assets/${KTL_LOGO}`;
  const dark = light.replace(/\.svg$/, "-dark.svg");
  return { light, dark: isFile(dark) ? dark : light };
}

export const LOGO = (() => {
  const value = given.LOGO === undefined ? "auto" : given.LOGO;
  if (value === null) return null;
  const logo = value === "auto" ? ktlLogo() : typeof value === "string" ? { light: value } : value;
  const light = logo.light ?? fail("LOGO needs at least a light file");
  const dark = logo.dark ?? light;
  const favicon = logo.favicon ?? (extname(light) === ".svg" ? light : null);
  for (const file of [light, dark, favicon]) {
    if (file && !isFile(file)) fail(`LOGO names ${file}, which is not in the repository`);
  }
  return { light, dark, favicon };
})();
/** The generated logo files, named by their source's type, and the favicon the site serves. */
export const LOGO_FILES = LOGO ? { light: `logo-light${extname(LOGO.light)}`, dark: `logo-dark${extname(LOGO.dark)}` } : null;
export const FAVICON = LOGO?.favicon ? `/favicon${extname(LOGO.favicon)}` : "/favicon.svg";

// docsPages() keeps its list here once read. It is declared before HOME,
// which asks for the list while this module is still loading.
let docsPagesRead = null;

export const DOCS = (() => {
  const value = given.DOCS === undefined ? "auto" : given.DOCS;
  if (value === null) return null;
  const docs =
    value === "auto" ? { dir: "docs" } : typeof value === "string" ? { dir: value } : { dir: value.dir ?? "docs", groups: value.groups };
  if (!isDir(docs.dir)) {
    if (value === "auto") return null;
    fail(`DOCS names ${docs.dir}, which is not a folder in the repository`);
  }
  return { dir: docs.dir, groups: docs.groups ?? null };
})();

export const CHANGELOG = (() => {
  const value = given.CHANGELOG === undefined ? "auto" : given.CHANGELOG;
  if (value === null) return null;
  const file = value === "auto" ? "CHANGELOG.md" : value;
  if (!isFile(file)) {
    if (value === "auto") return null;
    fail(`CHANGELOG names ${file}, which is not in the repository`);
  }
  // A release page needs one released version in Keep a Changelog form.
  if (/^## \[[^\]]+\] - \d{4}-\d{2}-\d{2}/m.test(readFileSync(resolve(REPO_ROOT, file), "utf8"))) return file;
  if (value === "auto") return null;
  return fail(`${file} has no "## [version] - YYYY-MM-DD" heading, which a release page needs`);
})();

export const PAGES = (given.PAGES ?? []).map((p) => {
  if (!p.slug || !p.source) fail("each PAGES entry needs a slug and a source");
  if (!isFile(p.source)) fail(`PAGES names ${p.source}, which is not in the repository`);
  return { slug: p.slug, source: p.source, label: p.label ?? p.slug };
});

/** The first `# ` line of a file outside fenced code, or null. */
function firstTitle(rel) {
  let fence = null;
  for (const line of readFileSync(resolve(REPO_ROOT, rel), "utf8").split("\n")) {
    const m = line.match(/^\s*(`{3,}|~{3,})/);
    if (fence) {
      if (m && m[1][0] === fence[0] && m[1].length >= fence.length) fence = null;
    } else if (m) fence = m[1];
    else if (/^# /.test(line)) return line.slice(2).trim();
  }
  return null;
}

// The buttons under the home page's title when HOME.actions is not set: the
// bundle, the docs' architecture page when the site has one, the health page
// and the graph.
function defaultActions() {
  return [
    { text: "Browse the bundle", link: "/knowledge/", icon: "right-arrow" },
    ...(docsPages().includes("architecture") ? [{ text: "Architecture", link: "/docs/architecture/", variant: "secondary" }] : []),
    { text: "Bundle health", link: "/health/", variant: "secondary" },
    { text: "Knowledge graph", link: "/graph/", variant: "secondary" },
  ];
}

export const HOME = (() => {
  const home = { source: "auto", tagline: null, actions: null, ...(given.HOME ?? {}) };
  let source = home.source ?? null;
  if (source === "auto") source = isFile("README.md") && firstTitle("README.md") ? "README.md" : null;
  else if (source !== null && !isFile(source)) fail(`HOME.source names ${source}, which is not in the repository`);
  const tagline = home.tagline ?? null;
  if (tagline && typeof tagline === "object" && !isFile(tagline.boldLineOf ?? "")) {
    fail("HOME.tagline.boldLineOf names a file that is not in the repository");
  }
  return { source, tagline, actions: home.actions ?? defaultActions() };
})();

// ---- the bundle and the docs, as folders and files -------------------------

/** The bundle's concept groups: its top-level folders, in name order. */
export function bundleGroups() {
  return readdirSync(BUNDLE_DIR)
    .filter((name) => !name.startsWith(".") && statSync(resolve(BUNDLE_DIR, name)).isDirectory())
    .sort();
}

/** A group's folder name as words, so young-readers reads "Young readers". */
export function groupLabel(group) {
  const words = group.replace(/[-_]+/g, " ");
  return words.charAt(0).toUpperCase() + words.slice(1);
}

/** Every concept's ID: its path in the bundle without `.md`, index and log files left out. */
export function conceptIds() {
  const ids = [];
  const walk = (dir, prefix) => {
    for (const name of readdirSync(dir).sort()) {
      if (name.startsWith(".")) continue;
      const full = resolve(dir, name);
      if (statSync(full).isDirectory()) walk(full, prefix + name + "/");
      else if (name.endsWith(".md") && name !== "index.md" && !(prefix === "" && name === "log.md"))
        ids.push(prefix + name.slice(0, -3));
    }
  };
  if (existsSync(BUNDLE_DIR)) walk(BUNDLE_DIR, "");
  return ids;
}

/**
 * Every docs page, as its path under the docs folder without `.md`: the
 * files git sees there, tracked or untracked but never ignored, so a folder
 * a generator writes stays out; a walk of the folder where there is no git.
 * A file PAGES names has a page of its own and is left out here. The list
 * is read once per process, since the home page's buttons, the links and
 * the sync all ask for it.
 */
export function docsPages() {
  if (docsPagesRead) return docsPagesRead;
  if (!DOCS) return (docsPagesRead = Object.freeze([]));
  const dir = DOCS.dir;
  const extra = new Set(PAGES.map((p) => p.source));
  let files;
  const ls = spawnSync("git", ["-C", REPO_ROOT, "ls-files", "--cached", "--others", "--exclude-standard", "--", dir], {
    encoding: "utf8",
  });
  if (ls.status === 0) {
    files = ls.stdout.split("\n").filter(Boolean);
  } else {
    files = [];
    const walk = (d, prefix) => {
      for (const name of readdirSync(d).sort()) {
        const full = resolve(d, name);
        if (statSync(full).isDirectory()) walk(full, prefix + name + "/");
        else files.push(prefix + name);
      }
    };
    walk(resolve(REPO_ROOT, dir), dir + "/");
  }
  return (docsPagesRead = Object.freeze(
    files
      .filter((f) => f.startsWith(dir + "/") && f.endsWith(".md") && !extra.has(f) && isFile(f))
      .map((f) => f.slice(dir.length + 1, -3))
      .sort(),
  ));
}

if (process.argv[1] && resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const settled = { REPO, SITE, BASE, TITLE, DESCRIPTION, BRANCH, CUSTOM_DOMAIN, REF, LOGO, ASSETS, DOCS, CHANGELOG, PAGES, HOME };
  console.log(JSON.stringify({ ...settled, docsPages: docsPages(), bundleGroups: bundleGroups() }, null, 2));
}
