#!/usr/bin/env bash
# The signature half of the registrar's provenance gate, with no forge.
# It runs off GitHub, and as a second opinion to the GitHub `provenance` job.
#
# The repository carries one public key per curator id under
# `.lokf/curators/`: `<id>.asc` as `gpg --armor --export` writes it, or
# `<id>.pub` as `ssh-keygen` writes it, one key per line. Every commit in a
# range that adds, changes or removes a `human:<id>` event under the bundle,
# in `verified` or `generated`, must be signed by a key on file for exactly
# that id. A GPG key counts with every subkey it carries, since most keys
# sign with a subkey. An SSH signature is checked with `ssh-keygen -Y verify`,
# which needs OpenSSH 8.2 or later.
#
# A removal needs the same signature. That covers a `verified` event that
# every parent held, struck out or gone with its concept. It covers a
# `generated` record by a person too, unless a record by another person
# replaces it, as Correct in ktl-curator does.
#
# `--unattended` checks a change that nobody stands behind, such as a run of
# the scheduled librarian, against HEAD, with no key and no forge. It reports
# every way the working tree, staged or not, touches the record of a person:
#   - a `human:` event added, changed or removed in a layout it reads;
#   - frontmatter it cannot read, which may hold one, added, changed or removed;
#   - a symbolic link left under the bundle;
#   - a person's note under `## Open questions` added or removed;
#   - text a person wrote, changed.
# knowledge-apply.sh refuses each of these before it writes, and this script
# checks the result in a job the agent never ran in.
#
# Findings, one line each, exit 1:
#   - the commit is unsigned, or its signature does not verify;
#   - it is signed by another key, or by an expired or revoked one;
#   - the id has no key on file, or is not a login any forge could list;
#   - the range adds, changes or removes the key file of that id *and*
#     records a confirmation by them, so nobody registers a key and vouches
#     with it in one step;
#   - a commit touches a bundle path that git quotes, changes frontmatter
#     this reader cannot follow, or leaves a symbolic link under the bundle:
#     each can hide an event.
# With no `.lokf/curators/` directory it says so and exits 0.
#
# A pass proves only that the holder of that key made that commit: not that
# anyone read the source, nor who the person is beyond what the reviewed
# history of the key file says. It needs Bash 3.2 or later, POSIX tools, git,
# and gpg or ssh-keygen for the kind of key on file.
#
# Usage: knowledge-provenance.sh <base-ref> [head-ref] [bundle-dir]
#        knowledge-provenance.sh --unattended [bundle-dir]
#   For example:
#        knowledge-provenance.sh origin/main            (a branch, locally)
#        knowledge-provenance.sh "$BASE_SHA" "$HEAD_SHA"  (in CI)
#        knowledge-provenance.sh --unattended            (what the librarian workflow runs)
#   Run it from the sidecar folder, the one that holds .lokf/, or run the
#   copy in its .lokf/scripts/ from anywhere in the repository. A bundle-dir
#   is read from the sidecar folder.
[ -n "${BASH_VERSION:-}" ] || { echo "run this with bash: bash ${0##*/} <base-ref> [head-ref] | --unattended" >&2; exit 2; }
set -u
# Read A-Z, a-z and 0-9 in a case glob as ASCII, so no locale can widen the
# login check. Bash 3.2 lacks the option and skips it.
shopt -s globasciiranges 2>/dev/null || :
# Make awk, sort and comm read bytes, in any locale. The frontmatter reader
# strips a byte order mark by its three bytes, which a UTF-8 gawk would read
# as one character, and `comm` needs the byte order that `sort` writes.
export LC_ALL=C

unattended=0
if [ "${1:-}" = "--unattended" ]; then
  unattended=1; base=HEAD; head=""; bundle="${2:-.lokf/knowledge}"
else
  base="${1:-}"; head="${2:-HEAD}"; bundle="${3:-.lokf/knowledge}"
fi
[ -n "$base" ] || { echo "usage: knowledge-provenance.sh <base-ref> [head-ref] [bundle-dir] | --unattended [bundle-dir]" >&2; exit 2; }
command -v git >/dev/null 2>&1 || { echo "git is required" >&2; exit 2; }
# Every finding below comes out of one of these. With one missing the script
# would find nothing, and a gate that could not look must not say OK.
for tool in awk comm sort cut sed grep mktemp; do
  command -v "$tool" >/dev/null 2>&1 || { echo "$tool is required, and this gate passes nothing it could not check" >&2; exit 2; }
done
root="$(git rev-parse --show-toplevel 2>/dev/null)" || { echo "not inside a git work tree" >&2; exit 2; }
root="$(cd "$root" && pwd -P)" || exit 2
# The sidecar folder is the nearest one that holds .lokf/, from the working
# directory up to the top of the work tree. Failing that, it is the folder
# that holds this script as .lokf/scripts/, so a workflow may run it from the
# top. Git names each path from the top, so each path below carries the
# sidecar folder as a prefix.
side=""
d="$(pwd -P)"
while :; do
  if [ -d "$d/.lokf" ]; then side="$d"; break; fi
  if [ "$d" = "$root" ] || [ "$d" = / ]; then break; fi
  d="$(dirname "$d")"
done
if [ -z "$side" ]; then
  here="$(cd "$(dirname "${BASH_SOURCE[0]}")" 2>/dev/null && pwd -P)"
  case "$here" in
    "$root"/.lokf/scripts|"$root"/*/.lokf/scripts) side="${here%/.lokf/scripts}" ;;
  esac
fi
[ -n "$side" ] || side="$root"
prefix="${side#"$root"}"; prefix="${prefix#/}"
[ -z "$prefix" ] || prefix="$prefix/"
cd "$root" || exit 2
inner="$bundle"   # the bundle as the sidecar's folder names it
bundle="$prefix$bundle"
doorway="${prefix}knowledge_bundle"
curators="${prefix}.lokf/curators"
# The first folder of the bundle's path, which is asked about as a link.
top_dir="$prefix${inner%%/*}"
# A gate that could not find the bundle says so: "skipped" or "OK" there
# would pass whatever changed.
if [ ! -d "$bundle" ] && [ -z "$(git ls-tree "$base" -- "$bundle" 2>/dev/null)" ]; then
  echo "no bundle at $bundle in $root, so this gate has nothing it can read; run it from the sidecar's folder, the one that holds .lokf/" >&2
  exit 2
fi
if [ "$unattended" -eq 0 ]; then
  # In a shallow clone the oldest commit fetched has no parent on disk, so
  # everything it holds would read as its own change.
  if [ "$(git rev-parse --is-shallow-repository 2>/dev/null || echo false)" = true ]; then
    echo "this clone is shallow, so the commits of $base..$head cannot each be compared with a parent; fetch the full history (git fetch --unshallow)" >&2
    exit 2
  fi
  # The keys are read from the files on disk. As a link, the folder could
  # name keys the same change brings in under another path.
  if [ -L "$curators" ]; then
    echo "$curators is a symbolic link, so the keys in it are not this repository's own files - keep it a folder of key files"
    exit 1
  fi
fi
# A range that deletes the folder has not opted out: its confirmations then
# name someone with no key on file. Only a base that never held it has.
if [ "$unattended" -eq 0 ] && [ ! -d "$curators" ] && [ -z "$(git ls-tree "$base" -- "$curators" 2>/dev/null)" ]; then
  echo "skipped - no $curators/ directory; nothing to verify confirmations against (the forge's gate, if any, is the only check)"
  exit 0
fi

fail=0
say() { echo "$1"; fail=1; }
have() { command -v "$1" >/dev/null 2>&1; }

# Throwaway keyring for the GPG keys on file, and a scratch directory for the
# SSH payloads and signatures, both gone on exit.
home="$(mktemp -d)"
trap 'rm -rf "$home"' EXIT
chmod 700 "$home"
gpg_ok=0
if [ "$unattended" -eq 0 ] && have gpg; then
  gpg_ok=1
  for k in "$curators"/*.asc; do
    [ -f "$k" ] || continue
    GNUPGHOME="$home" gpg --batch --quiet --import "$k" 2>/dev/null || say "$k: not an importable armored public key"
  done
fi
gpg_fprs() {  # id -> every fingerprint in .lokf/curators/<id>.asc, primary and subkeys, one per line
  GNUPGHOME="$home" gpg --batch --quiet --with-colons --import-options show-only --import "$curators/$1.asc" 2>/dev/null \
    | awk -F: '$1=="fpr" {print $10}'
}
# ssh-keygen verifies a detached signature against an allowed-signers file
# naming the principal, so each id's .pub becomes `<id> namespaces="git" <key>`.
allowed_of() {  # id -> path of an allowed-signers file listing that id's keys
  awk -v id="$1" '$1 ~ /^(ssh-|ecdsa-|sk-)/ {print id " namespaces=\"git\" " $0}' "$curators/$1.pub" > "$home/$1.allowed"
  echo "$home/$1.allowed"
}
# A commit's signed payload is the object with its `gpgsig` header and that
# header's continuation lines removed; the signature is those lines unindented.
payload_of() {
  git cat-file commit "$1" | awk '
    BEGIN {hdr = 1}
    hdr && $0 == "" {hdr = 0}
    hdr && /^gpgsig(-sha256)? / {skip = 1; next}
    hdr && skip && /^ / {next}
    {skip = 0; print}'
}
signature_of() {
  git cat-file commit "$1" | awk '
    !done && /^gpgsig(-sha256)? / {insig = 1; sub(/^gpgsig(-sha256)? /, ""); print; next}
    insig && /^ / {sub(/^ /, ""); print; next}
    insig {insig = 0; done = 1}'
}
sig_format() {  # commit -> pgp | ssh | none
  case "$(git cat-file commit "$1" | grep -m1 -E '^gpgsig(-sha256)? ' || true)" in
    *"BEGIN PGP SIGNATURE"*) echo pgp ;;
    *"BEGIN SSH SIGNATURE"*) echo ssh ;;
    *) echo none ;;
  esac
}

# The human events of a concept, one per line, as
# `<id or path>\t<by>\t<at>\t<revision>\t<verified|generated>`. It reads the
# frontmatter only, so an example in a body code fence is no claim. It reads
# a block list in any key order, a flow-style item, a flow sequence and a
# bare mapping, and gives whatever else it meets the actor (unreadable). An
# event is keyed by the `id` of its concept, and events_in adds its place.
human_events() {  # path -> events, reading the concept on stdin
  awk -v path="$1" '
  # Returns the value after the key, less one pair of enclosing quotes, and sets
  # `strange` on an unclosed or inner quote, a `\` escape, a trailing comment or
  # a leading indicator, which a parser reads another way.
  function val(s,  q, n) { sub(/^[^:]*:[[:space:]]*/, "", s); sub(/[[:space:]]+$/, "", s); q = substr(s, 1, 1); n = length(s)
    if (q == "\"" || q == "'"'"'") { if (n < 2 || substr(s, n) != q) { strange = 1; return s }
      s = substr(s, 2, n - 2); if (index(s, q) || (q == "\"" && index(s, "\\"))) strange = 1; return s }
    if (s ~ /[[:space:]]#/ || s ~ /^[!&*|>@`%#]/) strange = 1
    return s }
  # The schema gives an event only `by`, `at` and `revision`, so another key
  # (a quoted `by`, a merge, an alias) is a spelling this reader cannot
  # follow. Such an event, and one with an actor the schema does not allow,
  # gets the actor (unreadable), which is no login, so each gate refuses it.
  function kv(l,  k) { k = l; sub(/:.*/, "", k); sub(/^[[:space:]]+/, "", k); strange = 0
    if (k == "by") by = val(l); else if (k == "at") at = val(l); else if (k == "revision") rev = val(l); else odd = 1
    if (strange) odd = 1 }
  function actor(a) { return a !~ /\\/ && (a ~ /^(human|process):[^[:space:]]+$/ || a ~ "^[^[:space:]/]+/[^[:space:]/]+$") }
  # Any edit a parser could read must change the output, so an unreadable
  # file gives one line that holds everything up to the closing delimiter,
  # with control bytes YAML forbids in place of its tabs and line ends.
  function unread() { bad = 1 }
  function emit() { if (inev && (odd || !actor(by))) { bad = 1; by = "" }
    if (inev && by ~ /^human:/) { sub(/^human:/, "", by); out = out (cid ? cid : path) "\t" by "\t" at "\t" rev "\t" kind "\n" }
    inev = 0; odd = 0; by = ""; at = ""; rev = "" }
  function flow(s,  n, parts, i) { emit(); inev = 1; gsub(/[{}]/, "", s); n = split(s, parts, ",")
    for (i = 1; i <= n; i++) if (parts[i] !~ /^[[:space:]]*$/) kv(parts[i]); emit() }
  # A flow `verified` or `generated` may span lines, so collect it up to its
  # closing bracket, or a forged confirmation would pass. The block is
  # unreadable when a quoted value holds a bracket or a quote, which would
  # end the form early here and not for a parser, or when text that no rule
  # reads follows the closing bracket.
  function flushflow(  b, n, items, i, q, tail) { b = flowbuf
    if (b ~ /(^|[[:space:]])#/) unread()
    q = b; gsub(/"[^"]*"/, "", q); gsub(/'"'"'[^'"'"']*'"'"'/, "", q)
    if (q ~ /["'"'"']/) unread()
    tail = b; while (match(tail, /"[^"]*"|'"'"'[^'"'"']*'"'"'/)) { if (substr(tail, RSTART, RLENGTH) ~ /[][{}]/) unread(); tail = substr(tail, RSTART + RLENGTH) }
    tail = q; if (flowseq) sub(/^[^]]*\]/, "", tail); else sub(/^[^}]*\}/, "", tail)
    if (tail !~ /^[[:space:]]*$/) unread()
    if (flowseq) { sub(/^\[/, "", b); sub(/\].*/, "", b) } else { sub(/^\{/, "", b); sub(/\}.*/, "", b) }
    sub(/^[[:space:]]+/, "", b); sub(/[[:space:]]+$/, "", b)
    if (b != "") { if (flowseq) { n = split(b, items, /\}[[:space:]]*,/); for (i = 1; i <= n; i++) if (items[i] !~ /^[[:space:]]*$/) flow(items[i]) } else flow(b) }
    inflow = 0; flowbuf = "" }
  BEGIN { fm = 0; inv = 0; inev = 0; inflow = 0; cid = ""; out = ""; odd = 0; bad = 0; plain = 0; dashes = 0; seen = 0 }
  { sub(/\r$/, ""); line = $0; gsub(/\t/, "\002", line); raw[NR] = line }
  # Strip a byte order mark and the CR of a CRLF, as every YAML parser does,
  # or this reader would see no "---" and pass an unsigned event.
  NR == 1 { sub(/^\357\273\277/, ""); if ($0 == "---") { fm = 1; next } else plain = 1 }
  # The toolkit opens a block at the first `---` on any line, so a file that
  # opens any other way may hold events this reader never sees. log.md holds
  # none.
  plain { dashes += gsub(/---/, "&"); next }
  # A parser ends a line at a bare carriage return, U+0085, U+2028 and U+2029,
  # and this reader does not, so an event can sit inside one line it reads.
  /\r|\302\205|\342\200[\250\251]/ { unread() }
  inflow && $0 == "---" { flushflow(); exit }
  inflow { flowbuf = flowbuf " " $0; if (index($0, flowseq ? "]" : "}")) flushflow(); next }
  fm && $0 == "---" { emit(); exit }
  # A block indented whole, and a top-level key no plain `key:` spells, such as
  # a quoted key, `? key`, `<<:` or a flow mapping, can each hold an event.
  !seen && /[^[:space:]]/ && !/^[[:space:]]*#/ { seen = 1; if (/^[[:space:]]/) unread() }
  /^["'"'"'?{[<!&*:|>]/ || /^(verified|generated)[[:space:]]+:/ { emit(); inv = 0; unread(); next }
  # The id keys every event of the concept: a strange id, or a second `id`
  # line, makes the file unreadable.
  /^id:/ { strange = 0; cid = val($0); if (strange || ++ids > 1) unread() }
  /^(verified|generated):/ { emit(); inv = 1; kind = $0; sub(/:.*/, "", kind); rest = $0; sub(/^(verified|generated):[[:space:]]*/, "", rest); sub(/[[:space:]]+$/, "", rest)
    if (rest ~ /^\{/) { flowseq = 0; flowbuf = rest; inv = 0; if (index(rest, "}")) flushflow(); else inflow = 1 }
    else if (rest ~ /^\[/) { flowseq = 1; flowbuf = rest; inv = 0; if (index(rest, "]")) flushflow(); else inflow = 1 }
    else if (rest != "" && rest !~ /^#/ && rest !~ /^(null|~)$/) unread()
    next }
  # A comment line inside the block is no part of it and does not end it:
  # an event below a comment in the first column is still read.
  inv && /^[[:space:]]*#/ { next }
  inv && /^[^[:space:]-]/ { emit(); inv = 0 }
  inv && /^[[:space:]]*-[[:space:]]*(#.*)?$/ { emit(); inev = 1; next }
  inv && /^[[:space:]]*-[[:space:]]*\{/ { rest = $0; sub(/^[[:space:]]*-[[:space:]]*/, "", rest); flow(rest); next }
  inv && /^[[:space:]]*-[[:space:]]+/ { emit(); inev = 1; rest = $0; sub(/^[[:space:]]*-[[:space:]]+/, "", rest); kv(rest); next }
  inv && /^[[:space:]]+[a-z_]+:/ { inev = 1; kv($0); next }
  inv && /^[[:space:]]+[^[:space:]#]/ { inev = 1; odd = 1; next }
  END { if (plain && dashes >= 2 && path !~ /(^|\/)log\.md$/) unread(); emit(); printf "%s", out; if (bad) { printf "%s\t(unreadable)\t\t", cid ? cid : path; for (i = 1; i <= NR; i++) if (i in raw) printf "%s\001", raw[i]; printf "\tverified\n" } }'
}
# Each event is prefixed with its place: the concept's path, or `-` when the
# other ref has no file there. An event moved or copied between two concepts
# is one removal and one addition; a rename has `-` on both sides, so its
# events match by id. Duplicates are kept, so a second copy is an addition.
# Matches knowledge-registrar.yaml.
placed() {  # place, events on stdin -> the events with that place before each
  PLACE="$1" awk '{ print ENVIRON["PLACE"] "\t" $0 }'
}
events_in() {  # ref, the refs it is compared with..., paths on stdin -> the human events of those paths at that ref, sorted
  ref="$1"; shift
  while IFS= read -r f; do
    git cat-file -e "$ref:$f" 2>/dev/null || continue
    place="-"
    for other in "$@"; do
      if git cat-file -e "$other:$f" 2>/dev/null; then place="$f"; break; fi
    done
    git show "$ref:$f" 2>/dev/null | human_events "$f" | placed "$place"
  done | sort
}
# The paths a commit changes against any of its parents, which git lists for
# a merge only with -m. core.quotePath is off, or git would C-quote a name
# with a byte above 0x7f and `.md$` would miss it. The caller refuses the
# names git still quotes: `"`, `\` and control characters.
changed_paths() {  # commit, pathspecs... -> paths, one per line
  # --root: a commit with no parent, as a history merged in from elsewhere
  # starts with, is compared with the empty tree, so what it adds is read.
  git -c core.quotePath=false diff-tree --root --no-commit-id --name-only -r -m "$@" 2>/dev/null | sort -u
}

# The events that every parent held and the commit no longer holds. A
# `verified` event always counts, and a `generated` record only when the
# concept no longer holds one by a person.
removed_from() {  # events-before file, events-now file -> the removed events that need their person
  comm -23 "$1" "$2" | awk -F'\t' -v now="$2" '
    BEGIN { while ((getline line < now) > 0) { split(line, f, "\t"); if (f[6] == "generated") kept[f[2]] = 1 } }
    $6 == "verified" || !($2 in kept)'
}

# The toolkit follows a symbolic link and git does not, so a link onto a file
# outside the bundle holds events that no reader here sees, now or after an
# edit of that file. Only the doorway and the bundle path may be links, each
# onto the other. `.lokf` is always checked: as a link it takes the whole
# bundle out of the paths this script lists.
allowed_link() {  # path, the path it points at -> whether this is one of the bundle's two names
  case "$1:$2" in
    "$bundle:../knowledge_bundle"|"$doorway:$inner") return 0 ;;
    *) return 1 ;;
  esac
}
links_in() {  # commit, paths on stdin -> those the commit holds as a link it may not hold
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    case "$(git ls-tree "$1" -- "$f" 2>/dev/null)" in 120000\ *) ;; *) continue ;; esac
    allowed_link "$f" "$(git show "$1:$f" 2>/dev/null)" || printf '%s\n' "$f"
  done
}

# ---- --unattended: a change nobody stands behind may touch no person's record ----
# A concept's body up to `## Open questions`, without trailing blank lines:
# the text a person wrote, which a note added below it does not change.
body_of() {
  awk '{ sub(/\r$/, "") }
       NR == 1 { sub(/^\357\273\277/, "") }
       NR == 1 && $0 == "---" { fm = 1; next }
       fm == 1 { if ($0 == "---") fm = 2; next }
       /^## Open questions[ \t]*$/ { exit }
       /^[ \t]*$/ { blank++; next }
       { while (blank > 0) { print ""; blank-- } print }'
}
notes_of() {  # path, a concept on stdin -> each line a person's note would be, keyed by the path
  grep -E '^- [0-9]{4}-[0-9]{2}-[0-9]{2}, *human:' | awk -v f="$1" '{ print f "\t" $0 }' || true
}
if [ "$unattended" -eq 1 ]; then
  git rev-parse -q --verify HEAD >/dev/null 2>&1 || { echo "no commit to compare with" >&2; exit 2; }
  listed="$( { git -c core.quotePath=false diff --no-renames --name-only HEAD -- "$bundle" "$doorway" 2>/dev/null
               git -c core.quotePath=false ls-files --others --exclude-standard -- "$bundle" "$doorway" 2>/dev/null; } | sort -u )"
  quoted="$(printf '%s\n' "$listed" | grep '^"' || true)"
  [ -z "$quoted" ] || say "the change touches a bundle path git has to quote, which this script cannot read - rename it: $(printf '%s' "$quoted" | tr '\n' ' ')"
  while IFS= read -r f; do
    if [ -L "$f" ] && ! allowed_link "$f" "$(readlink "$f")"; then
      say "$f: an unattended change leaves a symbolic link under the bundle, which this gate cannot read - a concept is a file of its own"
    fi
  done < <(printf '%s\n%s\n' "$listed" "$top_dir" | grep -v '^"' || true)
  : > "$home/was.events"; : > "$home/now.events"; : > "$home/was.notes"; : > "$home/now.notes"
  while IFS= read -r f; do
    case "$f" in *.md) ;; *) continue ;; esac
    was_place="-"; now_place="-"
    if git show "HEAD:$f" > "$home/was.file" 2>/dev/null; then now_place="$f"; else : > "$home/was.file"; fi
    if [ -f "$f" ]; then cat "$f" > "$home/now.file"; was_place="$f"; else : > "$home/now.file"; fi
    human_events "$f" < "$home/was.file" | placed "$was_place" >> "$home/was.events"
    human_events "$f" < "$home/now.file" | placed "$now_place" >> "$home/now.events"
    notes_of "$f" < "$home/was.file" >> "$home/was.notes"
    notes_of "$f" < "$home/now.file" >> "$home/now.notes"
    if [ -f "$f" ] && human_events "$f" < "$home/was.file" | awk -F'\t' '$5 == "generated" { found = 1 } END { exit !found }' \
       && [ "$(body_of < "$home/was.file")" != "$(body_of < "$home/now.file")" ]; then
      say "$f: a person wrote this text, and an unattended change rewrites it"
    fi
  done < <(printf '%s\n' "$listed" | grep -v '^"' || true)
  # The loop above reads a rename as a delete and an add, with no copy of the
  # new path at HEAD, so a concept a person wrote could be renamed and
  # rewritten in one change. Pair the two paths by git rename detection, and
  # compare the old body at HEAD with the new one.
  while IFS="$(printf '\t')" read -r status old new; do
    case "$status" in R*) ;; *) continue ;; esac
    case "$new" in *.md) ;; *) continue ;; esac
    git show "HEAD:$old" > "$home/was.file" 2>/dev/null || continue
    [ -f "$new" ] || continue
    cat "$new" > "$home/now.file"
    if human_events "$old" < "$home/was.file" | awk -F'\t' '$5 == "generated" { found = 1 } END { exit !found }' \
       && [ "$(body_of < "$home/was.file")" != "$(body_of < "$home/now.file")" ]; then
      say "$new: a person wrote this text, which an unattended change rewrites under a new name (was $old)"
    fi
  done < <(git -c core.quotePath=false diff --name-status -M HEAD -- "$bundle" "$doorway" 2>/dev/null | grep -E '^R' || true)
  # Each list keeps its repeats: a second copy of an event or of a note is an addition.
  for kind in events notes; do sort "$home/was.$kind" -o "$home/was.$kind"; sort "$home/now.$kind" -o "$home/now.$kind"; done
  while IFS="$(printf '\t')" read -r _ id by at _; do
    [ -n "$id" ] || continue
    case "$by" in
      "(unreadable)") say "$id: an unattended change writes frontmatter this gate cannot read - spell it as conventions rule 10 asks" ;;
      *) say "$id: an unattended change adds or changes a confirmation by human:$by ($at)" ;;
    esac
  done < <(comm -13 "$home/was.events" "$home/now.events")
  while IFS="$(printf '\t')" read -r _ id by at _; do
    [ -n "$id" ] || continue
    case "$by" in
      "(unreadable)") say "$id: an unattended change removes frontmatter this gate could not read, which may have held a person's record" ;;
      *) say "$id: an unattended change removes a confirmation by human:$by ($at)" ;;
    esac
  done < <(comm -23 "$home/was.events" "$home/now.events")
  while IFS="$(printf '\t')" read -r f _; do
    [ -n "$f" ] && say "$f: an unattended change adds a note in a person's name"
  done < <(comm -13 "$home/was.notes" "$home/now.notes")
  while IFS="$(printf '\t')" read -r f _; do
    [ -n "$f" ] && say "$f: an unattended change removes a person's note"
  done < <(comm -23 "$home/was.notes" "$home/now.notes")
  if [ "$fail" -eq 0 ]; then
    echo "OK - the change against HEAD adds, changes and removes no person's event or note, and rewrites no text a person wrote"
  fi
  exit "$fail"
fi

# The range, oldest first, and the ids whose key file it adds, changes or
# removes: a confirmation by one of them in the same range fails before its
# signature is checked.
commits="$(git rev-list --reverse "$base..$head" 2>/dev/null)" || { echo "cannot resolve $base..$head" >&2; exit 2; }
# Only the two ends of the range are compared, so a merge of the default
# branch, which brings in a key added in a reviewed change of its own, adds
# no key file that the base lacks.
rekeyed=""
while IFS= read -r f; do
  [ -n "$f" ] || continue
  f="${f##*/}"; rekeyed="$rekeyed ${f%.*}"
done < <(git -c core.quotePath=false diff --no-renames --name-only "$base" "$head" -- "$curators" 2>/dev/null)
rekeyed_said=""

checked=0
for sha in $commits; do
  short="$(git rev-parse --short "$sha")"
  # A path this script cannot read, like an id it cannot check, is a finding,
  # never a skip.
  listed="$(changed_paths "$sha" -- "$bundle" "$doorway")"
  quoted="$(printf '%s\n' "$listed" | grep '^"' || true)"
  if [ -n "$quoted" ]; then
    say "$short touches a bundle path git has to quote, which this script cannot read - rename it: $(printf '%s' "$quoted" | tr '\n' ' ')"
    continue
  fi
  linked="$(printf '%s\n%s\n' "$listed" "$top_dir" | links_in "$sha")"
  if [ -n "$linked" ]; then
    say "$short leaves a symbolic link under the bundle, which this gate cannot read - a concept is a file of its own: $(printf '%s' "$linked" | tr '\n' ' ')"
    continue
  fi
  files="$(printf '%s\n' "$listed" | grep '\.md$' || true)"
  [ -n "$files" ] || continue
  # An event in this commit and in no parent is added, a re-dated `at` or a
  # moved `revision` included, and its actor must sign. parent.events holds
  # each event as often as the parent with most copies of it, and
  # every.events what every parent holds. So a merge claims nothing it took
  # from one side, and a root commit removes nothing.
  parents=()
  while IFS= read -r p; do [ -z "$p" ] || parents+=("$p"); done < <(git rev-parse "$sha^@" 2>/dev/null)
  : > "$home/every.events"; : > "$home/parent.events"; first=1
  for p in ${parents[@]+"${parents[@]}"}; do
    printf '%s\n' "$files" | events_in "$p" "$sha" > "$home/one.events"
    if [ "$first" -eq 1 ]; then cp "$home/one.events" "$home/every.events"; cp "$home/one.events" "$home/parent.events"; first=0
    else
      comm -12 "$home/every.events" "$home/one.events" > "$home/every.tmp"; mv "$home/every.tmp" "$home/every.events"
      { cat "$home/parent.events"; comm -13 "$home/parent.events" "$home/one.events"; } | sort > "$home/parent.tmp"; mv "$home/parent.tmp" "$home/parent.events"
    fi
  done
  printf '%s\n' "$files" | events_in "$sha" ${parents[@]+"${parents[@]}"} > "$home/sha.events"
  added="$(comm -13 "$home/parent.events" "$home/sha.events" | cut -f3 | sort -u)"
  gone="$(removed_from "$home/every.events" "$home/sha.events" | cut -f3 | sort -u)"
  ids="$(printf '%s\n%s\n' "$added" "$gone" | sed '/^$/d' | sort -u)"
  [ -n "$ids" ] || continue
  # One concept and one person count once, however many events of theirs it holds.
  touched="$({ comm -13 "$home/parent.events" "$home/sha.events"; removed_from "$home/every.events" "$home/sha.events"; } | cut -f2,3 | sort -u | grep -c . || true)"
  checked=$((checked + touched))
  format="$(sig_format "$sha")"
  status=""; signer=""
  if [ "$format" = pgp ] && [ "$gpg_ok" -eq 1 ]; then
    status="$(GNUPGHOME="$home" git verify-commit --raw "$sha" 2>&1 || true)"
    signer="$(printf '%s\n' "$status" | awk '/^\[GNUPG:\] VALIDSIG/ {print $3; exit}')"
  fi
  # Each id is read whole: one that holds `*` or `?` names no file here.
  while IFS= read -r id; do
    [ -n "$id" ] || continue
    # What this commit does with that person's record, for the finding's wording.
    does="adds or changes"
    printf '%s\n' "$added" | grep -qxF -- "$id" || does="removes"
    # A forge login is letters, digits, '.', '_' and '-'; anything else names
    # nobody the gate can look up, and could name a path outside $curators.
    case "$id" in
      "(unreadable)")
        say "$short $does frontmatter this gate cannot read, which may hold a person's record - spell it as conventions rule 10 asks"
        continue ;;
      *[!A-Za-z0-9._-]*|[!A-Za-z0-9]*)
        say "$short $does a confirmation by human:$id, which is not a login this gate can check (letters, digits, . _ - only)"
        continue ;;
    esac
    if [ -L "$curators/$id.asc" ] || [ -L "$curators/$id.pub" ]; then
      say "$short $does a confirmation by human:$id, whose key on file is a symbolic link - a key is a file of its own"
      continue
    fi
    has_asc=0; has_pub=0
    [ -f "$curators/$id.asc" ] && has_asc=1
    [ -f "$curators/$id.pub" ] && has_pub=1
    case " $rekeyed " in
      *" $id "*)
        case " $rekeyed_said " in *" $id "*) ;; *)
          rekeyed_said="$rekeyed_said $id"
          say "$base..$head adds or changes the key on file for human:$id and a confirmation by them in the same range - land the key in its own reviewed change first" ;;
        esac
        continue ;;
    esac
    if [ "$has_asc" -eq 0 ] && [ "$has_pub" -eq 0 ]; then
      say "$short $does a confirmation by human:$id, who has no key on file at $curators/$id.asc or $id.pub"
      continue
    fi
    case "$format" in
      none)
        say "$short $does a confirmation by human:$id but is unsigned" ;;
      pgp)
        if [ "$has_asc" -eq 0 ]; then
          say "$short $does a confirmation by human:$id with a GPG signature, but the key on file for them is an SSH key ($id.pub)"
        elif [ "$gpg_ok" -eq 0 ]; then
          say "$short $does a confirmation by human:$id with a GPG signature, and gpg is not installed here to verify it"
        elif printf '%s\n' "$status" | grep -qE '^\[GNUPG:\] (EXPKEYSIG|REVKEYSIG|EXPSIG)'; then
          say "$short $does a confirmation by human:$id signed by a key that has expired or been revoked"
        elif [ -z "$signer" ]; then
          unknown="$(printf '%s\n' "$status" | awk '/^\[GNUPG:\] NO_PUBKEY/ {print $3; exit}')"
          if [ -n "$unknown" ]; then
            say "$short $does a confirmation by human:$id but is signed by another key ($unknown, on file for nobody)"
          else
            say "$short $does a confirmation by human:$id but its signature does not verify (damaged, or made over different content)"
          fi
        elif ! gpg_fprs "$id" | grep -qx "$signer"; then
          say "$short $does a confirmation by human:$id but is signed by another key (${signer#"${signer%????????????????}"} is not in $id.asc)"
        fi ;;
      ssh)
        if [ "$has_pub" -eq 0 ]; then
          say "$short $does a confirmation by human:$id with an SSH signature, but the key on file for them is a GPG key ($id.asc)"
        elif ! have ssh-keygen; then
          say "$short $does a confirmation by human:$id with an SSH signature, and ssh-keygen is not installed here to verify it"
        else
          signature_of "$sha" > "$home/$sha.sig"
          if ! payload_of "$sha" | ssh-keygen -Y verify -f "$(allowed_of "$id")" -I "$id" -n git -s "$home/$sha.sig" >/dev/null 2>&1; then
            say "$short $does a confirmation by human:$id but its SSH signature is not by a key in $id.pub"
          fi
        fi ;;
    esac
  done <<IDS
$ids
IDS
done

if [ "$fail" -eq 0 ]; then
  echo "OK - $checked concept(s) hold a person's record new, changed or removed in $base..$head, each signed by the key on file for its curator"
fi
exit "$fail"
