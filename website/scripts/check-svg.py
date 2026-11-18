"""Names each SVG that could run a script on the site's address, and exits 1.

    python scripts/check-svg.py <folder> ...

Reads each .svg under the folders as XML, as a browser does, and names one
that holds:

- a script or foreignObject element under any prefix, or an XHTML element;
- an on* event handler;
- a value that starts with javascript: or another scheme that runs, or a
  data: address a browser opens as a page, except a data: SVG in an image;
- a DOCTYPE or an xml-stylesheet instruction;
- text that is not well-formed XML.

A .svgz is named unread. A missing folder is skipped.
"""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from xml.parsers import expat

XHTML = "http://www.w3.org/1999/xhtml"
ELEMENTS = {"script", "foreignobject"}
SCHEME = re.compile(r"^(?:javascript|vbscript|livescript):")
DATA = re.compile(r"^data:(?:text/html|application/xhtml\+xml|text/xml|application/xml|(image/svg\+xml))(?![\w+.-])")
SPACE = re.compile(r"[\x00-\x20]+")


class Found(Exception):
    """What a file holds that could run."""


def start(name: str, attributes: dict[str, str]):
    # expat gives a name as its namespace, a space and its local name.
    namespace, _, element = name.rpartition(" ")
    if element.lower() in ELEMENTS:
        raise Found(f"a {element} element")
    if namespace == XHTML:
        raise Found(f"an XHTML {element} element")
    for key, value in attributes.items():
        attribute = key.rpartition(" ")[2]
        if attribute.lower().startswith("on"):
            raise Found(f"an event handler, {attribute}")
        # An animation's values are a list, each of which can be an address.
        for part in SPACE.sub("", value).lower().split(";"):
            data = DATA.match(part)
            if SCHEME.match(part) or (data and not (data.group(1) and element == "image")):
                raise Found(f"an address that runs, in {attribute}")


def doctype(*_):
    raise Found("a DOCTYPE")


def instruction(target: str, _data: str):
    if target.lower() == "xml-stylesheet":
        raise Found("an xml-stylesheet instruction")


def check(path: Path) -> str:
    """What the file holds that could run, or ""."""
    if path.suffix.lower() == ".svgz":
        return "is compressed, so it is not read; keep the .svg"
    parser = expat.ParserCreate(namespace_separator=" ")
    parser.StartElementHandler = start
    parser.StartDoctypeDeclHandler = doctype
    parser.ProcessingInstructionHandler = instruction
    try:
        parser.Parse(path.read_bytes(), True)
    except Found as found:
        return f"holds {found}"
    except (expat.ExpatError, ValueError, OSError) as error:
        return f"is not XML the check can read ({error})"
    return ""


def main(folders: list[str]) -> int:
    named = []
    for folder in folders:
        for parent, _, names in sorted(os.walk(folder)):
            for name in sorted(names):
                path = Path(parent, name)
                if path.suffix.lower() in (".svg", ".svgz"):
                    reason = check(path)
                    if reason:
                        named.append(f"{path}: {reason}")
    if named:
        print("check-svg: these SVG files hold a script, an event handler, an address that runs or markup the check cannot read, and the site would serve them:", file=sys.stderr)
        for line in named:
            print(f"  {line}", file=sys.stderr)
    return 1 if named else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
