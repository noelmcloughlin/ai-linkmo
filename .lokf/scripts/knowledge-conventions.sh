#!/usr/bin/env bash
# Conventions of a LOKF bundle that `lokf validate` cannot see. The toolkit
# checks frontmatter against the schema, reads a concept body as an opaque
# string and never reads log.md. The skills and both Obsidian plugins rely
# on these rules, and knowledge-conventions.py gives the detail of each rule
# it checks:
#
#   1. log.md has one `## YYYY-MM-DD` heading per day: the bare ISO date,
#      newest first, no duplicates. OKF §9 makes the date form a MUST, and the
#      KTL Curator plugin finds today's section by that exact heading.
#   2. Every `at:` is a quoted string, and a UTC time to the second, as
#      `date -u +%Y-%m-%dT%H:%M:%SZ` writes it.
#   3. `verified` is a list, never a bare `{ by, at }` mapping, and carries at
#      most one `process:ktl-librarian` event: the librarian replaces its own.
#   4. A bullet under `## Open questions` is `- YYYY-MM-DD, <actor>: ...`, the
#      shape the curator and both plugins write and read. The curator quotes
#      the first bullet, so a trailing signature would become the question.
#   5. Every `resource:` that is not a URL names a file or directory that
#      exists, relative to the repository root: the nearest directory holding
#      `.lokf/`, or else the bundle's parent. URLs are never fetched.
#   6. A commit-shaped `revision` (lokf 0.9.0 and later) on a `generated` or
#      `verified` event names a commit in this repository that holds the
#      concept's local `resource`. ETags, digests and version labels pin URLs
#      and are not checked. The rule needs the full history: outside git it
#      is skipped, and a shallow clone is reported.
#   7. One file per `id`. A sync client's conflict copy or a pasted duplicate
#      passes `lokf validate` and silently merges into the original in the
#      graph.
#   8. Every path in the bundle is lowercase: a-z, 0-9, `.`, `_`, `-`. Two
#      paths that differ only by case collide on Windows, macOS and
#      SharePoint, and sync clients name a conflict copy with a space, a
#      parenthesis or an upper-case host name.
#   9. Every concept is a file, not a symbolic link, and starts with a `---`
#      frontmatter block that closes, with no byte order mark in front of it
#      and no `---` inside it. A BOM or a file with no block would otherwise
#      pass this script unread.
#  10. The fields the provenance gates read line by line are spelt so that a
#      line reader and a parser read the same thing, since both gates refuse
#      an event they cannot read. They are `id`, `verified`, `generated`, and
#      `by`, `at` and `revision` on an event. They carry no quoted or explicit
#      key, space before the colon, escape or block scalar. No value spans
#      lines or sits below its key, and no comment sits beside one or inside
#      a flow form. `resource` keeps the same spellings, though a comment may
#      stand beside it, and `sources` and `exclusions` hold no flow form.
#      The whole block holds no tag, anchor, alias or merge key, on any field:
#      a line reader resolves none of them, and an alias can stand in for an
#      event or a source wherever it sits. The block is not indented whole or
#      one flow mapping, and holds no line break but a line feed.
#  11. No `at:` is later than the commit that first recorded it, or, before
#      it is committed, than now. A time ahead of the clock, such as local
#      time labelled `Z` or a round placeholder, sorts after the edits and
#      confirmations that followed it, so a concept reads as edited since it
#      was confirmed when it was not. A rename or a shallow clone can only
#      make that commit look later, so the rule can miss a bad time but never
#      flags a good one. A time with an offset other than `Z` is not
#      compared. Outside git the rule is skipped.
#  12. An index bullet that names a concept carries that concept's title and
#      description, in the folder's index.md and in the root's. A concept no
#      index lists is not a finding.
#  13. A concept labelled confirmed by a person still says what that person
#      confirmed: an edit to its claims after the commit that recorded the
#      latest confirmation must move `generated.at` past that confirmation.
#  14. A commit that records a person's confirmation changes the verdict, not
#      what the concept says, unless `generated.by` names that same person.
#      The rule reads the commits after `--since <commit>`, and is skipped
#      without it.
#  15. Every concept names where it came from: a top-level `resource`, or a
#      `sources` list with an entry.
#  16. A footnote joins a claim to a source: each footnote in a body uses the
#      `id` of one of the concept's `sources` entries, each id is cited and
#      defined, and one id names one resource across the bundle.
#  17. A logged write has a file behind it: each `**Added**` and
#      `**Deprecation**` bullet in log.md names a concept the bundle holds.
#      The rule reads the bullets added since `--since <commit>`, or without
#      it those under the newest day heading.
#  18. Each `exclusions` entry (lokf 0.9.0 and later) gives a `reason` that is
#      not blank, and no material is both a source and an exclusion of one
#      concept.
#
# Rules 2, 3, 8, 10 and 18 are house rules, stricter than the format: OKF
# permits an unquoted datetime, a bare `verified` mapping, any file name and
# any YAML, and LOKF a blank reason and a material listed both ways. Every
# reader here (the toolkit, both plugins and the gates) reads a bare mapping
# as a one-item list, as it MUST. A bundle written to the letter of OKF may
# fail these rules: that is a policy of the gate, not a defect in the bundle.
#
# This shell half checks rules 1, 5, 6, 8 and 11: they are git and
# filesystem facts, which grep and awk check wherever bash and git run, with
# no toolchain. knowledge-conventions.py, beside this script, checks the
# rules that need a YAML parser.
#
# The Python half runs with the sidecar's .venv when that is Python 3.11 or
# later and holds pyyaml, and otherwise through `uv run` after uv_ready
# (knowledge-apply.sh explains both). Without uv, this script still runs,
# says so, and exits 0 when it finds nothing, or 2 under `--strict`. Every
# workflow passes `--strict`, so a gate never passes rules it did not check.
# When uv cannot install the packages, or a runner cannot start the Python
# half, the script reports a runner failure, not a finding, and exits 2.
#
# Files are read with carriage returns removed and a leading byte order mark
# stripped, so a Windows checkout (`core.autocrlf`) reads the same as CI. The
# sidecar's `.lokf/.gitattributes` keeps tracked files on LF; rule 9 still
# reports a BOM, because other readers do not strip it.
#
# Usage: knowledge-conventions.sh [bundle-dir] [--since <commit>] [--strict]
# (default: knowledge, i.e. run from .lokf/). Exit 1 with one line per
# finding; nothing else is written. Exit 2 when the Python half could not
# run, or under --strict when it was skipped, with the reason on stderr.
[ -n "${BASH_VERSION:-}" ] || { echo "run this with bash: bash ${0##*/} [bundle-dir] [--since <commit>] [--strict]" >&2; exit 2; }
set -euo pipefail

usage() { echo "usage: ${0##*/} [bundle-dir] [--since <commit>] [--strict]" >&2; exit 2; }
# The bundle directory may be a link, on a host that keeps the real folder as
# a visible knowledge_bundle/. Handed a link bare, find never enters it, so
# the trailing slash below is what makes it read the files.
bundle=""; since=""; strict=0
while [ $# -gt 0 ]; do
  case "$1" in
    --since) { [ $# -ge 2 ] && [ -n "$2" ]; } || usage; since="$2"; shift 2 ;;
    --strict) strict=1; shift ;;
    -*) usage ;;
    *) [ -z "$bundle" ] || usage; bundle="$1"; shift ;;
  esac
done
bundle="${bundle:-knowledge}"; bundle="${bundle%/}"
[ -d "$bundle" ] || { echo "no bundle directory at $bundle" >&2; exit 2; }
fail=0
say() { echo "$1"; fail=1; }

# POSIX tools only (head -c, od, tail -c, tr), so this reads the same on
# Linux, macOS and Git for Windows.
has_bom() { [ "$(head -c 3 "$1" | od -An -tx1 | tr -d ' \n')" = "efbbbf" ]; }
clean() { if has_bom "$1"; then tail -c +4 "$1"; else cat "$1"; fi | tr -d '\r'; }

# ---- 1. log.md headings ----------------------------------------------------
log="$bundle/log.md"
if [ -f "$log" ]; then
  if has_bom "$log"; then say "$log: starts with a byte order mark - save as UTF-8 without BOM"; fi
  while IFS= read -r line; do
    say "$log: heading is not a bare ISO date: $line"
  done < <(clean "$log" | grep -E '^## ' | grep -vE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}$' || true)
  dates="$(clean "$log" | grep -oE '^## [0-9]{4}-[0-9]{2}-[0-9]{2}$' | cut -c4- || true)"
  if [ -n "$dates" ]; then
    if ! printf '%s\n' "$dates" | sort -rc 2>/dev/null; then
      say "$log: day headings are not newest-first"
    fi
    while IFS= read -r d; do
      [ -n "$d" ] && say "$log: day $d has more than one heading - add bullets under the existing one"
    done < <(printf '%s\n' "$dates" | uniq -d)
  fi
fi

# ---- 5, 6, 8, 11. concept files ---------------------------------------------
# Repository root for rule 5.
real="$(cd "$bundle" && pwd -P)"
root="$(dirname "$real")"
d="$real"
while [ "$d" != "/" ]; do
  if [ -d "$d/.lokf" ]; then root="$d"; break; fi
  d="$(dirname "$d")"
done
# Whether the root is in a work tree (rules 6 and 11), and whether it is
# shallow (rule 6): a pin the script cannot resolve is not one it has checked.
gitroot="$(git -C "$root" rev-parse --show-toplevel 2>/dev/null || true)"
shallow="$(git -C "$root" rev-parse --is-shallow-repository 2>/dev/null || echo false)"
now="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
# Rule 11's comparison. Times are compared as strings, which is exact once
# both are in one UTC shape: a bare date is its midnight, minutes gain `:00`,
# fractions of a second are dropped, and any other shape is not compared.
# The input starts with the history of the whole bundle, from one walk:
# \001 carries a commit's time, a diff header names the file, and `+` lines
# are what the commit added to it. Then come \002 with now, and the \003
# lines that the fields program below writes. The output is the number, a
# tab and the finding.
# shellcheck disable=SC2016 # awk's own $0, not the shell's
rule11='
function norm(v) {
  gsub(/^["'"'"']|["'"'"']$/, "", v)
  if (v ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$/) return v "T00:00:00Z"
  if (v ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]Z$/) return substr(v, 1, 16) ":00Z"
  if (v ~ /^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9](\.[0-9]+)?Z$/) return substr(v, 1, 19) "Z"
  return ""
}
function value(line) {
  sub(/^[+]?[ \t]*(- )?at:[ \t]*/, "", line); sub(/[ \t]+$/, "", line)
  gsub(/^["'"'"']|["'"'"']$/, "", line)
  return line
}
# A flow form, as `- { by: process:ktl-librarian, at: "2026-09-14T00:00:00Z" }`
# or `verified: [{ by: ..., at: ... }]`, holds its keys inside one line. Each
# value of the key on a line that opens a flow mapping, as written.
function flowvals(l, key, out,   n, v, q, j) {
  n = 0
  if (!index(l, "{")) return 0
  while (match(l, "[{,][ \t]*" key ":[ \t]*")) {
    l = substr(l, RSTART + RLENGTH); q = substr(l, 1, 1)
    if (q == "\"" || q == "\047") { j = index(substr(l, 2), q); v = (j ? substr(l, 1, j + 1) : l) }
    else { v = l; sub(/[,}\]].*/, "", v); sub(/[ \t]+$/, "", v) }
    if (v != "") out[++n] = v
  }
  return n
}
# A path as a diff header prints it, back to the path itself. Git puts a name
# that holds a double quote, a backslash or a control character in double
# quotes, with C escapes, and ends a name that holds a space with a tab.
function gitname(s,  out, i, c, n) {
  sub(/\t$/, "", s)
  if (length(s) < 2 || substr(s, 1, 1) != "\"" || substr(s, length(s), 1) != "\"") return s
  s = substr(s, 2, length(s) - 2); out = ""
  for (i = 1; i <= length(s); i++) {
    c = substr(s, i, 1)
    if (c != "\\") { out = out c; continue }
    c = substr(s, ++i, 1)
    if (c == "t") out = out "\t"
    else if (c == "n") out = out "\n"
    else if (c == "r") out = out "\r"
    else if (c == "a") out = out sprintf("%c", 7)
    else if (c == "b") out = out sprintf("%c", 8)
    else if (c == "f") out = out sprintf("%c", 12)
    else if (c == "v") out = out sprintf("%c", 11)
    else if (c ~ /[0-7]/) { n = c * 64 + substr(s, i + 1, 1) * 8 + substr(s, i + 2, 1); i += 2; out = out sprintf("%c", n) }
    else out = out c
  }
  return out
}
/^\001/ { ct = substr($0, 2); next }
/^\002/ { now = substr($0, 2); next }
/^\003/ {
  split(substr($0, 2), f, "\t"); i = f[1]; p = f[2]; file = f[3]
  v = value(substr($0, length(i) + length(p) + length(file) + 5)); n = norm(v)
  if (n == "" || (i, v) in seen) next
  seen[i, v] = 1
  if ((p, v) in first) {
    if (n > first[p, v]) print i "\t" file ": at \"" v "\" is later than the commit that recorded it (" first[p, v] ") - take the time from date -u when the event happens"
  } else if (n > now) {
    print i "\t" file ": at \"" v "\" is in the future (now " now ") - take the time from date -u when the event happens"
  }
  next
}
/^diff --git / { head = 1; cur = ""; next }
head && /^\+\+\+ / { cur = gitname(substr($0, 5)); sub(/^b\//, "", cur); next }
/^@@/ { head = 0; next }
head { next }
/^[+][ \t]*(- )?at:[ \t]/ { v = value($0); if (!((cur, v) in first)) first[cur, v] = ct; next }
/^[+]/ { m = flowvals($0, "at", got); for (j = 1; j <= m; j++) { v = value(got[j]); if (!((cur, v) in first)) first[cur, v] = ct } }
'
# Each finding is held with the number of its file, the rule's place among
# the four and a sequence number, and printed in that order at the end, so
# the findings of one file stay together.
held=""; seq=0
hold() {  # <file number> <rank> <finding>
  seq=$((seq + 1)); held="$held$1"$'\t'"$2"$'\t'"$seq"$'\t'"$3"$'\n'
}
# What the shell half reads of the bundle, from one awk over every file. The
# paths arrive on standard input as find prints them, numbered from 1 in
# that order, and the links among them in the file KC_LINKS names. Out come
# tab-separated rows, each with the number and the path of its file:
#   P  number  path                    a path out of rule 8 shape
#   E  number  path  target  resource  a local resource rule 5 looks for
#   W  number  path  revision  resource  a commit-shaped revision rule 6 asks git about
# and, in the file KC_ATS names, each `at:` the frontmatter holds, after a
# \003, the number, the path git gives the concept and its path here (rule
# 11).
#
# Rule 8 reads every Markdown file, reserved ones included. The other rules
# read the frontmatter of each concept that is not a link: a link may point
# nowhere, and rule 9 reports it. A file with no block yields nothing here,
# and is rules 2-4, 7 and 9's to report.
#
# For rule 5, a URL, an identifier with a scheme such as urn:ietf:rfc:9110
# or doi:10.1000/182 (two characters at least, so a Windows drive letter is
# still a path), a fragment and the quotes are cut from a value. For rule 6,
# a revision with a character outside [0-9a-f] pins a URL and is skipped, as
# is every revision on a concept whose top-level `resource` is a URL, an
# absolute path or absent.
# shellcheck disable=SC2016 # awk's own $0, not the shell's
fields='
# The same flowvals as in the rule11 program above.
function flowvals(l, key, out,   n, v, q, j) {
  n = 0
  if (!index(l, "{")) return 0
  while (match(l, "[{,][ \t]*" key ":[ \t]*")) {
    l = substr(l, RSTART + RLENGTH); q = substr(l, 1, 1)
    if (q == "\"" || q == "\047") { j = index(substr(l, 2), q); v = (j ? substr(l, 1, j + 1) : l) }
    else { v = l; sub(/[,}\]].*/, "", v); sub(/[ \t]+$/, "", v) }
    if (v != "") out[++n] = v
  }
  return n
}
function after(l, key) { sub("^[ \t]*(- )?" key ":[ \t]*", "", l); sub(/[ \t]+$/, "", l); return l }
function unquote(v) { sub(/^["'"'"']/, "", v); sub(/["'"'"']$/, "", v); return v }
function scheme(v) { return v ~ /^[A-Za-z][A-Za-z0-9+.-]+:/ }
function local(v) {
  if (v ~ /:\/\//) return ""
  sub(/^["'"'"']/, "", v); if (scheme(v)) return ""
  sub(/#.*/, "", v); v = unquote(v); sub(/[ \t]+$/, "", v)
  return v
}
BEGIN {
  BOM = sprintf("%c%c%c", 239, 187, 191); bundle = ENVIRON["KC_BUNDLE"]; pfx = ENVIRON["KC_PREFIX"]; ats = ENVIRON["KC_ATS"]
  while ((getline l < ENVIRON["KC_LINKS"]) > 0) link[l] = 1
}
{
  f = $0; k = NR; rel = f
  if (substr(rel, 1, length(bundle) + 1) == bundle "/") rel = substr(rel, length(bundle) + 2)
  sub(/^\//, "", rel)   # BSD find prints the start point slash, then its own
  if (rel !~ /^([a-z0-9][a-z0-9._-]*\/)*[a-z0-9][a-z0-9._-]*$/) print "P\t" k "\t" f
  base = f; sub(/.*\//, "", base)
  if (base == "index.md" || base == "log.md" || base == "diataxis.md" || (f in link)) next
  n = 0; top = ""; nr = 0
  while ((getline l < f) > 0) {
    n++; gsub(/\r/, "", l)
    if (n == 1) { if (substr(l, 1, 3) == BOM) l = substr(l, 4); if (l != "---") break; continue }
    if (l == "---") break
    if (l ~ /^[ \t]*(- )?resource:[ \t]*[^ \t]/) {
      v = after(l, "resource"); if (top == "" && l ~ /^resource:/) top = v
      r = local(v); if (r == "") continue
      print "E\t" k "\t" f "\t" (r ~ /^\// ? r : ENVIRON["KC_ROOT"] "/" r) "\t" r
    }
    else if (l ~ /^[ \t]*(- )?revision:[ \t]*[^ \t]/) rev[++nr] = unquote(after(l, "revision"))
    else if (l ~ /^[ \t]*(- )?at:[ \t]*[^ \t]/) print "\003" k "\t" pfx rel "\t" f "\t" after(l, "at") > ats
    else {
      m = flowvals(l, "revision", got); for (j = 1; j <= m; j++) rev[++nr] = unquote(got[j])
      m = flowvals(l, "at", got); for (j = 1; j <= m; j++) print "\003" k "\t" pfx rel "\t" f "\t" got[j] > ats
    }
  }
  close(f)
  r = local(top); if (r ~ /^\//) r = ""
  for (j = 1; j <= nr; j++) if (r != "" && rev[j] ~ /^[0-9a-f]+$/ && length(rev[j]) >= 7) print "W\t" k "\t" f "\t" rev[j] "\t" r
}
END { print "Z" }
'
tmp="$(mktemp -d)"
trap 'rm -rf "$tmp"' EXIT
find "$bundle/" -name '*.md' -not -path '*/.obsidian/*' -type l > "$tmp/links"
# The awk below reads files and links only: a folder whose name ends in .md
# is no concept. Its last line is Z. An awk can stop early, as mawk does on
# a file it cannot read, so the script exits 2 when that line is missing.
read_all=0
# Where git names each concept: the bundle's real folder from the top of the
# work tree, then the path inside it.
kpfx=""
if [ -n "$gitroot" ]; then
  top="$(cd "$gitroot" && pwd -P)"
  case "$real" in "$top") ;; "$top"/*) kpfx="${real#"$top"/}/" ;; *) gitroot="" ;; esac
fi
: > "$tmp/ats"
asks=""; askers=""
while IFS=$'\t' read -r kind n f val res; do
  case "$kind" in
    # 8. path shape
    P) hold "$n" 0 "$f: path is not lowercase a-z, 0-9, '.', '_', '-' - case-insensitive hosts and sync conflict copies are why" ;;
    # 5. local resource paths exist: top-level `resource:` and `sources[].resource`
    E) [ -e "$val" ] || hold "$n" 1 "$f: resource not found: $res (looked at $val)" ;;
    # 6. commit-shaped revisions, asked of git in one call below
    W)
      [ -n "$gitroot" ] || continue
      if [ "$shallow" = true ]; then
        hold "$n" 2 "$f: revision $val cannot be checked in a shallow clone - check out with fetch-depth: 0"
      else
        asks="$asks$val:./$res"$'\n'; askers="$askers$n"$'\t'"$f"$'\t'"$val"$'\t'"$res"$'\n'
      fi
      ;;
    Z) read_all=1 ;;
  esac
done < <(find "$bundle/" -name '*.md' -not -path '*/.obsidian/*' \( -type f -o -type l \) | sort \
  | KC_BUNDLE="$bundle" KC_ROOT="$root" KC_PREFIX="$kpfx" KC_LINKS="$tmp/links" KC_ATS="$tmp/ats" LC_ALL=C awk "$fields")
if [ "$read_all" != 1 ]; then
  echo "the bundle could not be read to its end, so rules 5, 6, 8 and 11 were not checked - the error above names the file" >&2
  exit 2
fi
# Rule 6's answers, from one git call: a line for each question, in order,
# that ends in "missing" when the commit or the path in it is not there.
if [ -n "$asks" ]; then
  while IFS=$'\t' read -r n f rev res answer; do
    case "$answer" in *" missing"|*" ambiguous"|"") hold "$n" 2 "$f: revision $rev does not hold $res - no such commit, or the path was absent in it" ;; esac
  done < <(paste <(printf '%s' "$askers") <(printf '%s' "$asks" | git -C "$root" cat-file --batch-check 2>/dev/null || true))
fi
# 11. from one walk through the history of the bundle, oldest first.
if [ -n "$gitroot" ] && [ -s "$tmp/ats" ]; then
  while IFS=$'\t' read -r k finding; do
    hold "$k" 3 "$finding"
  done < <(
    {
      TZ=UTC git -C "$root" -c core.quotePath=false log --reverse --no-color --no-ext-diff --no-renames --unified=0 -p \
        --format='%x01%cd' --date=format-local:'%Y-%m-%dT%H:%M:%SZ' -- "$real" 2>/dev/null | tr -d '\r' || true
      printf '\002%s\n' "$now"
      cat "$tmp/ats"
    } | LC_ALL=C awk "$rule11"
  )
fi
if [ -n "$held" ]; then
  fail=1
  printf '%s' "$held" | sort -t "$(printf '\t')" -k1,1n -k2,2n -k3,3n | cut -f4-
fi

# ---- 2, 3, 4, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18. the Python half ------------
here="$(dirname "$0")"
py="$here/knowledge-conventions.py"
rules="rules 2, 3, 4, 7, 9, 10, 12, 13, 15, 16, 17 and 18"
[ -z "$since" ] || rules="rules 2, 3, 4, 7, 9, 10, 12, 13, 14, 15, 16, 17 and 18"
uvflags=(); uverr=""; uvhint="Run uv sync in .lokf/ to pin them by hash."
uv_ready() {
  local err names name again unpinned lifted=""
  command -v uv >/dev/null 2>&1 || return 1
  uv sync --offline --quiet --script "$1" >/dev/null 2>&1 && return 0
  until err="$(uv sync --color never --script "$1" ${uvflags[@]+"${uvflags[@]}"} 2>&1 >/dev/null)"; do
    names="$(printf '%s\n' "$err" | sed -n 's/^warning: \([^ ]*\) is missing an upload date.*/\1/p' | tr -d '\140' | sed 's/-[0-9].*//' | tr '[:upper:]' '[:lower:]' | tr '_.' '--' | sort -u)"
    again=""; unpinned=""
    for name in $names; do
      case " $lifted " in *" $name "*) again=1 ;; esac
      case "$name" in *[!a-z0-9-]*) unpinned="$unpinned $name"; continue ;; esac
      grep -qiE "^# dependencies = .*\"${name//-/[-_.]}==" "$1" || unpinned="$unpinned $name"
    done
    if [ -z "$names" ] || [ -n "$again$unpinned" ]; then
      uverr="$(printf '%s\n' "$err" | grep -v ' is missing an upload date' || true)"
      [ -z "$unpinned" ] || uverr+=$'\n'"${0##*/}: the package index serves no upload times for$unpinned, which the script's header does not pin with ==, so exclude-newer stays."
      return 1
    fi
    for name in $names; do uvflags+=(--exclude-newer-package "$name=false"); lifted="$lifted $name"; done
  done
  [ -z "$lifted" ] || echo "${0##*/}: the package index serves no upload times, so exclude-newer is lifted for$lifted. The versions stay pinned. $uvhint" >&2
  return 0
}
venv="$root/.lokf/.venv/bin/python"; [ -e "$venv" ] || venv="$root/.lokf/.venv/Scripts/python.exe"
runner=""
skipped=""; unrun=0
if [ -x "$venv" ] && "$venv" -c 'import sys; assert sys.version_info >= (3, 11); import yaml' >/dev/null 2>&1; then
  runner="$venv"
elif uv_ready "$py"; then
  runner=uv
elif command -v uv >/dev/null 2>&1; then
  unrun=1
  [ -z "$uverr" ] || printf '%s\n' "$uverr" >&2
  echo "$rules not checked: uv could not run $py, because it could not install its packages. Run uv sync in .lokf/ and this script uses that .venv." >&2
fi
if [ -n "$runner" ]; then
  rc=0
  if [ "$runner" = uv ]; then
    out="$(uv run --quiet ${uvflags[@]+"${uvflags[@]}"} "$py" "$bundle" ${since:+--since "$since"} 2>&1)" || rc=$?
  else
    out="$("$runner" "$py" "$bundle" ${since:+--since "$since"} 2>&1)" || rc=$?
  fi
  # The Python half exits 1 for findings. Any other failure is the runner's,
  # or a usage error, and says nothing about the bundle.
  case "$rc" in
    0) ;;
    1) printf '%s\n' "$out"; fail=1 ;;
    *) unrun=1
       printf '%s\n' "$out" >&2
       hint=""
       [ "$runner" = uv ] && hint=" Behind a package mirror, run uv sync in .lokf/ and this script uses that .venv."
       echo "$rules not checked: $runner could not run $py (exit $rc).$hint" >&2 ;;
  esac
elif [ "$unrun" -eq 0 ]; then
  skipped="$rules not checked: uv not found"
  echo "$skipped - install uv, or run $py directly with python3 3.11 or later and pyyaml" >&2
  # Under --strict a rule not checked is no pass.
  if [ "$strict" = 1 ]; then unrun=1; skipped=""; fi
fi

if [ "$fail" -eq 0 ] && [ "$unrun" -eq 0 ]; then
  echo "OK - $bundle keeps the conventions lokf validate cannot check${skipped:+ ($skipped)}"
fi
[ "$fail" -eq 0 ] && [ "$unrun" -eq 1 ] && exit 2
exit "$fail"
