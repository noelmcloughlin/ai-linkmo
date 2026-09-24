#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
# The parser's half of knowledge-conventions.sh: rules 2, 3, 4, 7, 9 and 10
# (see that script's header for the list). Rules 2, 3, 7 and 9 are questions
# about a document's YAML - is this scalar quoted, is this key a list or a
# mapping, do two files share an id, does the block even parse - that a real
# parser answers outright where grep and awk could only approximate: an
# unquoted `at:` is only visible as a `datetime` once something parses the
# document, and a flow-style `verified: { by: ... }` or a multi-line flow item
# is where a line-oriented regex used to guess wrong. Rule 4 is a body rule
# that rides along, and rule 10 exists because the provenance gates do read
# the frontmatter line by line: it keeps the fields they read to spellings a
# line reader and a parser agree on. Rules 1, 5, 6, 8 and 11 stay in the shell
# script: they are git and filesystem facts, and needn't wait on uv.
#
# Usage: knowledge-conventions.py <bundle-dir>. Same contract as the shell
# half: one line per finding on stdout, exit 1 if any; "OK" and exit 0 if
# none. Invoked by knowledge-conventions.sh through `uv run`, which reads the
# dependency block above and needs nothing preinstalled; run directly it
# needs python3 and pyyaml.

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md", "diataxis.md"}
OPEN_QUESTION = re.compile(r"^- \d{4}-\d{2}-\d{2}, (human|process):[^ :]+: ")
# The fields the provenance gates read line by line: a concept's id, and the
# actor, time and revision of each event.
GATE_FIELDS = {"id", "by", "at", "revision"}


def plain_spellings(fm_text: str) -> list[str]:
    """Rule 10: what a line reader could not read the way a parser does."""
    findings: list[str] = []
    stack: list[dict] = []  # one entry per open collection

    def at(ev) -> str:
        return f"line {ev.start_mark.line + 2}"  # +1 for zero-based, +1 for the opening ---

    for ev in yaml.parse(fm_text):
        top = stack[-1] if stack else None
        in_value = top is not None and top["kind"] == "map" and not top["expect_key"]
        field = top["key"] if in_value else None
        if isinstance(ev, yaml.AliasEvent):
            findings.append(f"an alias (*{ev.anchor}) at {at(ev)}")
        elif getattr(ev, "anchor", None):
            findings.append(f"an anchor (&{ev.anchor}) at {at(ev)}")
        if isinstance(ev, yaml.ScalarEvent):
            if ev.tag is not None:
                findings.append(f"a tag on '{ev.value}' at {at(ev)}")
            if top is not None and top["kind"] == "map" and top["expect_key"]:
                if ev.style is not None and ev.value in GATE_FIELDS:
                    findings.append(f"a quoted key ({ev.value}) at {at(ev)}")
                top["key"] = ev.value
                top["expect_key"] = False
                continue
            if field in GATE_FIELDS:
                if ev.style in ("|", ">"):
                    findings.append(f"a block scalar for {field} at {at(ev)}")
                elif ev.start_mark.line != ev.end_mark.line:
                    findings.append(f"a {field} spanning lines at {at(ev)}")
        if isinstance(ev, (yaml.MappingStartEvent, yaml.SequenceStartEvent)):
            if field in GATE_FIELDS:
                findings.append(f"a collection where {field} should be one scalar at {at(ev)}")
            if in_value:
                top["expect_key"] = True
            stack.append({"kind": "map" if isinstance(ev, yaml.MappingStartEvent) else "seq", "expect_key": True, "key": None})
            continue
        if isinstance(ev, (yaml.MappingEndEvent, yaml.SequenceEndEvent)):
            stack.pop()
            continue
        if in_value:
            top["expect_key"] = True
    return findings


def split_frontmatter(text: str) -> tuple[str, str] | None:
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return None


def find_unquoted_at(node, where: str) -> list[str]:
    findings: list[str] = []
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "at" and not isinstance(value, str):
                findings.append(f"{where}at")
            findings.extend(find_unquoted_at(value, f"{where}{key}."))
    elif isinstance(node, list):
        for index, item in enumerate(node):
            findings.extend(find_unquoted_at(item, f"{where}[{index}]."))
    return findings


def check_file(path: Path, ids: dict[str, list[Path]]) -> list[str]:
    findings: list[str] = []
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        findings.append(f"{path}: starts with a byte order mark - save as UTF-8 without BOM")
        raw = raw[3:]
    text = raw.decode("utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")

    split = split_frontmatter(text)
    if split is None:
        findings.append(
            f"{path}: no closed frontmatter block - a concept starts with '---' and closes it before the body"
        )
        return findings
    fm_text, body = split

    try:
        frontmatter = yaml.safe_load(fm_text)
    except yaml.YAMLError as exc:
        problem = getattr(exc, "problem", None) or " ".join(str(exc).split())
        mark = getattr(exc, "problem_mark", None)
        where = f" at line {mark.line + 2}" if mark is not None else ""
        findings.append(f"{path}: frontmatter is not valid YAML - {problem}{where}")
        return findings
    if not isinstance(frontmatter, dict):
        findings.append(f"{path}: frontmatter is not a mapping")
        return findings

    # 10. the fields the provenance gates read line by line are spelt so a
    #     line reader and a parser see the same event.
    for what in plain_spellings(fm_text):
        findings.append(f"{path}: frontmatter uses {what} - write it plainly, so the gate reads the event a parser reads")

    # 2. every `at:` quoted - unquoted, YAML resolves it to a datetime, a
    #    date or a number, and only a string reaches every consumer the same.
    for where in find_unquoted_at(frontmatter, ""):
        findings.append(f"{path}: unquoted timestamp at {where}")

    # 3. verified is a list, never a bare mapping, and carries at most one
    #    process:ktl-librarian event.
    verified = frontmatter.get("verified")
    if isinstance(verified, dict):
        findings.append(f"{path}: verified is a bare mapping - write a one-item list")
        events = [verified]
    elif isinstance(verified, list):
        events = [item for item in verified if isinstance(item, dict)]
    else:
        events = []
    librarian_events = [e for e in events if e.get("by") == "process:ktl-librarian"]
    if len(librarian_events) > 1:
        findings.append(
            f"{path}: {len(librarian_events)} process:ktl-librarian events - "
            "the librarian replaces its own, never stacks"
        )

    # 4. a bullet under `## Open questions` is `- YYYY-MM-DD, <actor>: ...`.
    in_section = False
    for line in body.split("\n"):
        if line == "## Open questions":
            in_section = True
            continue
        if in_section and line.startswith("#"):
            in_section = False
        if in_section and line.startswith("- ") and not OPEN_QUESTION.match(line):
            findings.append(f"{path}: open question not '- YYYY-MM-DD, <actor>: ...': {line[:60]}")

    # 7. one file per id - collected here, reported once every file is read.
    concept_id = frontmatter.get("id")
    if isinstance(concept_id, str) and concept_id:
        ids.setdefault(concept_id, []).append(path)

    return findings


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: knowledge-conventions.py <bundle-dir>", file=sys.stderr)
        return 2
    bundle = Path(argv[1])
    if not bundle.is_dir():
        print(f"no bundle directory at {bundle}", file=sys.stderr)
        return 2

    findings: list[str] = []
    ids: dict[str, list[Path]] = {}
    for path in sorted(bundle.rglob("*.md")):
        if ".obsidian" in path.parts or path.name in RESERVED:
            continue
        findings.extend(check_file(path, ids))

    for concept_id, paths in ids.items():
        if len(paths) > 1:
            files = "".join(f"{p} " for p in paths)
            findings.append(
                f"id {concept_id} is declared by more than one file: {files}- "
                "a sync conflict copy or a pasted duplicate; keep one"
            )

    for line in findings:
        print(line)
    if findings:
        return 1
    print(f"OK - {bundle} keeps the frontmatter conventions lokf validate cannot check")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
