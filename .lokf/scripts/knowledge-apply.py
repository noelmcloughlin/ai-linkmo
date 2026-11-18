#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = ["pyyaml==6.0.3"]
# ///
# The pen, the librarian's only way to write the bundle. ktl-librarian
# describes each change as an operation in .lokf/patch.yaml, and this script,
# run through knowledge-apply.sh, checks every operation and writes the files.
# Nothing is written unless every operation passes. The script:
#   - stamps `generated` from the clock;
#   - keeps a concept's description and its two index bullets equal;
#   - files each log line under the day's heading, once however many
#     operations give it;
#   - writes a bare web address in a log line or an open question as an
#     autolink, <https://...>;
#   - moves each feedback entry an operation handled out of feedback.md and
#     into the ledger of questions readers asked, ten to a patch at most;
#   - refuses an operation that would write a `human:` actor, rewrite text a
#     person wrote, or delete a concept a person confirmed or left a note on;
#   - refuses a relation the patch adds that names no concept of the bundle,
#     and the deletion of a concept another still relates to;
#   - refuses a patch whose concepts `lokf validate` rejects, with --dry-run
#     too, when the sidecar's .venv holds the toolkit, and says when it cannot
#     check them; that check also refuses a `sources[].excerpt` its local file
#     does not hold;
#   - refuses an excerpt that is empty or longer than 500 characters, and a
#     sources id the patch gives another resource or excerpt than another
#     concept gives it, since the id is one node in the graph.
#
# Every concept it writes keeps a person's record as it was: each `human:`
# event and each note in a person's name, as knowledge-provenance.sh
# --unattended reads them. A frontmatter value that no operation names keeps
# the text the file held. YAML would read it as a number, a boolean or a
# date, and write `1.10` back as `1.1`, `0123456` as `42798`, `12:30:00` as
# `45000`, `yes` as `true` and an unquoted time in another shape.
#
# `--format` prints the patch file's shape, so a host learns the format from
# the script that enforces it, whatever release of the skill it has.
#
# A patch may carry one `log` line, which stands for the line of every
# operation that gives none, so a change made alike to many concepts is
# logged once.
#
# A patch may also carry `handoff`: at most ten lines for the person who
# reviews the change, in the librarian's own words, never written to the
# bundle. The script prints them, and `--handoff <file>` writes them to the
# file that the scheduled wrapper passes to the pull request.
#
# The dependency block above names one PyYAML release. Move it here and in
# knowledge-conventions.py together. Where uv applies an `exclude-newer` date
# and the index serves no upload times, knowledge-apply.sh lifts the date but
# keeps the version. The sidecar's .venv, which it tries first, holds what
# uv.lock pins instead.
#
# Operations (each a mapping under `ops:` with `op:` and `path:`):
#   create    frontmatter + body for a concept that does not exist yet
#   patch     edits (replace / insert_after / append) and `set` frontmatter keys
#   rewrite   a whole new body, and `set` as on patch; the lokf:related block and open questions carry over
#   question  one open question, in the curator's shape, with this run's actor
#   resolve   withdraws one open question this run's actor asked; never a person's note
#   recheck   this run's own `verified` event, replacing its previous one
#   delete    the concept, its index bullets, and a log line saying why
#   reindex   both index bullets re-derived from the frontmatter; the concept itself is not touched
# An operation may carry only the keys it reads, which KEYS below lists.
#
# Usage: knowledge-apply.py [--dry-run [--diff]] [--keep] [--handoff <file>] --root <repo-root> [<patch-file>]
#        knowledge-apply.py --format
#   exit 0  applied, or with --dry-run would apply; or the format was printed
#   exit 1  findings; nothing written
#   exit 2  usage, no bundle, or a patch file that cannot be read

from __future__ import annotations

import argparse
import copy
import datetime as dt
import difflib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

RESERVED = {"index.md", "log.md"}  # in every folder; a concept path names a folder, so never the root map
PATH_RE = re.compile(r"[a-z0-9][a-z0-9-]*(/[a-z0-9][a-z0-9-]*)+\.md")  # matched whole, so no line break can follow it
EVENT_RE = re.compile(r"^\s*-?\s*by:\s*human:")  # a line the provenance gates read as a person's event
NOTE_RE = re.compile(r"^\s*-\s*\d{4}-\d{2}-\d{2},\s*human:")  # a line the curator reads as a person's note
KEPT_NOTE_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}, *human:")  # a person's note as knowledge-provenance.sh --unattended reads one
CURATOR_NOTE_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}, *process:ktl-curator:")  # a curator's send-back recorded with no authenticated login (review-session.md)
# A person's note in the spellings a Markdown reader shows as one: another
# bullet mark or a numbered item, an indent, a quote mark or a task box in
# front, a tab or two spaces after the comma, an escaped colon. The gates
# read the strict shape above, so no program counts these, and a person does.
LOOSE_NOTE_RE = re.compile(r"^[\s>]*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?\d{4}-\d{2}-\d{2}\s*,\s*human\\?:")
# The labels of the two log lines ktl-curator writes for a person. The report
# reads a retired concept's successor from the second.
CURATOR_LABELS = {"curation", "deprecation"}
# A person's note as knowledge-report.sh lists one, under an open-questions heading outside a code fence.
SEEN_NOTE_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}, human:[^ ]*: ")
# A patch's actor is `process:` and a login's characters, so no Markdown or
# colon reaches the stamps and bullets the patch writes.
ACTOR_RE = re.compile(r"process:[A-Za-z0-9][A-Za-z0-9._-]*")
# The curator's actor, which stands for a person who could not sign in. A
# patch under it, or under an actor that starts with it, would write notes
# that read as that person's.
CURATOR_ACTOR = "process:ktl-curator"
# Matched case-insensitively, and including the event-internal keys, so a
# patch cannot write a top-level `by: human:...` or a `Verified:` that a line
# reader would skip but a person, or another parser, could read as provenance.
# `revised` and `refuted`, the event slots of LOKF 0.9.0, each carry an actor,
# so they belong to the script and the curator like the rest.
DENIED_SET = {"id", "type", "generated", "verified", "revised", "refuted", "status", "stale_after", "timestamp", "by", "at", "revision"}
DENIED_CREATE = {"generated", "verified", "revised", "refuted", "status", "stale_after", "timestamp", "by", "at", "revision"}
# Where knowledge-report.sh reads a retired concept's successor, which ktl-curator writes on a person's word.
SUCCESSOR_KEYS = {"isreplacedby", "relations"}
RELATED_START, RELATED_END = "<!-- lokf:related -->", "<!-- /lokf:related -->"
OPEN_Q = "## Open questions"
# The longest `sources[].excerpt` the pen writes, counted with each run of
# white space as one character. An excerpt is the passage a claim rests on: a
# sentence, a table row or a line of configuration. The toolkit sets no
# limit, so a page copied whole would pass its check, break on every edit to
# the file, and reproduce the source inside a bundle that may be published.
EXCERPT_MAX = 500
BULLET_RE = re.compile(r"^- \d{4}-\d{2}-\d{2}, (\S+?): ")  # an open question's actor, in the shape the curator writes
# A web address that is not already an autolink, a link's target or a link's
# text: no `<`, `](` or `[` before it. A pair of parentheses inside it stays
# in it, as Wikipedia's addresses need, and its last character is no
# punctuation, so a full stop, a comma or a closing parenthesis after it
# stays in the sentence.
BARE_URL_RE = re.compile(r"(?<!\]\()(?<![<\[\w/])https?://(?:[^\s<>`()]|\([^\s<>`()]*\))*(?:[^\s<>`().,;:!?'\"]|\([^\s<>`()]*\))")
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.*\S)[ \t]*$")  # a Markdown heading: its level and its text
OWN_BULLET_RE = re.compile(r"^\* \[[^\]]*\]\([^)]+\)(?: - .*)?$")  # any concept's own index bullet: its link alone, then its description
FEEDBACK_KIND_RE = re.compile(r"^- \*\*(Miss|Disagreement)\*\* ")
HANDOFF_LINES, HANDOFF_CHARS = 10, 300
# What a new file's mode loses, read once: os.umask can only be read by setting it.
UMASK = os.umask(0)
os.umask(UMASK)
FEEDBACK_ENTRIES = 10  # the reader entries one patch may handle; the rest wait for the next run
# The characters Unicode calls default ignorable, which a renderer draws as
# nothing, beyond the format and control characters: variation selectors,
# which can spell hidden text after a visible character, the Hangul fillers
# and the combining grapheme joiner, among others. knowledge-ingest.py holds
# the same list.
IGNORABLE = re.compile("[\u034f\u115f\u1160\u17b4\u17b5\u180b-\u180f\u2065\u3164\ufe00-\ufe0f\uffa0\ufff0-\ufff8\U000e0000-\U000e0fff]")
# The keys each operation reads besides `op` and `path`. Any other key is
# refused by name, because a key the script skipped would pass a dry run and
# change nothing. Every operation that writes a log line reads the keys in
# LOGGED, and every one that stamps `generated` reads `revision`.
LOGGED = ("log", "from_feedback", "asked")
KEYS = {
    "create": ("frontmatter", "body", "revision", *LOGGED),
    "patch": ("edits", "set", "revision", *LOGGED),
    "rewrite": ("body", "set", "revision", *LOGGED),
    "question": ("text", *LOGGED),
    "resolve": ("target", *LOGGED),
    "recheck": (),
    "delete": LOGGED,
    "reindex": (),
}
OPS = set(KEYS)
EDITS = {"replace", "insert_after", "append"}
LEDGER_HEAD = (
    "# Questions readers asked\n"
    "\n"
    "Written by knowledge-apply.sh each time ktl-librarian handles a reader's feedback entry: the day, the kind, the concept that now answers it, and the reader's question where the entry held one. Oldest first, one line per entry, never edited. Programs read it: knowledge-report.sh counts the concepts readers keep asking about, and scores whether the index leads to them.\n"
    "\n"
)

# What `--format` prints. ktl-librarian's references/patch.md carries the same
# block, and check 19 of the repository contract holds the two equal.
FORMAT = r'''by: process:ktl-librarian        # optional; the actor every stamp carries, always process:<id>
log: "**Changed**: each service concept now cites its source by repository path."   # optional; the line for every operation that gives none, written once
ops:
  - op: create                   # a concept that does not exist yet
    path: services/orders-api.md # lowercase, under a folder, .md; the id is base_iri plus this path
    frontmatter:                 # type, title and description are required; never generated, verified, status, stale_after
      type: Service
      title: Orders API
      description: REST API serving order data to the CLI and web UI.
      resource: services/orders/openapi.yaml
      sources:
        - resource: services/orders/openapi.yaml
          id: openapi.yaml       # the label of the footnote that cites this entry
          excerpt: "x-rate-limit: 600 requests per minute"   # the passage the footnoted claim rests on, copied from the file; refused when the file does not hold it
      dependsOn:
        - https://acme.example/knowledge/datasets/orders-db
    body: |
      # Overview

      The **Orders API** generates its endpoints from `services/orders/openapi.yaml`...
      It serves at most 600 requests a minute.[^openapi.yaml]

      [^openapi.yaml]: services/orders/openapi.yaml, the `x-rate-limit` line
    log: "**Added**: Orders API, from `services/orders/openapi.yaml`."   # optional on create
    from_feedback: "- **Miss** - Q: \"Which API serves orders?\" Answered from `services/orders/openapi.yaml`. Nothing relevant in index.md. - docent"   # the exact entry, which the script moves out of feedback.md; ten to a patch at most
    asked: "Which API serves orders?"   # the reader's question from that entry, for the ledger in .lokf/questions.md

  - op: patch                    # minimal edits to a body, and frontmatter keys to set
    path: datasets/orders-db.md
    edits:
      - replace: { target: "nightly at 02:00", content: "nightly at 03:00" }   # target occurs exactly once
      - insert_after: { target: "## Columns", content: "" }                     # new lines after the one line holding the target
      - append: { content: "## Retention\n\nRows older than 13 months are dropped." }   # before ## Open questions, if any
    set:
      description: The orders table, loaded nightly at 03:00 from the Orders API.
    log: "**Changed**: the load moved to 03:00; `etl/orders.yaml` says so since 2026-08-01."
    from_feedback: "- **Disagreement** - `datasets/orders-db.md` says 02:00; `etl/orders.yaml` now says 03:00. - docent"

  - op: rewrite                  # a whole new body; the lokf:related block and ## Open questions carry over
    path: playbooks/release.md
    body: |
      # Overview
      ...
    set:                         # optional; frontmatter keys to set, as on patch
      description: How a release is cut and published by the release workflow.
    log: "the release page was rewritten around the new workflow"

  - op: question                 # one open question in the curator's shape; sets status: draft
    path: policies/retention.md
    text: "the policy names 13 months and the ETL config names 12; which is current?"

  - op: resolve                  # withdraws one open question this run's actor asked, once the source settles it
    path: policies/retention.md
    target: "which is current?"  # text found in exactly one of that actor's questions; a person's note is the curator's to clear
    log: "**Resolved**: the policy and the ETL config both name 13 months since a1b2c3d."

  - op: recheck                  # this run's own verified event, replacing its previous one where it stood
    path: glossary/order.md

  - op: reindex                  # both index bullets re-derived from the frontmatter; the concept is not written
    path: policies/retention.md

  - op: delete                   # the file and its index bullets; refused when a person confirmed it or left a note on it, or an index names it in a sentence
    path: services/legacy-sync.md
    log: "**Removal**: Legacy Sync; `services/legacy-sync/` was deleted in a1b2c3d."

handoff:                         # optional; at most ten lines of 300 characters for the reviewer, in your own words and never a reader's; written nowhere in the bundle
  - "datasets/orders-db.md and playbooks/release.md came back for the same misread date; the skill's rule on dates needs a look."
  - "https://acme.example/spec did not answer, so references/acme-spec.md was not rechecked."
'''


# The fields knowledge-report.sh reads as relations, which the schema ranges
# over Concept. A relation a patch adds is checked only in these: only
# `--check-refs` with the schema knows which of a host's own slots hold a
# concept. A delete is checked in those slots too, since a whole IRI that names
# the deleted concept is stale whatever its slot holds.
RELATION_FIELDS = (
    "isPartOf", "hasPart", "references", "dependsOn", "derivedFrom", "about", "sameAs",
    "relatedTo", "definedBy", "source", "measures", "memberOf", "holder", "isReplacedBy",
)
# The fields knowledge-report.sh never reads as a domain vocabulary's own slot.
NOT_LINKS = {
    "id", "type", "title", "description", "resource", "sources", "exclusions", "distribution",
    "endpoint", "documentation", "license", "author", "publisher", "generated", "verified", "status",
    "base_iri", "context", "stale_after", "timestamp", "genre", "definition", "version",
}
# An index and a log are no concept in any folder, and KTL Registrar's map is
# none at the bundle's root. The pen writes none of the three.
NOT_CONCEPTS = {"index.md", "log.md"}
ROOT_MAP = "diataxis.md"
SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")
WHOLE_IRI = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:\S+")


def material(value):
    """A resource as rule 16 compares it, as `lokf validate` does: `./docs/a.md`, `docs/a.md` and `docs/a.md/` name one material."""
    if not isinstance(value, str) or not value.strip():
        return None
    key = value.strip()
    while key.startswith("./"):
        key = key[2:]
    return key.rstrip("/") or key


def relation_targets(fm: dict) -> set:
    """Each (field, target) a concept's frontmatter relates it to, in any spelling the schema reads.

    A value holding a space is left out, as `--check-refs` leaves it: `measures` also takes a description.
    """
    def target(value) -> bool:
        return isinstance(value, str) and bool(value.strip()) and not any(ch.isspace() for ch in value.strip())

    found = set()
    for field in RELATION_FIELDS:
        value = fm.get(field)
        for item in value if isinstance(value, list) else [value]:
            if target(item):
                found.add((field, item.strip()))
    relations = fm.get("relations")
    for item in relations if isinstance(relations, list) else [relations]:
        if isinstance(item, dict) and target(item.get("target")):
            found.add(("relations", item["target"].strip()))
    return found


def domain_iris(fm: dict) -> set:
    """Each (field, whole IRI) under a field no list here names, which is how knowledge-report.sh reads a domain vocabulary's own slots."""
    found = set()

    def walk(field: str, value) -> None:
        if isinstance(value, str):
            if WHOLE_IRI.fullmatch(value.strip()):
                found.add((field, value.strip()))
        elif isinstance(value, list):
            for item in value:
                walk(field, item)
        elif isinstance(value, dict):
            for item in value.values():
                walk(field, item)

    for field, value in fm.items():
        if field not in NOT_LINKS and field not in RELATION_FIELDS and field != "relations":
            walk(field, value)
    return found


class Refused(Exception):
    pass


class Plain(str):
    """A scalar YAML would read as a number, a boolean or a time, kept as the text the file holds."""

    tag = "tag:yaml.org,2002:str"


class KeepLoader(yaml.SafeLoader):
    """A safe loader, which builds plain data and no object, that keeps each number, boolean and time as the text it was written in. So a value this script was not asked to change is written back as it was read."""


def unique_keys(loader, node, deep=False):
    """A mapping whose keys are each given once. PyYAML keeps the last of two alike and says nothing, so a concept that spells `verified` twice, as a clean merge of a confirmation and a re-check leaves it, would show this script one block where the gates read both. A patch that gives an operation a key twice would lose the first the same way."""
    seen = set()
    for key_node, _ in node.value:
        key = key_node.value if isinstance(key_node, yaml.ScalarNode) else None
        if key is not None and key in seen:
            raise yaml.constructor.ConstructorError(None, None, f"the key {key!r} is given twice in one mapping", key_node.start_mark)
        seen.add(key)
    return yaml.SafeLoader.construct_mapping(loader, node, deep=deep)


KeepLoader.construct_mapping = unique_keys


def keep_text(loader, node):
    text = Plain(node.value)
    text.tag = node.tag
    return text


for _kind in ("int", "float", "bool", "timestamp", "null"):
    KeepLoader.add_constructor("tag:yaml.org,2002:" + _kind, keep_text)


def read_yaml(text: str):
    """What `yaml.safe_load` returns for one document, with KeepLoader's text in place of each number, boolean and time."""
    loader = KeepLoader(text)
    try:
        return loader.get_single_data()
    finally:
        loader.dispose()


class Dumper(yaml.SafeDumper):
    """Writes frontmatter the way the bundle's own files do: a scalar that needs quoting gets double quotes, and one KeepLoader kept as text goes back as that text."""

    def choose_scalar_style(self):
        style = super().choose_scalar_style()
        # A value holding a double quote, such as an ETag, keeps single quotes:
        # double quotes would need a backslash escape, which the gate reads as unreadable.
        return '"' if style == "'" and '"' not in self.event.value else style

    def increase_indent(self, flow=False, indentless=False):
        # PyYAML writes a list under a key with its dashes at the key's
        # column, as the YAML specification's examples do. People indent it,
        # and yamllint's default rules reject the other form, so every list
        # is indented under its key.
        return super().increase_indent(flow, False)


class Quoted(str):
    """A revision, always quoted: a short hash such as 1234e56 reads as a number to a YAML 1.2 reader unquoted. Double quotes, or single quotes round an ETag's own double quotes."""


Dumper.add_representer(Plain, lambda dumper, text: dumper.represent_scalar(text.tag, str(text)))
Dumper.add_representer(Quoted, lambda dumper, text: dumper.represent_scalar("tag:yaml.org,2002:str", str(text), style="'" if '"' in text else '"'))


def quote_revisions(value):
    """The value with each non-empty string under a `revision` key, at any depth, made Quoted. An empty one, and one written unquoted that YAML reads as a number, go back as the file held them."""
    if isinstance(value, dict):
        return {k: Quoted(v) if k == "revision" and isinstance(v, str) and v and not isinstance(v, Plain) else quote_revisions(v) for k, v in value.items()}
    if isinstance(value, list):
        return [quote_revisions(v) for v in value]
    return value


def split_frontmatter(text: str):
    lines = text.split("\n")
    if not lines or lines[0] != "---":
        return None
    for i, line in enumerate(lines[1:], start=1):
        if line == "---":
            return "\n".join(lines[1:i]), "\n".join(lines[i + 1 :])
    return None


def dump(fm: dict, body: str) -> str:
    """The frontmatter block, then the body as it was read: a blank line after the closing --- stays, and one that was absent stays absent."""
    fm_text = yaml.dump(quote_revisions(fm), Dumper=Dumper, sort_keys=False, allow_unicode=True, default_flow_style=False, width=1_000_000)
    return "---\n" + fm_text + "---\n" + body.rstrip("\n") + "\n"


def one_line(value, what: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise Refused(f"{what} must be a non-empty string")
    return " ".join(value.split())


def shown(text: str) -> str:
    """The text without the characters no reader sees: control and format characters, such as a zero-width space, a soft hyphen, a bidirectional control or a tag character, and the rest Unicode calls default ignorable, such as variation selectors. knowledge-ingest.py drops the same characters but keeps the two joiners."""
    return " ".join("".join(char for char in text if unicodedata.category(char) not in ("Cc", "Cf") and not IGNORABLE.match(char)).split())


def human_events(value, slot: str):
    """Each mapping under one frontmatter key whose `by` names a person, at any depth, as (slot, by, at, revision, the other keys). The other keys are an exclusion's `resource` and `reason`, so neither changes under a person's name."""
    if isinstance(value, dict):
        if str(value.get("by", "")).startswith("human:"):
            rest = {str(k): v for k, v in value.items() if k not in ("by", "at", "revision")}
            yield (slot, str(value.get("by")), str(value.get("at", "")), str(value.get("revision", "")), json.dumps(rest, sort_keys=True, default=str))
        for inner in value.values():
            yield from human_events(inner, slot)
    elif isinstance(value, list):
        for inner in value:
            yield from human_events(inner, slot)


def seen_notes(body: str) -> list:
    """The notes in a person's name that knowledge-report.sh lists, read as it reads a body. A line of three backticks or tildes opens or closes a fence, a heading starts or ends the open questions, and a note counts under that heading outside a fence."""
    notes, fence, inq = [], False, False
    for line in body.split("\n"):
        line = line.rstrip("\r")
        if line.startswith("```") or line.startswith("~~~"):
            fence = not fence
        elif fence:
            continue
        elif re.match(r"#+ ", line):
            inq = re.fullmatch(r"## Open questions[ \t]*", line) is not None
        elif inq and SEEN_NOTE_RE.match(line):
            notes.append(line.rstrip())
    return notes


def person_record(text: str | None) -> Counter:
    """What a concept holds in a person's name. Each mapping in its frontmatter, under any key, whose `by` names a person: a `generated`, `verified`, `revised` or `refuted` event, an exclusion a person decided, or a key spelt like one of them. Each line that would be a person's note, read over the whole file as knowledge-provenance.sh --unattended reads it, and in the looser spellings a Markdown reader shows alike. Each note the report lists, so a note still in the file but no longer listed counts as gone. A concept that cannot be read as a mapping still has its notes counted."""
    record: Counter = Counter()
    if text is None:
        return record
    split = split_frontmatter(text)
    try:
        fm = read_yaml(split[0]) if split else None
    except yaml.YAMLError:
        fm = None
    if isinstance(fm, dict):
        for key, value in fm.items():
            for event in human_events(value, str(key)):
                record[event] += 1
    lines = text.split("\n")
    kept = []
    for i, line in enumerate(lines):
        if KEPT_NOTE_RE.match(line) or LOOSE_NOTE_RE.match(line) or CURATOR_NOTE_RE.match(line):
            record[("note", line.rstrip())] += 1
            kept.append(line.rstrip())
            # The indented lines under a note are part of it to a reader.
            under = []
            for more in lines[i + 1:]:
                if not more.strip() or not more[0] in " \t":
                    break
                under.append(more.rstrip())
            if under:
                record[("under", line.rstrip(), "\n".join(under))] += 1
    if kept:
        record[("order", "\n".join(kept))] += 1
    for line in seen_notes(split[1] if split else text):
        record[("seen", line)] += 1
    return record


def record_findings(path: str, was: Counter, now: Counter) -> list:
    """One line for each way a patch would change a person's record in one concept, naming the actor and the day and never the words."""
    findings = []
    gone = {e[1] for e in was - now if e[0] == "note"}
    came = {e[1] for e in now - was if e[0] == "note"}
    for what, entry in [("remove", e) for e in sorted(was - now)] + [("add", e) for e in sorted(now - was)]:
        if entry[0] == "order":
            # The same notes in another order: the curator quotes the first.
            if what == "add" and not gone and not came and any(e[0] == "order" for e in was):
                findings.append(f"{path}: this patch would put the notes people left in another order; leave the {OPEN_Q} section as it stands")
        elif entry[0] == "under":
            if entry[1] not in gone and entry[1] not in came:
                who = re.match(r"^[\s>]*\S+\s+(?:\[[ xX]\]\s+)?(\d{4}-\d{2}-\d{2})\s*,\s*(human\\?:[^ :]*|process:ktl-curator)", entry[1])
                name = f"{who.group(2)}, {who.group(1)}" if who else "a person"
                findings.append(f"{path}: this patch would {'take lines from' if what == 'remove' else 'add lines to'} a note a person left ({name}); only ktl-curator changes one, on that person's word")
        elif entry[0] == "seen":
            # A note that left the file is reported as removed. One still in
            # the file that the report no longer lists was hidden: a second
            # heading above it, or a fence opened and never closed.
            if what == "remove" and entry[1] not in gone:
                who = re.match(r"^- (\d{4}-\d{2}-\d{2}), *(human:[^ :]*)", entry[1])
                findings.append(
                    f"{path}: this patch would hide a note a person left ({who.group(2)}, {who.group(1)}) from the report; "
                    f"add no second {OPEN_Q} heading, and close every code fence the new text opens"
                )
        elif entry[0] == "note":
            who = re.match(r"^- (\d{4}-\d{2}-\d{2}), *(human:[^ :]*|process:ktl-curator)", entry[1])
            name = f"{who.group(2)}, {who.group(1)}" if who else "a person"
            if what == "remove":
                findings.append(f"{path}: this patch would remove a note a person left ({name}); only ktl-curator clears one, on that person's word, and a rewrite carries the {OPEN_Q} section over only when its own body has none")
            else:
                findings.append(f"{path}: this patch would add a note in a person's name ({name}); only ktl-curator records one, on that person's word")
        else:
            findings.append(f"{path}: this patch would {what} a person's {entry[0]} event ({entry[1]}, {entry[2] or 'no time'}); only ktl-curator writes one, in a live session")
    return findings


def line_offsets(body: str):
    lines = body.split("\n")
    offsets, pos = [], 0
    for line in lines:
        offsets.append(pos)
        pos += len(line) + 1
    return lines, offsets


def related_span(body: str):
    """(start, end) of the lokf:related block: a marker line, then an end-marker line. A mention in prose is not a block."""
    lines, offsets = line_offsets(body)
    for i, line in enumerate(lines):
        if line.strip() == RELATED_START:
            for j in range(i + 1, len(lines)):
                if lines[j].strip() == RELATED_END:
                    return (offsets[i], offsets[j] + len(lines[j]))
            return None
    return None


def questions_span(body: str):
    """(start, end) of the ## Open questions section: its heading line to the next ## heading or the end. A heading shown inside a code fence is an example, not the section."""
    lines, offsets = line_offsets(body)
    fenced = False
    for i, line in enumerate(lines):
        if line.startswith("```") or line.startswith("~~~"):
            fenced = not fenced
            continue
        if not fenced and line.strip() == OPEN_Q:
            end = len(body)
            for j in range(i + 1, len(lines)):
                if lines[j].startswith("## "):
                    end = offsets[j]
                    break
            return (offsets[i], end)
    return None


def autolinked(text: str) -> str:
    """The line with each bare web address outside a code span written as an autolink, <https://...>. Markdown linters refuse a bare one (markdownlint's MD034), and the curator reads the line in a rendered view, where an autolink is a link."""
    parts = re.split(r"(`[^`]*`)", text)
    return "".join(part if part.startswith("`") else BARE_URL_RE.sub(r"<\g<0>>", part) for part in parts)


def clean_question(value, what: str) -> str:
    """A reader's question as the ledger holds it: one line, no character a reader cannot see, no backtick to close the code span it sits in, and no longer than a question is."""
    text = shown(one_line(value, what)).replace("`", "'")
    if not text:
        raise Refused(f"{what} holds no printable text")
    return text[:300].rstrip()


def handoff_lines(value) -> list:
    """The patch's lines for the reviewer: one line of printable text each, with no backtick to close the code block they are shown in."""
    if value is None:
        return []
    if not isinstance(value, list) or not value:
        raise Refused("handoff is a list of lines for the reviewer")
    if len(value) > HANDOFF_LINES:
        raise Refused(f"handoff holds {len(value)} lines; a reviewer gets at most {HANDOFF_LINES}")
    lines = []
    for n, item in enumerate(value, start=1):
        text = shown(one_line(item, f"handoff line {n}")).replace("`", "'")
        if not text:
            raise Refused(f"handoff line {n} holds no printable text")
        if len(text) > HANDOFF_CHARS:
            raise Refused(f"handoff line {n} is {len(text)} characters; a line is at most {HANDOFF_CHARS}")
        lines.append(text)
    return lines


def protected_spans(body: str):
    return [s for s in (related_span(body), questions_span(body)) if s]


def overlaps(spans, start: int, end: int) -> bool:
    return any(start < e and end > s for s, e in spans)


class Concept:
    def __init__(self, path: str, text: str | None):
        self.path = path
        self.deleted = False
        self.touched = False
        self.record = person_record(text)  # what the file holds in a person's name, before any operation
        self.targets_before: set = set()
        if text is None:
            self.fm, self.body = {}, ""
            return
        split = split_frontmatter(text)
        if split is None:
            raise Refused(f"{path}: no closed frontmatter block, so this script cannot read it")
        fm_text, body = split
        try:
            fm = read_yaml(fm_text)
        except yaml.YAMLError as exc:
            raise Refused(f"{path}: frontmatter is not valid YAML ({' '.join(str(exc).split())[:80]})")
        if not isinstance(fm, dict):
            raise Refused(f"{path}: frontmatter is not a mapping")
        self.fm, self.body = fm, body
        # The block as the file holds it, and what it parsed to. An operation
        # that leaves the frontmatter as it was, such as `resolve`, writes
        # this text back, so a comment or a folded line a person wrote stays.
        self.fm_text, self.fm_read = fm_text, copy.deepcopy(fm)
        self.targets_before = relation_targets(fm)

    def text(self) -> str:
        """The concept as it would be written: the frontmatter re-dumped only when an operation changed it."""
        if getattr(self, "fm_text", None) is not None and self.fm == self.fm_read:
            return "---\n" + self.fm_text + "\n---\n" + self.body.rstrip("\n") + "\n"
        return dump(self.fm, self.body)

    def events(self) -> list:
        v = self.fm.get("verified")
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list):
            return [e for e in v if isinstance(e, dict)]
        return []

    def authored_by_person(self) -> bool:
        g = self.fm.get("generated")
        return isinstance(g, dict) and str(g.get("by", "")).startswith("human:")

    def confirmed_by_person(self) -> bool:
        return any(str(e.get("by", "")).startswith("human:") for e in self.events())

    def retired(self) -> bool:
        """`status: deprecated`, which only the curator writes, on a person's word."""
        return str(self.fm.get("status", "")).strip().lower() == "deprecated"

    def noted_by_person(self) -> bool:
        q = questions_span(self.body)
        if q is None:
            return False
        actors = (BULLET_RE.match(line) for line in self.body[q[0]:q[1]].split("\n"))
        return any(m is not None and m.group(1).startswith("human:") for m in actors)

    def noted_by_curator(self) -> bool:
        """A send-back the curator left under a `process:ktl-curator` actor, which stands for a person who could not sign in. The librarian re-derives such a concept but never deletes it or clears the note; only the curator does, on Confirm or Correct."""
        q = questions_span(self.body)
        if q is None:
            return False
        return any(CURATOR_NOTE_RE.match(line) for line in self.body[q[0]:q[1]].split("\n"))

    def title(self) -> str:
        return " ".join(str(self.fm.get("title", self.path)).split())

    def description(self) -> str:
        return " ".join(str(self.fm.get("description", "")).split())


class Bundle:
    def __init__(self, root: Path, by: str, now: str, today: str, log: str | None = None):
        self.root = root
        self.knowledge = root / ".lokf" / "knowledge"
        self.feedback = root / ".lokf" / "feedback.md"
        self.ledger = root / ".lokf" / "questions.md"
        self.by, self.now, self.today = by, now, today
        self.concepts: dict[str, Concept] = {}
        self.indexes: dict[Path, str] = {}
        self.log_lines: list[str] = []
        self.patch_log = log  # the patch's own line, already labelled, for each operation that gives none
        self.feedback_handled: list[str] = []
        self.ledger_lines: list[str] = []
        self.demoted: list[str] = []  # concepts a person confirmed that this run edited
        self.shared_confirmed: list[str] = []  # those of them the patch's own log line speaks for
        self.base_iri = self.read_base_iri()

    def read_base_iri(self) -> str:
        try:
            split = split_frontmatter((self.knowledge / "index.md").read_text(encoding="utf-8"))
            fm = read_yaml(split[0]) if split else None
        except (yaml.YAMLError, UnicodeDecodeError) as exc:
            raise Refused(f"index.md: the bundle's root index.md cannot be read ({' '.join(str(exc).split())[:80]})")
        base = fm.get("base_iri") if isinstance(fm, dict) else None
        if not isinstance(base, str) or not base:
            raise Refused("index.md: the bundle's root index.md carries no base_iri, so no id can be minted")
        return base

    def concept(self, path: str, must_exist: bool) -> Concept:
        if path not in self.concepts:
            file = self.knowledge / path
            # A folder of the bundle that is a link to one outside it would
            # have this script write there, under a path that reads as the
            # bundle's. Conventions rule 9 refuses a concept that is a link.
            inside = self.knowledge.resolve()
            if file.is_symlink() or inside not in (file.parent.resolve(), *file.parent.resolve().parents):
                raise Refused(f"{path}: a link on this path leads out of the bundle, so nothing is read or written through it")
            self.concepts[path] = Concept(path, file.read_text(encoding="utf-8") if file.is_file() else None)
            if not file.is_file():
                self.concepts[path].deleted = True  # absent until created
        c = self.concepts[path]
        if must_exist and c.deleted:
            raise Refused(f"{path}: no such concept")
        if not must_exist and not c.deleted:
            raise Refused(f"{path}: already exists; use patch or rewrite")
        return c

    # ---- the operations -------------------------------------------------
    def create(self, op: dict) -> None:
        path = op["path"]
        c = self.concept(path, must_exist=False)
        fm_in = op.get("frontmatter")
        if not isinstance(fm_in, dict):
            raise Refused(f"{path}: create needs a frontmatter mapping")
        denied = sorted(k for k in fm_in if k.lower() in DENIED_CREATE)
        if denied:
            raise Refused(f"{path}: create may not set {', '.join(denied)}; the script stamps provenance and status")
        if not isinstance(fm_in.get("type"), str) or not fm_in["type"]:
            raise Refused(f"{path}: create needs a type")
        title = one_line(fm_in.get("title"), f"{path}: title")
        description = one_line(fm_in.get("description"), f"{path}: description")
        if "]" in title or "[" in title:
            raise Refused(f"{path}: a title may not contain square brackets, which the index bullet uses")
        minted = self.base_iri + path[: -len(".md")]
        given = fm_in.get("id")
        if given is not None and given != minted:
            raise Refused(f"{path}: id must be {minted} (base_iri plus the path), not {given}")
        self.check_excerpts(path, fm_in.get("sources") or [])
        fm: dict = {"type": fm_in["type"], "id": minted}
        for k, v in fm_in.items():
            if k not in ("type", "id"):
                fm[k] = v
        fm["title"], fm["description"] = title, description
        fm["generated"] = self.stamp(op)
        fm["status"] = "draft"
        body = op.get("body")
        if not isinstance(body, str) or not body.strip():
            raise Refused(f"{path}: create needs a body")
        c.fm, c.body, c.deleted, c.touched = fm, "\n" + body.strip("\n") + "\n", False, True
        self.index_set(path, title, description)
        self.log(op, f"**Added**: {title}, from `{fm.get('resource', 'the repository')}`.")

    def stamp(self, op: dict) -> dict:
        g = {"by": self.by, "at": self.now}
        rev = op.get("revision")
        if rev is not None:
            g["revision"] = one_line(rev, f"{op['path']}: revision")
        return g

    def guard_writable(self, c: Concept, verb: str) -> None:
        if c.authored_by_person():
            raise Refused(f"{c.path}: a person wrote this text, so {verb} is refused; add a question for the curator instead")

    def patch(self, op: dict) -> None:
        path = op["path"]
        c = self.concept(path, must_exist=True)
        self.guard_writable(c, "patch")
        edits = op.get("edits", [])
        sets = op.get("set", {})
        if not isinstance(edits, list) or not isinstance(sets, dict):
            raise Refused(f"{path}: patch takes a list of edits and a mapping of keys to set")
        if not edits and not sets:
            raise Refused(f"{path}: patch changes nothing")
        for edit in edits:
            self.apply_edit(c, edit)
        self.set_frontmatter(c, sets)
        c.fm["generated"] = self.stamp(op)
        c.touched = True
        if c.confirmed_by_person() and path not in self.demoted:
            self.demoted.append(path)
        self.index_set(path, c.title(), c.description())
        self.log(op, None, c)

    @staticmethod
    def check_excerpts(path: str, sources) -> None:
        """Refuses a `sources` value holding an excerpt that is empty or longer than EXCERPT_MAX. Whether the file holds the passage is the toolkit's to say, in schema_findings."""
        for i, entry in enumerate(sources if isinstance(sources, list) else [sources]):
            if not isinstance(entry, dict) or "excerpt" not in entry:
                continue
            quoted = entry["excerpt"]
            size = len(" ".join(quoted.split())) if isinstance(quoted, str) else 0
            if size == 0:
                raise Refused(f"{path}: sources[{i}].excerpt holds no text; copy the passage from the file, or leave the key out")
            if size > EXCERPT_MAX:
                raise Refused(
                    f"{path}: sources[{i}].excerpt is {size} characters and the pen writes at most {EXCERPT_MAX}; "
                    "quote the sentence, the row or the line the claim rests on, and join two passages of one section with ..."
                )

    def set_frontmatter(self, c: Concept, sets) -> None:
        """Sets the frontmatter keys an operation's `set` names. `patch` and `rewrite` both call it, so the two refuse the same keys and check a title and a description the same way. Each calls it before it stamps `generated` and rewrites the index bullets, so the bullets carry a changed title or description."""
        if not isinstance(sets, dict):
            raise Refused(f"{c.path}: set is a mapping of frontmatter keys to their values")
        denied = sorted(k for k in sets if k.lower() in DENIED_SET)
        if denied:
            raise Refused(f"{c.path}: set may not touch {', '.join(denied)}; those belong to the script, the curator or the schema")
        successor = sorted(k for k in sets if k.lower() in SUCCESSOR_KEYS)
        if successor and c.retired():
            raise Refused(f"{c.path}: a person retired this concept, so set may not touch {', '.join(successor)}: its successor is that person's word; name it in the hand-off instead")
        for k, v in sets.items():
            if k in ("title", "description"):
                v = one_line(v, f"{c.path}: {k}")
                if k == "title" and ("[" in v or "]" in v):
                    raise Refused(f"{c.path}: a title may not contain square brackets")
            if k == "sources":
                self.check_excerpts(c.path, v)
            c.fm[k] = v

    def apply_edit(self, c: Concept, edit) -> None:
        if not isinstance(edit, dict) or len(edit) != 1 or next(iter(edit)) not in EDITS:
            raise Refused(f"{c.path}: each edit is one of replace, insert_after or append")
        kind, spec = next(iter(edit.items()))
        if not isinstance(spec, dict) or not isinstance(spec.get("content"), str):
            raise Refused(f"{c.path}: {kind} needs a content string")
        content = spec["content"]
        spans = protected_spans(c.body)
        had_q, had_r = questions_span(c.body) is not None, related_span(c.body) is not None
        if kind == "append":
            self.append_body(c, content)
            return
        target = spec.get("target")
        if not isinstance(target, str) or not target:
            raise Refused(f"{c.path}: {kind} needs a target string")
        if kind == "replace":
            # Only the text this script may edit is searched, so a question
            # that quotes the target does not make it occur twice.
            found, at = [], c.body.find(target)
            while at != -1:
                found.append(at)
                at = c.body.find(target, at + len(target))
            hits = [i for i in found if not overlaps(spans, i, i + len(target))]
            if not hits and found:
                raise Refused(f"{c.path}: the target lies in the lokf:related block or under {OPEN_Q}, which this script never edits")
            if len(hits) != 1:
                raise Refused(f"{c.path}: replace target occurs {len(hits)} times, and must occur exactly once: {target[:60]!r}")
            i = hits[0]
            c.body = c.body[:i] + content + c.body[i + len(target):]
            self.check_protected_intact(c, had_q, had_r)
            return
        lines = c.body.split("\n")
        found = [k for k, line in enumerate(lines) if target in line]
        offsets = [sum(len(line) + 1 for line in lines[:k]) for k in found]
        hits = [k for k, offset in zip(found, offsets) if not overlaps(spans, offset, offset + len(lines[k]))]
        if not hits and found:
            raise Refused(f"{c.path}: the target lies in the lokf:related block or under {OPEN_Q}, which this script never edits")
        if len(hits) != 1:
            raise Refused(f"{c.path}: insert_after target is on {len(hits)} lines, and must be on exactly one: {target[:60]!r}")
        k = hits[0]
        lines[k + 1 : k + 1] = content.rstrip("\n").split("\n")
        c.body = "\n".join(lines)
        self.check_protected_intact(c, had_q, had_r)

    def check_protected_intact(self, c: Concept, had_q: bool, had_r: bool) -> None:
        """An edit whose target ends right at a protected heading could glue it onto the line before, so the section is no longer a heading and the overlap test, which starts at that heading, never saw it. After the edit, a section that was there must still be there."""
        if had_q and questions_span(c.body) is None:
            raise Refused(f"{c.path}: this edit would merge the {OPEN_Q} heading into the text before it, and that section is never edited")
        if had_r and related_span(c.body) is None:
            raise Refused(f"{c.path}: this edit would break the lokf:related block, which this script never edits")

    def append_body(self, c: Concept, content: str) -> None:
        block = "\n" + content.strip("\n") + "\n"
        q = questions_span(c.body)
        if q:
            head = c.body[: q[0]].rstrip("\n")
            c.body = head + "\n" + block + "\n" + c.body[q[0]:]
        else:
            c.body = c.body.rstrip("\n") + "\n" + block

    def rewrite(self, op: dict) -> None:
        path = op["path"]
        c = self.concept(path, must_exist=True)
        self.guard_writable(c, "rewrite")
        body = op.get("body")
        if not isinstance(body, str) or not body.strip():
            raise Refused(f"{path}: rewrite needs a body")
        new = "\n" + body.strip("\n") + "\n"
        related = related_span(c.body)
        if related and related_span(new) is None:
            new = new.rstrip("\n") + "\n\n" + c.body[related[0]:related[1]].strip("\n") + "\n"
        questions = questions_span(c.body)
        if questions and questions_span(new) is None:
            new = new.rstrip("\n") + "\n\n" + c.body[questions[0]:questions[1]].strip("\n") + "\n"
        c.body = new
        self.set_frontmatter(c, op.get("set", {}))
        c.fm["generated"] = self.stamp(op)
        c.touched = True
        if c.confirmed_by_person() and path not in self.demoted:
            self.demoted.append(path)
        self.index_set(path, c.title(), c.description())
        self.log(op, None, c, label="Rewrite")

    def question(self, op: dict) -> None:
        path = op["path"]
        c = self.concept(path, must_exist=True)
        if c.retired():
            raise Refused(f"{path}: a person retired this concept, so question is refused: it would set the status back to draft; name the concept in the hand-off instead")
        text = autolinked(shown(one_line(op.get("text"), f"{path}: question text")))
        if not text:
            raise Refused(f"{path}: question text has no visible characters")
        bullet = f"- {self.today}, {self.by}: {text}"
        q = questions_span(c.body)
        if q:
            section = c.body[q[0]:q[1]].rstrip("\n") + "\n" + bullet + "\n"
            c.body = c.body[: q[0]] + section + c.body[q[1]:]
        else:
            c.body = c.body.rstrip("\n") + "\n\n" + OPEN_Q + "\n\n" + bullet + "\n"
        c.fm["status"] = "draft"
        c.touched = True
        self.log(op, f"**Open question**: {c.title()}: {text}")

    def resolve(self, op: dict) -> None:
        """Withdraws one open question this run's actor asked, once the source settles it. A person's note stays: only the curator clears one, on that person's word. Neither `generated` nor `status` moves, since the question was never part of what the concept claims."""
        path = op["path"]
        c = self.concept(path, must_exist=True)
        target = op.get("target")
        if not isinstance(target, str) or not target.strip():
            raise Refused(f"{path}: resolve needs a target string found in the question")
        if not isinstance(op.get("log"), str) or not op["log"].strip():
            raise Refused(f"{path}: resolve needs a log line saying what settled the question")
        q = questions_span(c.body)
        if q is None:
            raise Refused(f"{path}: no {OPEN_Q} section, so there is no question to resolve")
        section = c.body[q[0]:q[1]].split("\n")
        hits = [k for k, line in enumerate(section) if line.startswith("- ") and target in line]
        if len(hits) != 1:
            raise Refused(f"{path}: resolve target is in {len(hits)} open questions, and must be in exactly one: {target[:60]!r}")
        asker = BULLET_RE.match(section[hits[0]])
        if asker is not None and asker.group(1) == "process:ktl-curator":
            raise Refused(f"{path}: that is a curator's send-back, not a question to withdraw; only the curator clears it, on Confirm or Correct")
        if asker is None or asker.group(1) != self.by:
            raise Refused(f"{path}: that question is not one {self.by} asked; a person's note is the curator's to clear, on that person's word")
        del section[hits[0]]
        if any(line.strip() for line in section[1:]):
            c.body = c.body[: q[0]] + "\n".join(section) + c.body[q[1]:]
        else:  # the heading goes with its last question
            head, tail = c.body[: q[0]].rstrip("\n"), c.body[q[1]:].lstrip("\n")
            c.body = head + "\n" + ("\n" + tail if tail else "")
        c.touched = True
        self.log(op, None, None, label="Resolved")

    def recheck(self, op: dict) -> None:
        """This run's own event replaces its previous one where it stood, so a person's events keep their place."""
        c = self.concept(op["path"], must_exist=True)
        events = c.events()
        mine = [k for k, e in enumerate(events) if e.get("by") == self.by]
        event = {"by": self.by, "at": self.now}
        if mine:
            events[mine[0]] = event
            for k in reversed(mine[1:]):
                del events[k]
        else:
            events.append(event)
        c.fm["verified"] = events
        c.touched = True

    def reindex(self, op: dict) -> None:
        """Both index bullets re-derived from the frontmatter as it stands. The concept is read, never written, so it works on a person's text too. An index that lists the concept inside a line of its own making keeps that line."""
        c = self.concept(op["path"], must_exist=True)
        self.index_set(op["path"], c.title(), c.description())

    def delete(self, op: dict) -> None:
        path = op["path"]
        c = self.concept(path, must_exist=True)
        if not (self.knowledge / path).is_file():
            raise Refused(f"{path}: this patch creates the concept, so there is no file to delete; drop both operations")
        if c.confirmed_by_person():
            raise Refused(f"{path}: a person confirmed this concept, so delete is refused; add a question saying the source is gone, and the curator retires it")
        if c.noted_by_person():
            raise Refused(f"{path}: a person left a note on this concept, so delete is refused; add a question saying the source is gone, and the curator retires it")
        if c.noted_by_curator():
            raise Refused(f"{path}: the curator left a send-back on this concept, so delete is refused; re-derive it and leave the note for the curator")
        if c.retired():
            raise Refused(f"{path}: a person retired this concept, so delete is refused; a retired concept stays for links and history")
        self.guard_writable(c, "delete")
        if not isinstance(op.get("log"), str) or not op["log"].strip():
            raise Refused(f"{path}: delete needs a log line saying why")
        c.deleted, c.touched = True, True
        self.index_set(path, None, None)
        self.log(op, f"**Removal**: {c.title()}.")

    # ---- relations ------------------------------------------------------
    def concept_id(self, path: str, fm: dict) -> str:
        own = fm.get("id")
        return own if isinstance(own, str) and own else self.base_iri + path[:-3]

    def resolves(self, target: str, citing: str, ids: dict) -> str | None:
        """The concept's path a target names among ids, as knowledge-report.sh finds it. An IRI outside the bundle names none."""
        if target in ids:
            return ids[target]
        target = target.split("#", 1)[0]
        if SCHEME.match(target):
            if not target.startswith(self.base_iri):
                return None
            target = target[len(self.base_iri):]
        target = target[2:] if target.startswith("./") else target.lstrip("/")
        target = target[:-3] if target.endswith(".md") else target
        return ids.get(self.base_iri + target) or ids.get(self.base_iri + f"{citing.rsplit('/', 1)[0]}/{target}")

    def relation_findings(self) -> list:
        """What this patch breaks in the graph: a relation it adds to nothing, and a relation left pointing at a concept it deletes.

        Only `--check-refs` would catch either, after the patch is written, and a
        relation that was already broken is no fault of this patch. The whole
        bundle is read only when a patch adds a relation or deletes a concept,
        so a patch of bodies costs no more on a large bundle.
        """
        added = {path: relation_targets(c.fm) - c.targets_before for path, c in self.concepts.items() if c.touched and not c.deleted}
        added = {path: found for path, found in added.items() if found}
        gone = [path for path, c in self.concepts.items() if c.touched and c.deleted and (self.knowledge / path).is_file()]
        if not added and not gone:
            return []
        before, after, standing = {}, {}, {}
        for file in sorted(self.knowledge.rglob("*.md")):
            path = file.relative_to(self.knowledge).as_posix()
            if file.name in NOT_CONCEPTS or path == ROOT_MAP or ".obsidian" in path.split("/"):
                continue
            try:
                split = split_frontmatter(file.read_text(encoding="utf-8"))
                fm = read_yaml(split[0]) if split else None
            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                continue  # a concept this script cannot read is refused when an operation names it
            if not isinstance(fm, dict):
                continue
            before[self.concept_id(path, fm)] = path
            if path not in self.concepts:
                after[self.concept_id(path, fm)] = path
                standing[path] = fm
        for path, c in self.concepts.items():
            if not c.deleted:
                after[self.concept_id(path, c.fm)] = path
                standing[path] = c.fm
        findings = []
        for path, found in sorted(added.items()):
            for field, target in sorted(found):
                outside = SCHEME.match(target) and not target.startswith(self.base_iri)
                if not outside and not self.resolves(target, path, after):
                    findings.append(f"{path}: {field} names {shown(target)}, and no concept of the bundle has that id; name a concept that exists, or create it in this patch")
        for path, fm in sorted(standing.items()):
            for field, target in sorted(relation_targets(fm) | domain_iris(fm)):
                named = self.resolves(target, path, before)
                if named in gone and not self.resolves(target, path, after):
                    findings.append(f"{path}: {field} still names {named}, which this patch deletes; drop or repoint the relation in this patch, or add a question to the concept if a person wrote it")
        return findings

    def source_findings(self) -> list:
        """Rule 16 across the bundle, for the `sources` entries this patch adds or changes: one id names one resource and one excerpt.

        A clash the patch did not make is left to the gate.
        """
        def entries(fm) -> set:
            found = fm.get("sources") if isinstance(fm, dict) else None
            found = [found] if isinstance(found, dict) else found if isinstance(found, list) else []
            return {(str(e["id"]), material(e.get("resource")), e.get("excerpt") if isinstance(e.get("excerpt"), str) else None)
                    for e in found if isinstance(e, dict) and e.get("id") is not None}

        added = {path: entries(c.fm) - entries(getattr(c, "fm_read", {})) for path, c in self.concepts.items() if c.touched and not c.deleted}
        added = {path: found for path, found in added.items() if found}
        if not added:
            return []
        uses: dict = {}
        for path, fm in self.standing().items():
            for label, resource, excerpt in entries(fm):
                uses.setdefault(label, []).append((path, resource, excerpt))
        findings = []
        for path, found in sorted(added.items()):
            for label, resource, excerpt in sorted(found, key=str):
                for other, theirs, quoted in sorted(uses.get(label, []), key=str):
                    if other == path:
                        continue
                    if theirs != resource:
                        findings.append(f"{path}: sources id {label} names {resource} here and {theirs} in {other}; one id names one resource across the bundle, so give this entry an id of its own and use it in the footnote")
                    elif excerpt is not None and quoted is not None and quoted != excerpt:
                        findings.append(f"{path}: sources id {label} quotes another passage in {other}; one id is one source node across the bundle, which holds one excerpt, so give this entry an id named after its passage and use it in the footnote")
                    else:
                        continue
                    break
        return findings

    def standing(self) -> dict:
        """Each concept's frontmatter as the bundle would hold it after this patch, by path."""
        standing = {}
        for file in sorted(self.knowledge.rglob("*.md")):
            path = file.relative_to(self.knowledge).as_posix()
            if path in self.concepts or file.name in NOT_CONCEPTS or path == ROOT_MAP or ".obsidian" in path.split("/"):
                continue
            try:
                split = split_frontmatter(file.read_text(encoding="utf-8"))
                fm = read_yaml(split[0]) if split else None
            except (OSError, UnicodeDecodeError, yaml.YAMLError):
                continue  # a concept this script cannot read is refused when an operation names it
            if isinstance(fm, dict):
                standing[path] = fm
        for path, c in self.concepts.items():
            if not c.deleted:
                standing[path] = c.fm
        return standing

    # ---- index, log, feedback -------------------------------------------
    def index_text(self, file: Path, default: str) -> str:
        if file not in self.indexes:
            self.indexes[file] = file.read_text(encoding="utf-8") if file.is_file() else default
        return self.indexes[file]

    def index_set(self, path: str, title, description) -> None:
        folder, name = path.rsplit("/", 1)
        section = folder.rsplit("/", 1)[-1].capitalize()
        folder_file = self.knowledge / folder / "index.md"
        root_file = self.knowledge / "index.md"
        folder_text = self.index_text(folder_file, f"# {section}\n")
        if not folder_text.strip():  # an empty file starts from its heading, as a new one does
            folder_text = f"# {section}\n"
        # The " - " in a bullet introduces the description. A concept with no
        # description gets its link alone, so no bullet ends in a bare dash.
        tail = f" - {description}" if description else ""
        self.indexes[folder_file] = self.place_bullet(
            folder_text, name, None if title is None else f"* [{title}]({name}){tail}", path, f"{folder}/index.md")
        self.indexes[root_file] = self.place_bullet(
            self.index_text(root_file, ""), path,
            None if title is None else f"* [{title}]({path}){tail}", path, "index.md",
            section=(section, f"]({folder}/index.md)"))

    @staticmethod
    def place_bullet(text: str, link: str, bullet, path: str, where: str, section=None) -> str:
        """Sets, adds or removes one concept's bullet in one index.md, with None for bullet on delete.

        The concept's own bullet is a line that holds its link alone,
        optionally followed by its description; every such line is rewritten.
        A line that lists the concept among other links, or names it in a
        sentence, is the host's own way of listing it. Create, set and reindex
        leave it alone, as rule 12 does, and delete takes the link out of a
        list of links. A mention inside another concept's bullet lists nothing.
        `section` is the folder's heading text and a link to the folder's
        index.md, given for the root index only.
        """
        lines = text.split("\n")
        own = re.compile(r"^\* \[[^\]]*\]\(" + re.escape(link) + r"\)(?: - .*)?$")
        mine = [k for k, line in enumerate(lines) if own.match(line)]
        ref = Bundle.link_ref(link)
        if bullet is None:
            for k in reversed(mine):
                del lines[k]
                if 0 < k < len(lines) and lines[k - 1] == "" and lines[k] == "":
                    del lines[k]  # the blank line on either side of it, now two in a row
            lines = [Bundle.unlink(line, link, path, where) if ref.search(line) else line for line in lines]
            if section is not None:
                lines = Bundle.drop_empty_section(lines, section[0])
            return Bundle.joined(lines)
        if mine:
            for k in mine:
                lines[k] = bullet
            return Bundle.joined(lines)
        if any(ref.search(line) and not OWN_BULLET_RE.match(line) for line in lines):
            return Bundle.joined(lines)
        start, end = 0, len(lines)
        if section is not None:
            found = Bundle.find_section(lines, *section)
            if found is None:
                level = Bundle.section_level(lines)
                return text.rstrip("\n") + "\n\n" + "#" * level + f" {section[0]}\n\n" + bullet + "\n"
            start, end = found
        bullets = [k for k in range(start, end) if lines[k].startswith("* [")]
        if bullets:
            lines.insert(bullets[-1] + 1, bullet)
        else:  # after the section's last line of text, with a blank line on each side
            last = end - 1
            while last > start and lines[last] == "":
                last -= 1
            lines[last + 1 : last + 1] = ["", bullet]
            if last + 3 < len(lines) and lines[last + 3] != "":
                lines.insert(last + 3, "")
        return Bundle.joined(lines)

    @staticmethod
    def drop_empty_section(lines: list, name: str) -> list:
        """The lines without the heading named after a folder when nothing but blank lines is left under it."""
        heads = Bundle.headings(lines)
        for i, (k, level, text) in enumerate(heads):
            if i == 0 or text.lower() != name.lower():
                continue
            end = next((k2 for k2, level2, _ in heads[i + 1 :] if level2 <= level), len(lines))
            if any(line.strip() for line in lines[k + 1 : end]):
                continue
            while k > 0 and lines[k - 1] == "":
                k -= 1
            lines = lines[:k] + ([""] if end < len(lines) and k > 0 else []) + lines[end:]
            break
        return lines

    def index_writes(self) -> list:
        """Each index.md this patch changed, with None for a folder's index left holding only its heading, no concept beside it and no link to it."""
        out = []
        for file, text in self.indexes.items():
            if file != self.knowledge / "index.md" and len([line for line in text.split("\n") if line.strip()]) == 1 and HEADING_RE.match(text.strip()):
                folder = file.parent.relative_to(self.knowledge).as_posix()
                left = {f.relative_to(self.knowledge).as_posix() for f in file.parent.rglob("*.md") if f != file}
                left -= {p for p, c in self.concepts.items() if c.deleted}
                left |= {p for p, c in self.concepts.items() if not c.deleted and p.startswith(folder + "/")}
                if not left and not self.linked_from_an_index(file):
                    text = None
            out.append((file, text))
        return out

    def linked_from_an_index(self, folder_index: Path) -> bool:
        """Whether another index.md, as this patch leaves it, links to the folder or its index.md."""
        others = set(self.knowledge.rglob("index.md")) | set(self.indexes)
        for other in sorted(others):
            if other == folder_index or ".obsidian" in other.relative_to(self.knowledge).parts:
                continue
            text = self.indexes.get(other)
            if text is None:
                try:
                    text = other.read_text(encoding="utf-8")
                except (OSError, UnicodeDecodeError):
                    continue
            rel = Path(os.path.relpath(folder_index.parent, other.parent)).as_posix()
            if re.search(r"\]\((?:\./)?" + re.escape(rel) + r"(?:/(?:index\.md)?)?(?:#[^)]*)?\)", text):
                return True
        return False

    @staticmethod
    def joined(lines: list) -> str:
        return "\n".join(lines).rstrip("\n") + "\n"

    @staticmethod
    def link_ref(link: str) -> "re.Pattern[str]":
        """A Markdown link to the concept, with or without a leading `./` and a `#fragment`. A bare `]({link})` match would miss both forms and leave the link dangling after a delete."""
        return re.compile(r"\]\((?:\./)?" + re.escape(link) + r"(?:#[^)]*)?\)")

    @staticmethod
    def unlink(line: str, link: str, path: str, where: str) -> str:
        """The line with the concept's link taken out of a comma-separated list of links, where a link stands next to it. A link anywhere else, in a sentence say, is refused: the host's text is not this script's to reword. The `./` and the `#fragment` are matched as link_ref matches them, so neither form is left behind."""
        item = r"\[[^\]]*\]\((?:\./)?" + re.escape(link) + r"(?:#[^)]*)?\)"
        after_link = re.compile(r"(\]\([^)]*\)), " + item)
        before_link = re.compile(item + r", (?=\[[^\]]*\]\()")
        ref = Bundle.link_ref(link)
        while ref.search(line):
            new, n = after_link.subn(r"\1", line, count=1)
            if not n:
                new, n = before_link.subn("", line, count=1)
            if not n:
                raise Refused(f"{path}: {where} links this concept inside other text, which this script never rewrites; a person takes that link out, and the delete can then run")
            line = new
        return line

    @staticmethod
    def headings(lines: list) -> list:
        """(line, level, text) for each heading outside the frontmatter and outside a code fence."""
        found, fenced = [], False
        body = 0
        if lines and lines[0] == "---":
            body = next((k + 1 for k in range(1, len(lines)) if lines[k] == "---"), len(lines))
        for k, line in enumerate(lines):
            if k < body:
                continue
            if line.startswith("```") or line.startswith("~~~"):
                fenced = not fenced
                continue
            m = None if fenced else HEADING_RE.match(line)
            if m:
                found.append((k, len(m.group(1)), m.group(2)))
        return found

    @staticmethod
    def find_section(lines: list, name: str, folder_link: str):
        """(start, end) of the root section a folder's bullets go under: a heading named after the folder, at any level, or else a section that links the folder's index.md. A heading that does both wins, then the narrowest. The first heading is the title, whose section is the whole file, so it never wins by a link."""
        heads = Bundle.headings(lines)
        spans = []
        for i, (k, level, text) in enumerate(heads):
            end = next((k2 for k2, level2, _ in heads[i + 1 :] if level2 <= level), len(lines))
            spans.append((i, k, end, text))
        named = {(k, end) for i, k, end, text in spans if text.lower() == name.lower()}
        linked = {(k, end) for i, k, end, _ in spans if i > 0 and any(folder_link in line for line in lines[k:end])}
        for matches in (named & linked, named, linked):
            if matches:
                return min(matches, key=lambda span: span[1] - span[0])
        return None

    @staticmethod
    def section_level(lines: list) -> int:
        """The heading level the root index gives its sections: the shallowest heading after its title, or 1."""
        levels = [level for _, level, _ in Bundle.headings(lines)[1:]]
        return min(levels) if levels else 1

    def log(self, op: dict, default: str | None, c: Concept | None = None, label: str = "Changed") -> None:
        text = op.get("log")
        shared = text is None and self.patch_log is not None
        if text is not None:
            text = log_line(text, f"{op['path']}: log", label)
        elif shared:
            text = self.patch_log
        elif default is None:
            raise Refused(f"{op['path']}: {op['op']} needs a log line naming what changed and why, its own or the patch's")
        else:
            text = default
        fb = op.get("from_feedback")
        if c is not None and c.confirmed_by_person() and "edited since" not in text.lower():
            if shared and fb is None:
                # The patch's line speaks for many concepts. It is written
                # once, and one sentence after it names each concept a person
                # had confirmed.
                if c.path not in self.shared_confirmed:
                    self.shared_confirmed.append(c.path)
            elif shared:
                text += f" `{c.path}` was edited since a person confirmed it; the label says so until the curator looks again."
            else:
                text += " Edited since a person confirmed it; the label says so until the curator looks again."
        asked = op.get("asked")
        if asked is not None and fb is None:
            raise Refused(f"{op['path']}: asked goes with from_feedback; it is the reader's question from that entry")
        if fb is not None:
            if not isinstance(fb, str):
                raise Refused(f"{op['path']}: from_feedback is the exact one-line entry as feedback.md holds it")
            fb = fb.rstrip("\n")
            if "\n" in fb or not fb.startswith("- **"):
                raise Refused(f"{op['path']}: from_feedback is the exact one-line entry as feedback.md holds it")
            if fb in self.feedback_handled:
                raise Refused(f"{op['path']}: from_feedback names an entry another operation of this patch already handles; one operation answers each entry")
            self.feedback_handled.append(fb)
            text = "**From reader feedback**: " + re.sub(r"^\*\*[^*]+\*\*: ?", "", text)
            # The entry leaves feedback.md for the ledger: the day, its kind and
            # the concept that now answers it, with the reader's question in a
            # code span so that none of it renders or reads as Markdown.
            kind = FEEDBACK_KIND_RE.match(fb)
            line = f"- {self.today} {kind.group(1) if kind else 'Feedback'} {op['path']}"
            if asked is not None:
                line += ": `" + clean_question(asked, f"{op['path']}: asked") + "`"
            self.ledger_lines.append(line)
        self.log_lines.append("* " + autolinked(text))

    def log_text(self) -> str | None:
        if not self.log_lines:
            return None
        # A line given by many operations, the patch's own or the same words
        # in each, is written once, where it first appears.
        self.log_lines = list(dict.fromkeys(self.log_lines))
        if self.shared_confirmed:
            names = [f"`{path}`" for path in self.shared_confirmed]
            if len(names) == 1:
                note = f" {names[0]} was edited since a person confirmed it; the label says so until the curator looks again."
            else:
                note = f" {', '.join(names[:-1])} and {names[-1]} were edited since a person confirmed them; each label says so until the curator looks again."
            plain = "* " + autolinked(self.patch_log)
            self.log_lines = ["* " + autolinked(self.patch_log + note) if line == plain else line for line in self.log_lines]
        file = self.knowledge / "log.md"
        lines = file.read_text(encoding="utf-8").split("\n") if file.is_file() else ["# Change Log", ""]
        first = next((k for k, line in enumerate(lines) if line.startswith("## ")), None)
        if first is not None and lines[first] == f"## {self.today}":
            at = first + 1
            while at < len(lines) and lines[at] == "":
                at += 1
            lines[at:at] = self.log_lines
        else:
            at = len(lines) if first is None else first
            lines[at:at] = [f"## {self.today}", ""] + self.log_lines + [""]
        return "\n".join(lines).rstrip("\n") + "\n"

    def feedback_text(self) -> str | None:
        if not self.feedback_handled:
            return None
        if len(self.feedback_handled) > FEEDBACK_ENTRIES:
            raise Refused(f"feedback.md: this patch handles {len(self.feedback_handled)} reader entries, and one run handles at most {FEEDBACK_ENTRIES}; leave the newer ones for the next run and say in the hand-off how many remain")
        if not self.feedback.is_file():
            raise Refused("feedback.md: an operation handles a feedback entry, but there is no .lokf/feedback.md")
        lines = self.feedback.read_text(encoding="utf-8").split("\n")
        for entry in self.feedback_handled:
            if entry not in lines:
                raise Refused(f"feedback.md: no entry reads exactly {entry[:60]!r}")
            lines.remove(entry)
        out, k = [], 0
        while k < len(lines):  # a day left with no entry loses its heading
            line = lines[k]
            if re.match(r"^## \d{4}-\d{2}-\d{2}$", line):
                j = k + 1
                while j < len(lines) and lines[j] == "":
                    j += 1
                if j >= len(lines) or lines[j].startswith("## "):
                    k = j
                    continue
            out.append(line)
            k += 1
        return "\n".join(out).rstrip("\n") + "\n"

    def ledger_text(self) -> str | None:
        """The ledger with this run's lines appended. It only ever grows: no line already in it is read, moved or rewritten."""
        if not self.ledger_lines:
            return None
        text = self.ledger.read_text(encoding="utf-8").rstrip("\n") + "\n" if self.ledger.is_file() else LEDGER_HEAD
        if not text.endswith("\n\n") and not text.rstrip("\n").split("\n")[-1].startswith("- "):
            text += "\n"  # a file that holds only its heading and paragraph
        return text + "\n".join(self.ledger_lines) + "\n"


def check_path(path) -> str:
    if not isinstance(path, str) or not PATH_RE.fullmatch(path) or ".." in path or path.rsplit("/", 1)[-1] in RESERVED:
        raise Refused(f"path {path!r} is not a concept path: lowercase a-z, 0-9 and hyphens, at least one folder, .md, and not index.md or log.md")
    if path.startswith("knowledge/"):
        raise Refused(f"path {path!r} starts with knowledge/; paths are relative to .lokf/knowledge/")
    return path


def log_line(text, what: str, label: str = "Changed") -> str:
    """One log line as log.md shows it: a single line of visible text, given the operation's label, or `**Changed**`, when it brings none of its own."""
    text = shown(one_line(text, what))
    if not text:
        raise Refused(f"{what} line has no visible characters")
    own = re.match(r"[*_]{2}\s*([^*_]*?)\s*[*_]{2}", text)
    if own and own.group(1).strip(" :").lower() in CURATOR_LABELS:
        raise Refused(f"{what} line starts with **{own.group(1)}**, a line only ktl-curator writes, for a person")
    return text if text.startswith("**") else f"**{label}**: {text}"


def print_diff(file: Path, rel: Path, text: str | None) -> None:
    """The change to one file as a unified diff, the way git shows it, so a reviewer reads it before it is written."""
    try:
        before = file.read_text(encoding="utf-8") if file.is_file() else ""
    except (OSError, UnicodeDecodeError):
        before = ""
    after = text or ""
    old = "/dev/null" if not file.is_file() else f"a/{rel}"
    new = "/dev/null" if text is None else f"b/{rel}"
    sys.stdout.writelines(difflib.unified_diff(before.splitlines(keepends=True), after.splitlines(keepends=True), old, new))
    if after and not after.endswith("\n"):
        print()


def check_keys(op: dict) -> None:
    """Refuses a key the operation does not read, and names it, along with the keys the operation does read."""
    known = ("op", "path", *KEYS[op["op"]])
    unknown = sorted(str(k) for k in op if k not in known)
    if unknown:
        raise Refused(f"{op['path']}: {op['op']} does not take {', '.join(unknown)}; it takes {', '.join(known)}")


# The justfile line that names a domain vocabulary, as the sidecar's template
# writes it: `schema := "<path relative to .lokf/>"`, empty for none. The
# release workflow and knowledge-federate.py read only this form. A `schema`
# line in any other form is reported, not read as no schema: validating a
# domain's concepts against LOKF core alone would refuse every valid one.
SCHEMA_LINE = re.compile(r'^schema := "([^"]*)"$', re.M)
ANY_SCHEMA_LINE = re.compile(r"^(export\s+)?schema\s*:=", re.M)
# The prefixes `lokf validate` gives a finding that fails the check. A failure
# with neither, such as a toolkit without LinkML or a schema file that is not
# there, is the toolkit's, and says nothing about the patch.
FAILING = ("[ERROR]", "[FATAL]")
# A `sources` entry's excerpt, as a line of the frontmatter this script dumps.
EXCERPT_LINE = re.compile(r"^[ \t]+(?:- )?excerpt:", re.M)
# What the toolkit's verdict line says of the excerpts it looked for.
EXCERPT_VERDICT = re.compile(r"(?:Every local excerpt|No local excerpt|\d+ local excerpts? checked)[^\n]*")


def resource_root(lokf_dir: Path) -> Path:
    """Where the toolkit looks for a local `resource` of the bundle in .lokf/knowledge: the nearest folder above the bundle that holds `.git`, else .lokf/ itself. The staged copy sits one folder deeper, so the check below names this root."""
    bundle = (lokf_dir / "knowledge").resolve()
    return next((p for p in (bundle, *bundle.parents) if (p / ".git").exists()), bundle.parent)


def schema_findings(root: Path, files: dict) -> tuple:
    """What `lokf validate` says of the concepts about to be written, as the findings and a note.

    The rules above check what an operation may change, not the shape the
    schema gives a slot: a `sources` entry written as a bare string passes
    them and fails the validator. The concepts are staged in a folder inside
    .lokf/, so the validator finds the sidecar's pyproject.toml. It runs from
    the sidecar's .venv, which needs no network, with the domain vocabulary
    the justfile names, from that file's folder, as the justfile's recipes
    run it. The check is skipped, and the note says why, when the .venv holds
    no toolkit, the toolkit cannot run, or the justfile's schema line is not
    in the form the release reads.

    When a concept carries a `sources[].excerpt`, the validator also looks for
    each excerpt in its local file, as the gate's `just lokf-check-refs` does,
    and counts an excerpt on a URL without fetching it. `--check-excerpts` is
    passed only then, since a toolkit older than lokf 0.9.0 knows neither the
    flag nor the key.
    """
    lokf_dir = root / ".lokf"
    exe = next((p for p in (lokf_dir / ".venv" / "bin" / "lokf", lokf_dir / ".venv" / "Scripts" / "lokf.exe") if p.is_file()), None)
    if exe is None:
        return [], "schema not checked: the lokf toolkit is not installed in .lokf/.venv; run uv sync in .lokf/"
    cmd, cwd = [str(exe), "validate"], lokf_dir
    justfile = lokf_dir / "justfile"
    recipes = justfile.read_text(encoding="utf-8") if justfile.is_file() else ""
    named = SCHEMA_LINE.search(recipes)
    if named is None and ANY_SCHEMA_LINE.search(recipes):
        return [], 'schema not checked: the justfile\'s schema line is not in the form schema := "<file>"'
    if named and named.group(1):
        schema = (lokf_dir / named.group(1)).resolve()
        cmd, cwd = cmd + ["--schema", schema.name], schema.parent
    quoting = any(EXCERPT_LINE.search((split_frontmatter(text) or ("", ""))[0]) for text in files.values())
    if quoting:
        cmd += ["--check-excerpts", "--root", str(resource_root(lokf_dir))]
    stage = Path(tempfile.mkdtemp(dir=str(lokf_dir), prefix=".pen-check-"))
    staged = stage / "knowledge"
    try:
        for rel, text in files.items():
            file = staged / rel
            file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(text, encoding="utf-8", newline="\n")
        done = subprocess.run(cmd + [str(staged)], cwd=str(cwd), capture_output=True, text=True,
                              encoding="utf-8", errors="replace", timeout=600)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [], f"schema not checked: lokf validate could not run ({exc})"
    finally:
        shutil.rmtree(stage, ignore_errors=True)
    if done.returncode == 0:
        note = "schema checked: lokf validate accepts every concept this patch writes"
        said = EXCERPT_VERDICT.search(done.stdout) if quoting else None
        if quoting:
            note += f". {said.group(0).rstrip('.')}" if said else ", and finds each local excerpt in its file"
        return [], note
    out = (done.stdout + done.stderr).replace(str(staged), ".lokf/knowledge")
    lines = [shown(line) for line in out.splitlines() if line.strip()]
    if quoting and not any(line.startswith(FAILING) for line in lines) and "--check-excerpts" in out:
        return ["schema: the toolkit in .lokf/.venv does not take --check-excerpts, so it is older than lokf 0.9.0, "
                "whose schema first holds `excerpt`; raise the floor in .lokf/pyproject.toml and run uv sync, or leave the excerpt out"], ""
    if not any(line.startswith(FAILING) for line in lines):
        return [], f"schema not checked: lokf validate could not run ({lines[0][:200] if lines else f'exit {done.returncode}'})"
    # The validator echoes a rejected concept whole on one line, and gives the
    # reason and a hint on the lines after, so each line is cut at 240
    # characters and all of them are kept.
    return [f"schema: {line[:240]}{' ...' if len(line) > 240 else ''}" for line in lines], ""


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="knowledge-apply.py", add_help=True)
    ap.add_argument("--root")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--diff", action="store_true", help="with --dry-run, also print each change as a unified diff")
    ap.add_argument("--keep", action="store_true", help="keep the patch file after applying it")
    ap.add_argument("--format", action="store_true", help="print the patch file's shape and exit")
    ap.add_argument("--handoff", metavar="FILE", help="after applying, write the patch's hand-off lines to FILE, or empty it")
    ap.add_argument("patch", nargs="?")
    a = ap.parse_args(argv[1:])
    if a.format:
        sys.stdout.write(FORMAT)
        return 0
    if not a.root:
        print("--root <repo-root> is required", file=sys.stderr)
        return 2
    if a.diff and not a.dry_run:
        print("--diff goes with --dry-run: it shows a change before it is written", file=sys.stderr)
        return 2
    # In the agent's step of a scheduled run the wrapper sets this, and applies
    # the patch file itself once the agent has finished. A write here would
    # delete the file and leave a bundle the wrapper refuses, so the pen only
    # checks, and says so.
    deferred = os.environ.get("KNOWLEDGE_PEN_DRY_RUN_ONLY") == "1"
    if deferred and not a.dry_run:
        print("refused: this is the agent's step of a scheduled run, where the pen only checks the patch file (--dry-run). "
              "Leave .lokf/patch.yaml in place: the wrapper applies it after the agent finishes, and the workflow then validates the bundle. "
              "Nothing was written.", file=sys.stderr)
        return 2
    root = Path(a.root).resolve()
    patch_file = Path(a.patch).resolve() if a.patch else root / ".lokf" / "patch.yaml"
    if not (root / ".lokf" / "knowledge" / "index.md").is_file():
        print(f"no bundle at {root / '.lokf' / 'knowledge'}", file=sys.stderr)
        return 2
    if not patch_file.is_file():
        print(f"no patch file at {patch_file}", file=sys.stderr)
        return 2
    raw = patch_file.read_text(encoding="utf-8")
    for n, line in enumerate(raw.split("\n"), start=1):
        if EVENT_RE.match(line) or NOTE_RE.match(line):
            print(f"refused: line {n} of the patch file names a human: actor as an event or a note; only ktl-curator writes one, in a live session")
            return 1
    try:
        doc = read_yaml(raw)
    except yaml.YAMLError as exc:
        print(f"the patch file is not valid YAML: {' '.join(str(exc).split())[:120]}", file=sys.stderr)
        return 2
    if not isinstance(doc, dict) or not isinstance(doc.get("ops"), list) or not doc["ops"]:
        print("the patch file is a mapping with a non-empty `ops` list", file=sys.stderr)
        return 2
    by = doc.get("by", "process:ktl-librarian")
    now = dt.datetime.now(dt.timezone.utc)
    findings: list[str] = []
    if not isinstance(by, str) or not ACTOR_RE.fullmatch(by):
        findings.append(f"by must be a process:<id> actor, not {by!r}")
    elif by.startswith(CURATOR_ACTOR):
        findings.append(f"by may not be {CURATOR_ACTOR}: that actor stands for a person in a curator's session, and only ktl-curator writes under it")
    handoff: list = []
    try:
        handoff = handoff_lines(doc.get("handoff"))
    except Refused as exc:
        findings.append(str(exc))
    patch_log = None
    if doc.get("log") is not None:
        try:
            patch_log = log_line(doc["log"], "log")
        except Refused as exc:
            findings.append(str(exc))
    bundle = None
    if not findings:
        try:
            bundle = Bundle(root, by, now.strftime("%Y-%m-%dT%H:%M:%SZ"), now.strftime("%Y-%m-%d"), patch_log)
        except Refused as exc:
            findings.append(str(exc))
    if bundle is not None:
        for n, op in enumerate(doc["ops"], start=1):
            try:
                if not isinstance(op, dict) or op.get("op") not in OPS:
                    raise Refused(f"op {n}: each operation is a mapping whose op is one of {', '.join(sorted(OPS))}")
                check_path(op.get("path"))
                check_keys(op)
                getattr(bundle, op["op"])(op)
            except Refused as exc:
                findings.append(f"op {n}: {exc}")
            except (OSError, UnicodeDecodeError) as exc:
                findings.append(f"op {n}: {exc}")
        # Each refusal above guards one way in. This compares a person's
        # record in each concept before and after, so it also refuses a body
        # that brings its own `## Open questions` section, a note spelt with
        # an escaped line break, or a second heading above the real one.
        if not findings:
            for path, c in bundle.concepts.items():
                if c.touched:
                    findings.extend(record_findings(path, c.record, Counter() if c.deleted else person_record(c.text())))
            findings.extend(bundle.relation_findings())
            findings.extend(bundle.source_findings())
    for line in findings:
        print(line)
    if findings:
        print(f"refused: {len(findings)} finding(s); nothing was written")
        return 1
    writes: list[tuple[Path, str | None]] = []
    for path, c in bundle.concepts.items():
        if not c.touched:
            continue
        writes.append((bundle.knowledge / path, None if c.deleted else c.text()))
    writes.extend(bundle.index_writes())
    try:
        log_text = bundle.log_text()
    except (OSError, UnicodeDecodeError) as exc:
        print(f"log.md: the log cannot be read ({' '.join(str(exc).split())[:80]})")
        print("refused: 1 finding(s); nothing was written")
        return 1
    if log_text is not None:
        writes.append((bundle.knowledge / "log.md", log_text))
    try:
        fb_text = bundle.feedback_text()
    except Refused as exc:
        print(str(exc))
        print("refused: 1 finding(s); nothing was written")
        return 1
    if fb_text is not None:
        writes.append((bundle.feedback, fb_text))
    ledger_text = bundle.ledger_text()
    if ledger_text is not None:
        writes.append((bundle.ledger, ledger_text))
    concepts = {path: c.text() for path, c in bundle.concepts.items() if c.touched and not c.deleted}
    schema_note = ""
    if concepts:
        top = bundle.knowledge / "index.md"
        concepts["index.md"] = bundle.indexes.get(top) or top.read_text(encoding="utf-8")
        found, schema_note = schema_findings(root, concepts)
        if found:
            for line in found:
                print(line)
            print(f"refused: lokf validate rejects what this patch would write ({len(found)} line(s)); nothing was written")
            return 1
    # The hand-off goes first, outside the bundle, so a file that cannot be
    # written stops the run before the bundle is touched.
    if a.handoff and not a.dry_run:
        try:
            with open(a.handoff, "w", encoding="utf-8", newline="\n") as f:
                f.write("".join(f"{line}\n" for line in handoff))
        except OSError as exc:
            print(f"the hand-off file cannot be written ({exc}); nothing was written")
            return 2
    if a.dry_run:
        for file, text in writes:
            rel = file.relative_to(root)
            print(f"{'would delete' if text is None else 'would write'} {rel}")
            if a.diff:
                print_diff(file, rel, text)
    else:
        # Write each changed file to a temporary file beside it, and put them
        # in place only once all are written, so a write that fails (a
        # read-only file, a full disk) leaves the bundle untouched.
        staged: dict[Path, str] = {}
        try:
            for file, text in writes:
                if text is None:
                    continue
                file.parent.mkdir(parents=True, exist_ok=True)
                fd, tmp = tempfile.mkstemp(dir=str(file.parent), prefix="." + file.name + ".", suffix=".tmp")
                with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
                    f.write(text)
                staged[file] = tmp
                # mkstemp makes a file only its owner reads. The file keeps
                # the mode it had, and a new one takes what the umask leaves.
                os.chmod(tmp, file.stat().st_mode & 0o777 if file.is_file() else 0o666 & ~UMASK)
        except OSError as exc:
            for tmp in staged.values():
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            print(f"a file could not be written ({exc}); nothing was changed")
            return 2
        try:
            for file, text in writes:
                rel = file.relative_to(root)
                if text is None:
                    if file.exists():
                        file.unlink()
                    print(f"deleted {rel}")
                else:
                    os.replace(staged.pop(file), file)
                    print(f"wrote {rel}")
        except OSError as exc:
            for tmp in staged.values():
                try:
                    os.unlink(tmp)
                except OSError:
                    pass
            print(f"a file could not be put in place ({exc}); the files named above were written and the rest were not. Check the bundle with git status before you run the patch again")
            return 2
    if not a.dry_run and not a.keep:
        patch_file.unlink()
    if handoff:
        print(f"hand-off for the reviewer, {len(handoff)} line(s):")
        for line in handoff:
            print(f"  {line}")
    if bundle.demoted:
        print(f"confirmed by a person, and edited {'by this patch' if a.dry_run else 'here'}: {', '.join(bundle.demoted)}; each reads as edited since that confirmation until the curator looks again")
    if not a.dry_run:
        after = "now run lokf validate --check-refs and knowledge-conventions.sh"
    elif deferred:
        after = "leave the patch file in place: the wrapper applies it after you finish, and the workflow validates the bundle"
    else:
        after = "nothing was written: apply it without --dry-run, then run lokf validate --check-refs and knowledge-conventions.sh"
    if schema_note:
        print(schema_note)
    print(f"{'OK (dry run)' if a.dry_run else 'OK'} - {len(doc['ops'])} operation(s) by {by} at {bundle.now}; {after}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
