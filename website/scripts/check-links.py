"""Checks every link between the built site's own pages.

    python scripts/check-links.py <site folder> <the site's address>

A link, an image, a script or a page's social card that names a path under
the site's address must be a file of the build, and a link to a heading must
find that id on the page. A link that starts with / and falls outside the
site's path is broken too, since it leaves the site by mistake. llms.txt,
llms-full.txt and the Markdown files beside the pages are read for their
full addresses. Links that leave the site are not checked, and nor is the
workspace a domain host's federation workflow adds after the build. Exits 1
and names each broken link.
"""

from __future__ import annotations

import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urljoin, urlsplit

# A full address in Markdown or plain text: an inline link, a reference
# definition, or a src or href in raw HTML.
FULL = re.compile(r"\]\((https?://[^)\s]+)|^\s{0,3}\[[^\]]+\]:\s*<?(https?://[^\s>]+)|\s(?:src|href)=[\"'](https?://[^\"']+)", re.M)


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links, self.ids = [], set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        for key in ("id", "name"):
            if attrs.get(key):
                self.ids.add(attrs[key])
        for key in ("href", "src"):
            if attrs.get(key):
                self.links.append(attrs[key])
        for part in (attrs.get("srcset") or "").split(","):
            if part.strip():
                self.links.append(part.split()[0])
        if tag == "meta" and attrs.get("property") == "og:image" and attrs.get("content"):
            self.links.append(attrs["content"])


def main(site: Path, address: str) -> int:
    base = urlsplit(address)
    root = base.path if base.path.endswith("/") else base.path + "/"
    skip = ("pagefind", "workspace")
    pages = {}
    for path in site.rglob("*.html"):
        if path.relative_to(site).parts[0] in skip:
            continue
        page = Page()
        page.feed(path.read_text(encoding="utf-8"))
        pages[path] = page

    def target(url: str, source: Path):
        """The file a link names and its fragment, None for a link that leaves the site, or False for a path outside it."""
        if url.startswith("/") and not url.startswith("//") and not url.startswith(root):
            return False
        here = address + source.relative_to(site).as_posix()
        parts = urlsplit(urljoin(here, url))
        if parts.scheme not in ("http", "https") or parts.netloc != base.netloc or not parts.path.startswith(root):
            return None
        rel = unquote(parts.path[len(root):])
        if rel.startswith(tuple(f"{part}/" for part in skip)):
            return None
        file = site / rel
        if file.is_dir() or rel == "" or rel.endswith("/"):
            file = file / "index.html"
        return file, unquote(parts.fragment)

    broken = []
    for source, page in sorted(pages.items()):
        for url in page.links:
            found = target(url, source)
            if found is False:
                broken.append(f"{source.relative_to(site)}: {url} is outside the site's path, {root}")
                continue
            if not found:
                continue
            file, fragment = found
            if not file.is_file():
                broken.append(f"{source.relative_to(site)}: {url} names no file of the site")
            elif fragment and file in pages and fragment not in pages[file].ids:
                broken.append(f"{source.relative_to(site)}: {url} names no heading of that page")
    texts = [site / "llms.txt", site / "llms-full.txt"]
    texts += sorted(p for p in site.rglob("*.md") if p.relative_to(site).parts[0] not in skip)
    for text in texts:
        if not text.is_file():
            continue
        for match in FULL.finditer(text.read_text(encoding="utf-8")):
            url = next(group for group in match.groups() if group)
            found = target(url, text)
            if found and not found[0].is_file():
                broken.append(f"{text.relative_to(site)}: {url} names no file of the site")
    for line in broken:
        print(f"check-links: {line}", file=sys.stderr)
    print(f"check-links: {len(pages)} pages, {len(broken)} broken link(s)")
    return 1 if broken else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), sys.argv[2]))
