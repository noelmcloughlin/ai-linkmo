// A Sätteri plugin, Astro's Markdown processor, that renders repository
// Markdown on the site. A page the sync wrote names its source file in the
// `ktlSource` frontmatter key, and for such a page the plugin:
//   - points each relative link, image and raw-HTML src/href at the page or
//     file it names (scripts/routes.mjs);
//   - turns an Obsidian [[wikilink]] in a concept into a link to that concept;
//   - moves every heading down one level when `ktlShiftHeadings` is set,
//     since a concept's body starts its sections at `#` and the page title is
//     already the one h1.
import { BASE } from "./config.mjs";
import { rewriteHtml, rewriteUrl } from "./routes.mjs";

const WIKILINK = /\[\[([^\]|#]+)(#[^\]|]*)?(?:\|([^\]]+))?\]\]/g;

function resolveWikilink(name, selfId, ids) {
  const want = name.trim().replace(/\.md$/, "");
  const hits = ids.filter((id) => id !== selfId && (id === want || id.endsWith("/" + want)));
  return hits.length === 1 ? hits[0] : null;
}

/** The plugin factory: called once per document, it returns null for a page the sync did not write. */
export default function markdownKtl({ conceptIds = [] } = {}) {
  return ({ data }) => {
    const fm = data?.astro?.frontmatter ?? {};
    const source = fm.ktlSource;
    if (!source) return null;
    const selfId = source.startsWith(".lokf/knowledge/")
      ? source.slice(".lokf/knowledge/".length).replace(/\.md$/, "")
      : null;
    const relink = (node, ctx) => {
      const url = rewriteUrl(source, node.url);
      if (url !== node.url) ctx.setProperty(node, "url", url);
    };
    return {
      name: "ktl-repository-markdown",
      link: relink,
      image: relink,
      definition: relink,
      html(node, ctx) {
        const value = rewriteHtml(source, node.value);
        if (value !== node.value) ctx.setProperty(node, "value", value);
      },
      heading(node, ctx) {
        if (fm.ktlShiftHeadings) ctx.setProperty(node, "depth", Math.min(6, node.depth + 1));
      },
      text(node, ctx) {
        if (selfId === null || !node.value.includes("[[")) return;
        const parts = [];
        let last = 0;
        for (const m of node.value.matchAll(WIKILINK)) {
          const [whole, name, heading = "", alias] = m;
          if (m.index > last) parts.push({ type: "text", value: node.value.slice(last, m.index) });
          const id = resolveWikilink(name, selfId, conceptIds);
          const text = alias ?? name.trim();
          parts.push(
            id
              ? { type: "link", url: `${BASE}/knowledge/${id}/${heading}`, children: [{ type: "text", value: text }] }
              : { type: "text", value: text },
          );
          last = m.index + whole.length;
        }
        if (parts.length === 0) return;
        if (last < node.value.length) parts.push({ type: "text", value: node.value.slice(last) });
        ctx.replaceNode(node, parts);
      },
    };
  };
}
