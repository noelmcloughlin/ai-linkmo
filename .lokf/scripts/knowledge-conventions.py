#!/usr/bin/env python3
# /// script
# requires-python = ">=3.9"
# dependencies = ["pyyaml"]
# ///
# The parser's half of knowledge-conventions.sh: rules 2, 3, 4, 7, 9, 10, 12
# and 13 (see that script's header for the list).
#
# Rules 2, 3, 7 and 9 are questions about a document's YAML that a real
# parser answers outright, where grep and awk could only approximate. Is this
# scalar quoted, is this key a list or a mapping, do two files share an id,
# does the block even parse? An unquoted `at:` is only visible as a
# `datetime` once something parses the document. A flow-style
# `verified: { by: ... }` or a multi-line flow item is where a line-oriented
# regex used to guess wrong.
#
# Rule 4 is a body rule that goes with them. Rule 10 exists because the
# provenance gates do read the frontmatter line by line: it keeps the fields
# they read to spellings a line reader and a parser agree on. Rule 12 compares
# a concept's title and description, which only a parser reads whole, with
# the index bullets that copy them. Rule 13 asks git for the text a person
# confirmed and compares it with today's as parsed values, since
# knowledge-apply.sh writes the whole frontmatter back and a requoted value is
# no change. Rules 1, 5, 6, 8 and 11 stay in the shell script: they are git
# and filesystem facts, and need not wait on uv.
#
# Usage: knowledge-conventions.py <bundle-dir>. Same contract as the shell
# half: one line per finding on stdout, exit 1 if any; "OK" and exit 0 if
# none. Invoked by knowledge-conventions.sh through `uv run`, which reads the
# dependency block above and needs nothing preinstalled; run directly it
# needs python3 and pyyaml.

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md", "diataxis.md"}
OPEN_QUESTION = re.compile(r"^- \d{4}-\d{2}-\d{2}, (human|process):[^ :]+: ")
# An index bullet in the shape knowledge-apply.sh writes: the title linked to
# the concept, then its description. A line that lists two concepts is
# neither one's bullet, so the title holds no closing bracket.
INDEX_BULLET = re.compile(r"^\* \[([^\]]*)\]\(([^)]+)\) - (.*)$")
# The fields the provenance gates read line by line: a concept's id, and the
# actor, time and revision of each event.
GATE_FIELDS = {"id", "by", "at", "revision"}
# What a person's confirmation does not cover, for rule 13. In the
# frontmatter these are the trust, lifecycle and usage fields, which record
# who checked what and when rather than what the concept claims. In the body
# they are the open questions and the block KTL Registrar derives from the
# frontmatter.
NOT_CLAIMS = {"generated", "verified", "status", "stale_after", "timestamp", "usage_window"}
RELATED_START, RELATED_END = "<!-- lokf:related -->", "<!-- /lokf:related -->"


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


def moment(value) -> str:
    """A time in the one UTC shape rule 11 and knowledge-report.sh compare, or '' for any other shape."""
    if not isinstance(value, str):
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
        return value + "T00:00:00Z"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}Z", value):
        return value[:16] + ":00Z"
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", value):
        return value[:19] + "Z"
    return ""


def claims(frontmatter: dict, body: str):
    """What a person confirms: the frontmatter without NOT_CLAIMS, and the body without its open questions and its lokf:related block, with blank lines and trailing spaces evened out."""
    kept = {k: v for k, v in frontmatter.items() if k not in NOT_CLAIMS}
    if isinstance(kept.get("sources"), list):  # a source's usage_count is a usage signal too
        kept["sources"] = [{k: v for k, v in s.items() if k != "usage_count"} if isinstance(s, dict) else s for s in kept["sources"]]
    out: list[str] = []
    fenced = in_questions = in_related = False
    for line in body.split("\n"):
        line = line.rstrip()
        # The registrar appends its block at the end, after any open questions,
        # and the block holds a `## Related` heading of its own: skip it first.
        if in_related or line.strip() == RELATED_START:
            in_related = line.strip() != RELATED_END
            continue
        if line.startswith("```") or line.startswith("~~~"):
            fenced = not fenced
        elif not fenced and re.match(r"^#{1,2} ", line):
            in_questions = line == "## Open questions"
        if in_questions:
            continue
        if line or (out and out[-1]):
            out.append(line)
    return kept, "\n".join(out).strip("\n")


def git(cwd: Path, *args: str) -> str | None:
    try:
        done = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, encoding="utf-8", errors="replace", timeout=120)
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout if done.returncode == 0 else None


def unstamped_edit(path: Path, frontmatter: dict, body: str) -> str | None:
    """Rule 13: a concept that reads as confirmed by a person still holds the claims they confirmed.

    The text they confirmed is the concept at the newest commit that recorded
    the time of its latest confirmation. Any later commit can only be an
    edit after it, so the rule can miss one but never flags a concept that
    person saw. Outside git, or before that commit exists, there is nothing
    to compare and nothing is said.
    """
    if frontmatter.get("status") == "deprecated":
        return None
    verified = frontmatter.get("verified")
    events = [verified] if isinstance(verified, dict) else verified if isinstance(verified, list) else []
    confirmations = [
        (moment(e.get("at")), e.get("at"), str(e.get("by")))
        for e in events
        if isinstance(e, dict) and str(e.get("by", "")).startswith("human:") and moment(e.get("at"))
    ]
    if not confirmations:
        return None
    confirmed_at, written, by = max(confirmations)
    generated = frontmatter.get("generated")
    stamp = moment(generated.get("at")) if isinstance(generated, dict) else moment(frontmatter.get("timestamp"))
    if stamp > confirmed_at:
        return None  # it already reads as edited since that confirmation
    real = path.resolve()
    found = git(real.parent, "log", "--format=%H", "-S" + written, "--", real.name)
    commit = found.split("\n", 1)[0].strip() if found else ""
    if not commit:
        return None
    then = git(real.parent, "show", f"{commit}:./{real.name}")
    split = split_frontmatter(then.lstrip("\ufeff").replace("\r\n", "\n").replace("\r", "\n")) if then else None
    if split is None:
        return None
    try:
        frontmatter_then = yaml.safe_load(split[0])
    except yaml.YAMLError:
        return None
    if not isinstance(frontmatter_then, dict) or claims(frontmatter_then, split[1]) == claims(frontmatter, body):
        return None
    return (
        f"{path}: changed since {by} confirmed it ({confirmed_at[:10]}, in {commit[:7]}), and `generated` was not "
        "restamped, so it still reads as confirmed - knowledge-apply.sh restamps every change it writes; by hand, "
        f"move generated.at to the time of the change, or have {by} confirm it again"
    )


def index_bullets(index: Path, cache: dict[Path, dict[str, tuple[str, str]]]) -> dict[str, tuple[str, str]]:
    """The bullets of one index.md, as link -> (title, description), each with its whitespace collapsed."""
    if index not in cache:
        found: dict[str, tuple[str, str]] = {}
        if index.is_file():
            text = index.read_text(encoding="utf-8", errors="replace").replace("\r\n", "\n").replace("\r", "\n")
            for line in text.split("\n"):
                m = INDEX_BULLET.match(line)
                if m:
                    found[m.group(2)] = (" ".join(m.group(1).split()), " ".join(m.group(3).split()))
        cache[index] = found
    return cache[index]


def check_file(path: Path, ids: dict[str, list[Path]], entries: dict[Path, tuple[str, str]]) -> list[str]:
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

    # 2. every `at:` quoted: unquoted, YAML resolves it to a datetime, a
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

    # 7. one file per id: collected here, reported once every file is read.
    concept_id = frontmatter.get("id")
    if isinstance(concept_id, str) and concept_id:
        ids.setdefault(concept_id, []).append(path)

    # 12. the catalogue entry: collected here, compared with the index
    #     bullets once every file is read.
    title, description = frontmatter.get("title"), frontmatter.get("description")
    if isinstance(title, str) and isinstance(description, str):
        entries[path] = (" ".join(title.split()), " ".join(description.split()))

    # 13. a concept that reads as confirmed by a person still says what that
    #     person confirmed: an edit since then restamps `generated`.
    finding = unstamped_edit(path, frontmatter, body)
    if finding:
        findings.append(finding)

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
    entries: dict[Path, tuple[str, str]] = {}
    for path in sorted(bundle.rglob("*.md")):
        if ".obsidian" in path.parts or path.name in RESERVED:
            continue
        findings.extend(check_file(path, ids, entries))

    # 12. an index bullet that names a concept says what the concept says. A
    #     reader chooses from the index before opening anything, so a bullet
    #     left behind by an edited title or description hides the concept as
    #     surely as a missing one. Only a bullet that exists is compared, in
    #     the folder's index.md and in the root's: a concept no index lists
    #     is a choice this rule leaves alone.
    cache: dict[Path, dict[str, tuple[str, str]]] = {}
    for path, entry in entries.items():
        places = {path.parent / "index.md": path.name, bundle / "index.md": path.relative_to(bundle).as_posix()}
        for index, link in places.items():
            bullet = index_bullets(index, cache).get(link)
            if bullet is not None and bullet != entry:
                findings.append(
                    f"{path}: its bullet in {index} does not match its title and description - "
                    "a reindex operation through knowledge-apply.sh re-derives it"
                )

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
