#!/usr/bin/env bash
# Conventions of a LOKF bundle that `lokf validate` cannot see.
#
# The toolkit checks frontmatter against the schema and reads a concept body
# as an opaque string; it never reads log.md. The four skills and both
# Obsidian plugins rely on a few conventions beyond that, and each has been
# broken at least once by an agent that had been told the rule in prose:
#
#   1. log.md has one `## YYYY-MM-DD` heading per day - the bare ISO date,
#      newest first, no duplicates. OKF §9 makes the date form a MUST, and the
#      LOKF Curator plugin finds today's section by that exact heading.
#   2. Every `at:` is a quoted string. Unquoted, YAML hands the toolkit a
#      datetime object and the curator's string comparison a surprise.
#   3. `verified` is a list, never a bare `{ by, at }` mapping, and carries at
#      most one `process:lokf-librarian` event - the librarian replaces its
#      own, it does not stack them.
#   4. A bullet under `## Open questions` is `- YYYY-MM-DD, <actor>: ...`, the
#      shape the curator and both plugins write and read; the curator quotes
#      the first bullet, so a trailing signature would become the question.
#   5. Every `resource:` that is not a URL names a file or directory that
#      exists, relative to the repository root (the nearest directory holding
#      `.lokf/`; failing that, the bundle's parent). A source that has gone
#      should fail the gate now, not wait for the librarian's next refresh.
#      URLs are never fetched.
#   6. A commit-shaped `revision` on a `generated` or `verified` event (a
#      field proposed for lokf 0.9.0; the released 0.8.0 validator rejects it,
#      so the skills write it only where `lokf validate` accepts it) names a
#      commit in this repository that holds the concept's local `resource`.
#      ETags, digests and version labels pin URLs and are not checked. Needs
#      the full history: a shallow clone is reported.
#   7. One file per `id`. A sync client's conflict copy (OneDrive, Dropbox,
#      Drive, iCloud) or a pasted duplicate carries the same `id`, passes
#      `lokf validate`, and silently merges into the original in the graph.
#   8. Every path in the bundle is lowercase: a-z, 0-9, `.`, `_`, `-`. Two
#      paths that differ only by case collide on Windows, macOS and SharePoint,
#      and a space, a parenthesis or an upper-case host name in a file name is
#      how every sync client names a conflict copy.
#   9. Every concept starts with a `---` frontmatter block that closes, with no
#      byte order mark in front of it. A BOM from a web editor or Notepad, or a
#      file with no block at all, would otherwise pass this script unread.
#  10. The fields the provenance gates read line by line - `id`, and `by`,
#      `at` and `revision` on an event - are spelt so a line reader and a
#      parser see the same thing: no tags, anchors, aliases, quoted keys,
#      block scalars or values spanning lines. Each of those is valid YAML
#      that `lokf validate` accepts and both gates cannot see, which is a
#      confirmation nobody has to stand behind.
#
# Rules 2, 3, 8 and 10 are house rules, stricter than the format: OKF permits
# an unquoted datetime, a bare `verified` mapping (which every reader here -
# the toolkit, both plugins, the gates - does read as a one-item list, as it
# MUST), any file name and any YAML. This bundle holds itself to more so that
# an event is always appended to a list and never converted first, a datetime
# reaches every consumer as the same string, a name never collides on a
# case-insensitive host, and an event reads the same to a line reader as to
# a parser. A bundle written to the letter of OKF may fail them; that is a
# policy of the gate, not a defect in the bundle.
#
# Rules 2, 3, 7, 9 and 10 are questions about a document's YAML that a real
# parse answers outright, and rule 4 rides along, so this script hands them
# to knowledge-conventions.py (same directory) through `uv run`, which needs
# nothing preinstalled. Rules 1, 5, 6 and 8 stay here: they are git and
# filesystem facts, and this half keeps running - grep and awk only -
# wherever bash and git do, with no toolchain at all. Without uv, this half
# still runs and says so.
#
# Files are read with carriage returns removed and a leading byte order mark
# stripped, so a Windows checkout (`core.autocrlf`) reads the same as CI. The
# sidecar's `.lokf/.gitattributes` keeps tracked files on LF; rule 9 still
# reports a BOM, because other readers do not strip it.
#
# Usage: knowledge-conventions.sh [bundle-dir]   (default: knowledge, i.e. run
# from .lokf/). Exit 1 with one line per finding; nothing else is written.
[ -n "${BASH_VERSION:-}" ] || { echo "run this with bash: bash ${0##*/} [bundle-dir]" >&2; exit 2; }
set -euo pipefail

# The bundle directory may be a link (a host that keeps the real folder as a
# visible knowledge_bundle/), and find never enters a link it is handed bare:
# the trailing slash below is what makes it read the files at all.
bundle="${1:-knowledge}"; bundle="${bundle%/}"
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

# ---- 2-9. concept files -----------------------------------------------------
# Repository root for rule 5: the nearest ancestor holding `.lokf/`, else the
# bundle's parent (a bare bundle handed to this script on its own).
real="$(cd "$bundle" && pwd -P)"
root="$(dirname "$real")"
d="$real"
while [ "$d" != "/" ]; do
  if [ -d "$d/.lokf" ]; then root="$d"; break; fi
  d="$(dirname "$d")"
done
# Rule 6 needs git: whether the root is in a work tree, and whether that tree
# has its full history. Outside git the rule is skipped; a shallow clone is
# reported, because a pin the script cannot resolve is not a pin it has checked.
gitroot="$(git -C "$root" rev-parse --show-toplevel 2>/dev/null || true)"
shallow="$(git -C "$root" rev-parse --is-shallow-repository 2>/dev/null || echo false)"
while IFS= read -r f; do
  # 8. path shape, checked on every Markdown file, reserved ones included
  rel="${f#"$bundle"/}"
  if ! printf '%s\n' "$rel" | grep -qE '^([a-z0-9][a-z0-9._-]*/)*[a-z0-9][a-z0-9._-]*$'; then
    say "$f: path is not lowercase a-z, 0-9, '.', '_', '-' - case-insensitive hosts and sync conflict copies are why"
  fi
  case "$(basename "$f")" in index.md|log.md|diataxis.md) continue ;; esac
  # Frontmatter only, best effort, for 5 and 6: the text between the first two
  # `---` lines. A missing or malformed block yields nothing here and is
  # rules 2-4, 7 and 9's job below to report, not this loop's. The awk reads
  # the whole file rather than exiting at the second `---`: a CI runner that
  # ignores SIGPIPE (GitHub Actions does) turns an early-closed pipe into a
  # `tr: write error` that pipefail then makes fatal.
  fm="$(clean "$f" | awk 'NR==1 {if ($0!="---") stop=1; next} stop {next} $0=="---" {stop=1; next} {print}')"
  # 5. local resource paths exist: top-level `resource:` and `sources[].resource`
  while IFS= read -r res; do
    [ -z "$res" ] && continue
    case "$res" in *://*) continue ;; esac
    res="${res%%#*}"
    res="${res#\"}"; res="${res%\"}"; res="${res#\'}"; res="${res%\'}"
    res="${res%"${res##*[![:space:]]}"}"
    [ -z "$res" ] && continue
    case "$res" in /*) target="$res" ;; *) target="$root/$res" ;; esac
    [ -e "$target" ] || say "$f: resource not found: $res (looked at $target)"
  done < <(printf '%s\n' "$fm" | sed -nE 's/^[[:space:]]*(- )?resource:[[:space:]]*(.*[^[:space:]])[[:space:]]*$/\2/p')
  # 6. a commit-shaped `revision` names a commit that holds the concept's own
  #    local `resource`. Anything with a character outside [0-9a-f] - an ETag,
  #    a `sha256:` digest, a version label - pins a URL and is skipped, as is
  #    every revision on a concept whose `resource` is a URL, absolute or absent.
  res="$(printf '%s\n' "$fm" | sed -nE 's/^resource:[[:space:]]*(.*[^[:space:]])[[:space:]]*$/\1/p' | sed -n 1p)"
  res="${res%%#*}"
  res="${res#\"}"; res="${res%\"}"; res="${res#\'}"; res="${res%\'}"
  res="${res%"${res##*[![:space:]]}"}"
  case "$res" in ""|*://*|/*) res="" ;; esac
  while IFS= read -r rev; do
    rev="${rev#\"}"; rev="${rev%\"}"; rev="${rev#\'}"; rev="${rev%\'}"
    case "$rev" in ""|*[!0-9a-f]*) continue ;; esac
    if [ "${#rev}" -lt 7 ] || [ -z "$res" ] || [ -z "$gitroot" ]; then continue; fi
    if [ "$shallow" = true ]; then
      say "$f: revision $rev cannot be checked in a shallow clone - check out with fetch-depth: 0"
    elif ! git -C "$root" cat-file -e "$rev:./$res" 2>/dev/null; then
      say "$f: revision $rev does not hold $res - no such commit, or the path was absent in it"
    fi
  done < <(printf '%s\n' "$fm" | sed -nE 's/^[[:space:]]*(- )?revision:[[:space:]]*(.*[^[:space:]])[[:space:]]*$/\2/p')
done < <(find "$bundle/" -name '*.md' -not -path '*/.obsidian/*' | sort)

# ---- 2, 3, 4, 7, 9, 10. the parser's half ------------------------------------
py="$(dirname "$0")/knowledge-conventions.py"
skipped=""
if command -v uv >/dev/null 2>&1; then
  if ! out="$(uv run --quiet "$py" "$bundle" 2>&1)"; then
    printf '%s\n' "$out"
    fail=1
  fi
else
  skipped="rules 2, 3, 4, 7, 9 and 10 not checked: uv not found"
  echo "$skipped - install uv, or run $py directly with python3 and pyyaml" >&2
fi

if [ "$fail" -eq 0 ]; then
  echo "OK - $bundle keeps the conventions lokf validate cannot check${skipped:+ ($skipped)}"
fi
exit "$fail"
