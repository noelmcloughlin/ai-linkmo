#!/usr/bin/env bash
# Record one reader-feedback entry in .lokf/feedback.md without reading it.
#
# ktl-docent records a Miss or a Disagreement with this script, and
# ktl-librarian consumes them. The entries of other readers are free text
# from people who may have no access to this repository. The caller passes
# its own entry and never opens the file, so none of that text reaches the
# model (docs/threat-model.md, "Prompt-injection guards"). It prints one
# line, with the kind, the date and how many entries now wait, and never the
# text of an entry.
#
# Bash 3.2 and POSIX tools only, so it runs on macOS's stock bash and on Git
# for Windows.
#
# Usage:
#   knowledge-feedback.sh [--root <dir>] [--for <login>] [--concept <path>] <kind> <text>
#
#   kind    Miss or Disagreement, in any letter case, and nothing else.
#   text    the entry itself, one argument, written as one line. Text that
#           holds ` - docent` is refused.
#   --for   an authenticated login (gh api user --jq .login, or glab), which
#           records the entry as `- docent, for human:<login>`. Left out, the
#           entry is `- docent` alone. It is never a name typed in
#           conversation and never git config user.name: the attribution is
#           worth carrying only when the forge stands behind it.
#   --root  the repository root (default: the nearest ancestor of the current
#           directory holding .lokf/, else the current directory).
#   --concept  with a Disagreement only, the bundle path of the concept the
#           reader disputes, such as services/orders-api.md. It must name a
#           concept file under .lokf/knowledge, in the bundle's lowercase
#           spelling. The entry then reads `- **Disagreement** (on `<path>`) -`,
#           and knowledge-report.sh labels that concept as disputed until the
#           librarian handles the entry. The report reads the path and never
#           the text.
#
# The day heading is the date today in UTC.
#
# Exit:
#   0  recorded;
#   2  the call was wrong, and nothing was written;
#   1  the file could not be written (a read-only .lokf/, most often, another
#      run holding it, or a symbolic link where the script writes), and the
#      caller should tell the reader the gap out loud instead.
[ -n "${BASH_VERSION:-}" ] || { echo "run this with bash: bash ${0##*/} [--root <dir>] [--for <login>] <kind> <text>" >&2; exit 2; }
set -u
# A-Z, a-z and 0-9 in a case glob mean the ASCII letters and digits, not
# whatever a locale collates between them, so a login check below cannot be
# widened by the host's locale. A no-op where the option is unknown (bash 3.2).
shopt -s globasciiranges 2>/dev/null || :

usage() {
  echo "usage: ${0##*/} [--root <dir>] [--for <login>] [--concept <path>] <Miss|Disagreement> <text>" >&2
  exit 2
}

root=""; asker=""; concept=""
while [ $# -gt 0 ]; do
  case "$1" in
    --root) [ $# -ge 2 ] || usage; root="$2"; shift 2 ;;
    --for)  [ $# -ge 2 ] || usage; asker="$2"; shift 2 ;;
    --concept) [ $# -ge 2 ] || usage; concept="$2"; shift 2 ;;
    -h|--help) usage ;;
    --) shift; break ;;
    -*) echo "unknown option: $1" >&2; usage ;;
    *) break ;;
  esac
done
[ $# -eq 2 ] || usage
kind="$1"; text="$2"

# ---- what the librarian can consume ----------------------------------------
# A third kind would reach the librarian as an entry it has no rule for.
case "$kind" in
  [Mm][Ii][Ss][Ss]) kind=Miss ;;
  [Dd][Ii][Ss][Aa][Gg][Rr][Ee][Ee][Mm][Ee][Nn][Tt]) kind=Disagreement ;;
  *) echo "kind must be Miss or Disagreement, not '$kind'" >&2; exit 2 ;;
esac

# The attribution is the one field a later reader may take as evidence that a
# named person asked, so it holds only the characters of a login, in the
# shape that both provenance gates accept.
if [ -n "$asker" ]; then
  case "$asker" in
    *[!A-Za-z0-9._-]*|[!A-Za-z0-9]*)
      echo "--for takes a forge login (a letter or digit, then letters, digits, '.', '_' or '-'), not '$asker'" >&2; exit 2 ;;
  esac
fi

# The concept is the one field a program reads back, so it holds only the
# path spelling of the bundle (conventions rule 8), with no `..`.
if [ -n "$concept" ]; then
  [ "$kind" = Disagreement ] || { echo "--concept goes with a Disagreement only; a Miss names a gap, not a concept the bundle holds" >&2; exit 2; }
  case "$concept" in
    *[!a-z0-9._/-]*|[!a-z0-9]*|*..*|*/|*//*|*/./*)
      echo "--concept takes a concept's path in the bundle, in lowercase with no '..' or '.' segment, such as services/orders-api.md, not '$concept'" >&2; exit 2 ;;
  esac
  case "$concept" in *.md) ;; *) echo "--concept takes the concept's file, ending in .md, not '$concept'" >&2; exit 2 ;; esac
  [ "$concept" != diataxis.md ] || { echo "--concept takes a concept, not the bundle's $concept" >&2; exit 2; }
  case "${concept##*/}" in index.md|log.md) echo "--concept takes a concept, not the bundle's $concept" >&2; exit 2 ;; esac
fi

# One entry is one line. Collapse every whitespace run, drop control
# characters, and trim: a caller that passes a paragraph still cannot break
# the file's shape or forge a second entry with an embedded newline.
text="$(printf '%s' "$text" | tr -d '\000-\010\013\014\016-\037\177' | tr '\t\n\r' '   ' | sed -e 's/  */ /g' -e 's/^ //' -e 's/ $//')"
[ -n "$text" ] || { echo "the entry text is empty" >&2; exit 2; }
# The entry ends in its attribution, so text that holds ` - docent`, in any
# letter case, could pass for an attribution, such as one for a login nobody
# authenticated.
case "$(printf ' - %s' "$text" | tr '[:upper:]' '[:lower:]')" in
  *" - docent"*) echo "the entry text holds ' - docent', which reads as the attribution the script adds - word the entry another way" >&2; exit 2 ;;
esac

# ---- root ------------------------------------------------------------------
if [ -z "$root" ]; then
  d="$(pwd -P)"; root="$d"
  while [ "$d" != "/" ]; do
    if [ -d "$d/.lokf" ]; then root="$d"; break; fi
    d="$(dirname "$d")"
  done
fi
root="$(cd "$root" 2>/dev/null && pwd -P)" || { echo "no such directory: $root" >&2; exit 2; }
# Feedback is a report against a bundle. With no bundle there is nothing for
# the librarian to fix, and ktl-docent is told to say so instead of writing.
[ -d "$root/.lokf/knowledge" ] || { echo "no .lokf/knowledge under $root - no bundle to record a gap against; say the gap out loud, and that ktl-sidecar can create one" >&2; exit 2; }
if [ -n "$concept" ] && [ ! -f "$root/.lokf/knowledge/$concept" ]; then
  echo "--concept names no concept in this bundle: $concept - record the Disagreement without it" >&2; exit 2
fi

dir="$root/.lokf"
file="$dir/feedback.md"
tmp=""
lock="$file.lock"
today="$(date -u +%Y-%m-%d)"
entry="- **$kind**${concept:+ (on \`$concept\`)} - $text - docent${asker:+, for human:$asker}"

# ---- the file --------------------------------------------------------------
readonly_bundle() {
  echo "cannot write $file - if .lokf/ is read-only, say the gap out loud to the reader instead" >&2
  exit 1
}
# Refuse a symbolic link at the folder, the file or the lock, which a
# repository can commit: a write through one changes another file, and a
# read copies it into feedback.md.
for place in "$dir" "$file" "$lock"; do
  if [ -L "$place" ]; then
    echo "$place is a symbolic link, which this script neither reads nor writes through - say the gap out loud to the reader instead" >&2
    exit 1
  fi
done
if [ -e "$file" ] && [ ! -f "$file" ]; then
  echo "$file is not a regular file - say the gap out loud to the reader instead" >&2
  exit 1
fi
# The rewrite below writes a temporary file beside this one, so the directory
# has to be writable even when the file itself already is.
[ -w "$dir" ] || readonly_bundle

# Two runs at once would each read the file, and the second mv would drop the
# first entry. A directory is the one lock that every platform here creates
# atomically. A run killed before it cleans up leaves the lock behind, and
# the message says what to remove. When mkdir fails and no lock is there, the
# mount is read-only.
tries=0
until mkdir "$lock" 2>/dev/null; do
  [ -d "$lock" ] || readonly_bundle
  tries=$((tries + 1))
  if [ "$tries" -ge 5 ]; then
    echo "another run holds $lock - if nothing else is recording feedback, remove that directory and try again" >&2
    exit 1
  fi
  sleep 1
done
trap 'rmdir "$lock" 2>/dev/null; [ -z "$tmp" ] || rm -f "$tmp"' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

# mktemp picks a name a committed link cannot already hold, unlike $$.
# Its file is owner-only, so chmod gives it the mode a new file takes here.
tmp="$(mktemp "$dir/feedback.md.XXXXXX" 2>/dev/null)" || { tmp=""; readonly_bundle; }
chmod "$(printf '%o' $((0666 & ~$(umask))))" "$tmp" 2>/dev/null || :

# feedback.md is not knowledge and has no frontmatter; it appears the first
# time a reader's agent records a gap, which may be this call.
if [ ! -s "$file" ]; then
  {
    echo "# Reader feedback for the librarian"
    echo ""
    echo "Written by ktl-docent; consumed and cleared by ktl-librarian on its next run. Newest first. One line per entry."
  } > "$file" 2>/dev/null || readonly_bundle
fi
[ -w "$file" ] || readonly_bundle

# The entry is passed in the environment rather than through -v, which would
# read a backslash in the text as an escape.
KF_ENTRY="$entry" awk -v hdr="## $today" '
  BEGIN { entry = ENVIRON["KF_ENTRY"]; done = 0; skipblank = 0; last = "" }
  # Headings are days, newest first, and ISO dates order as strings. The
  # entry goes first under the heading for today, or under a new one above
  # the first older heading. A heading after today stays where it is.
  /^## / && done == 0 {
    h = $0; sub(/[ \t\r]+$/, "", h)
    if (h == hdr) { print hdr; print ""; print entry; skipblank = 1; done = 1; next }
    if (h < hdr) { print hdr; print ""; print entry; print ""; print; last = $0; done = 1; next }
  }
  # Skip the blank line that followed that heading: we printed our own.
  skipblank == 1 { skipblank = 0; if ($0 ~ /^[ \t\r]*$/) next }
  { print; last = $0 }
  # No heading today could go above: a file that has only ever held its
  # intro, or whose every day is after today.
  END { if (done == 0) { if (last != "" && last != "\r") print ""; print hdr; print ""; print entry } }
' "$file" > "$tmp" || { echo "could not record the entry in $file" >&2; exit 1; }
mv "$tmp" "$file" || { echo "could not record the entry in $file" >&2; exit 1; }

# The same expression ktl-curator counts with, so the two never disagree about
# how many entries are waiting. It reads no entry's text, and neither does the
# caller from this line.
waiting="$(grep -c '^- \*\*' "$file" 2>/dev/null || true)"
printf 'recorded: %s under %s in .lokf/feedback.md (%s waiting for the librarian)\n' "$kind" "$today" "${waiting:-1}"
