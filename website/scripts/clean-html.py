"""Cleans the raw HTML of each built page to the tags GitHub allows.

    python scripts/clean-html.py <site folder> <mark>

Hugo writes the HTML each repository file renders to between two comments
that carry the build's mark, which changes with every build, so no file can
fake one. Within them, a tag GitHub allows in a README keeps the attributes
it allows, with the class, id, data-* and aria-* attributes the site's
Markdown rendering writes, and a style that only aligns a table's cell. An
address that is not http, https, mailto, a path or a fragment is dropped.
Any other markup is shown as text, so the reader sees it and nothing in it
runs, and each is named on the log. Comments are dropped. Every element is
closed, so nothing a file writes can reach the page around it. The page's
Content-Security-Policy stays as a second guard, and the script needs only
the Python standard library.

Exits 1 when a page holds a mark with no end, as it does when an unclosed
comment or script swallowed the rest of the page, or when no page holds a
mark.
"""

from __future__ import annotations

import re
import sys
from html import escape
from html.parser import HTMLParser
from pathlib import Path

# The tags GitHub keeps in a README, with picture and source for a figure
# that has a dark version, and input for a task list's checkbox.
TAGS = set(
    "h1 h2 h3 h4 h5 h6 br b i strong em a pre code img tt div ins del sup sub p ol ul table thead tbody tfoot "
    "blockquote dl dt dd kbd q samp var hr ruby rt rp li tr td th s strike summary details caption figure "
    "figcaption abbr bdo cite dfn mark small span time wbr picture source input".split()
)
VOID = {"br", "hr", "img", "wbr", "source", "input"}
# The attributes GitHub keeps on any tag, less a form's, with those the
# site's rendering writes.
ATTRIBUTES = set(
    "abbr align alt aria-describedby aria-hidden aria-label aria-labelledby axis border cellpadding cellspacing "
    "char charoff checked clear cols colspan color compact coords datetime dir disabled for frame headers height "
    "hreflang hspace ismap label lang maxlength media multiple name nohref noshade nowrap open prompt readonly "
    "rel rev role rows rowspan rules scope selected shape size span start summary tabindex target title type "
    "usemap valign value vspace width itemprop class id loading".split()
)
PER_TAG = {
    "a": {"href"},
    "img": {"src", "srcset", "longdesc"},
    "source": {"srcset"},
    "div": {"itemscope", "itemtype"},
    "blockquote": {"cite"},
    "del": {"cite"},
    "ins": {"cite"},
    "q": {"cite"},
}
ADDRESSES = {"href", "src", "srcset", "longdesc", "cite"}
SAFE = re.compile(r"^(?:https?:|mailto:|#|/|\.|[^:/?#]*(?:[/?#]|$))", re.I)
ALIGN = re.compile(r"^\s*text-align:\s*(?:left|right|center)\s*;?\s*$", re.I)


def safe_address(name: str, value: str) -> bool:
    urls = [part.split()[0] for part in value.split(",") if part.strip()] if name == "srcset" else [value.strip()]
    return all(SAFE.match(url) and not (url.lower().startswith("mailto:") and name != "href") for url in urls)


class Cleaner(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.open, self.shown = [], [], []

    def show(self, text: str):
        self.out.append(escape(text, quote=False))
        self.shown.append(" ".join(text.split())[:80])

    def handle_starttag(self, tag, attrs):
        if tag not in TAGS or (tag == "input" and dict(attrs).get("type") != "checkbox"):
            self.show(self.get_starttag_text() or f"<{tag}>")
            return
        kept = []
        for name, value in attrs:
            value = value or ""
            if name == "style":
                if not ALIGN.match(value):
                    continue
            elif not (name in ATTRIBUTES or name in PER_TAG.get(tag, ()) or name.startswith(("data-", "aria-"))):
                continue
            if name in ADDRESSES and not safe_address(name, value):
                continue
            kept.append(f' {name}="{escape(value)}"')
        self.out.append(f"<{tag}{''.join(kept)}>")
        if tag not in VOID:
            self.open.append(tag)

    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        if tag in TAGS and tag not in VOID and self.open and self.open[-1] == tag:
            self.handle_endtag(tag)

    def handle_endtag(self, tag):
        if tag not in TAGS or tag in VOID:
            if tag not in TAGS:
                self.show(f"</{tag}>")
            return
        if tag in self.open:
            while self.open:
                last = self.open.pop()
                self.out.append(f"</{last}>")
                if last == tag:
                    break

    def handle_data(self, data):
        self.out.append(escape(data, quote=False))

    def handle_comment(self, data):
        pass

    def handle_decl(self, decl):
        self.show(f"<!{decl}>")

    def handle_pi(self, data):
        self.show(f"<?{data}>")

    def unknown_decl(self, data):
        self.show(f"<![{data}]>")

    def clean(self, html: str) -> str:
        self.feed(html)
        self.close()
        self.out.extend(f"</{tag}>" for tag in reversed(self.open))
        self.open = []
        return "".join(self.out)


def main(site: Path, mark: str) -> int:
    region = re.compile(rf"<!--# raw {re.escape(mark)} -->(.*?)<!--# /raw {re.escape(mark)} -->", re.S)
    failed, regions = [], 0
    for path in sorted(site.rglob("*.html")):
        text = path.read_text(encoding="utf-8")
        if mark not in text:
            continue
        found = list(region.finditer(text))
        if text.count(mark) != 2 * len(found):
            failed.append(f"{path.relative_to(site)} holds a mark with no end: an unclosed comment, script or other element in its source swallowed the rest of the page")
            continue
        shown = []

        def cleaned(match):
            cleaner = Cleaner()
            html = cleaner.clean(match.group(1))
            shown.extend(cleaner.shown)
            return html

        path.write_text(region.sub(cleaned, text), encoding="utf-8")
        regions += len(found)
        for tag in shown:
            print(f"clean-html: {path.relative_to(site)}: {tag} is not a tag GitHub allows, and is shown as text", file=sys.stderr)
    if not regions:
        failed.append("no page holds the build's mark, so none could be cleaned; Hugo's minifier may have dropped the comments")
    for line in failed:
        print(f"clean-html: {line}", file=sys.stderr)
    print(f"clean-html: {regions} region(s) of raw HTML cleaned")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), sys.argv[2]))
