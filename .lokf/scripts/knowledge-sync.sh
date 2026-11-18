#!/usr/bin/env bash
# Sync this host's sidecar copies and skills pin to one release of Knowledge
# Trust Ladder (KTL), and leave the diff for a person to review.
#
# The host pins KTL's `ktl` package in .lokf/pyproject.toml ("ktl==X.Y.Z"),
# with its hashes in .lokf/uv.lock, and carries byte-identical copies of the
# templates under skills/ktl-sidecar/templates/. The scheduled librarian
# installs ktl-librarian from the locked package, so copies and pin move
# together. The script:
#   - sets the pin to the tag's version and runs `uv lock` against the host's
#     own index; a host with no pin gets the `uv add` command that adds it;
#   - installs that package at the lock's hash, unbuilt, into a temporary
#     folder, and reads the manifest and templates there as data;
#   - copies each template the host carries, adds one an `always` or `needs`
#     line asks for, and lists the rest for ktl-sidecar's Step 5;
#   - reports local edits it overwrote, and host files no manifest line names;
#   - writes the changelog entry under "## [Unreleased]", "### Security";
#   - runs the sidecar's checks on the result.
# It starts from a clean tree, on the current branch or a new one from
# origin's default branch. It edits the pin line and runs `uv lock` because
# `uv add` also writes an index named in UV_DEFAULT_INDEX into the file.
#
# The host's own copy runs, from a person or knowledge-sync.yaml. A manifest
# rule it does not know is reported for the run after the newer copy is
# merged.
#
# Usage: knowledge-sync.sh [options] <tag>
#   --host <dir>      the host; by default the nearest parent holding .lokf/
#   --source <dir>    a folder of wheels used as the only index (uv's
#                     --no-index --find-links); it must hold every package
#                     the lock names
#   --branch          work on sync-<tag>, from origin's default branch
#   --commit          --branch, then commit the sync there
#   --push            --commit, then push the branch to origin
#   --pr              --push, then open the pull request with gh, from
#                     .github/PULL_REQUEST_TEMPLATE/knowledge-sync.md
#   --changed <file>  write the paths the sync changed or added, one a line
#   --report <file>   write the report as Markdown, for a pull request body
#   --no-checks       skip the sidecar's checks
#   --apply <patch>   apply a patch a sync made to this clean checkout, for
#                     the workflow's privileged job: check its paths and pin,
#                     lock the pin again from the index and compare, and move
#                     every workflow change into --held for a person to apply
#   --held <file>     where --apply writes the held workflow changes
#
# Exit 0 when the host is synced or already was. Exit 1 when the host was
# skipped (no .lokf/, no git, no ktl pin, uncommitted changes, the branch
# exists) or a check failed. Exit 2 when the arguments or the release are
# unusable.
#
# Everything runs inside main(), called on the last line: bash reads a
# function whole before running it, so the sync can overwrite this file.
set -euo pipefail

repo_url="https://github.com/noelmcloughlin/knowledge-trust-ladder"
pyproject=".lokf/pyproject.toml"
lock=".lokf/uv.lock"
# The release's folders, inside the installed package.
sidecar_in="ktl/skills/ktl-sidecar/templates"
website_in="ktl/skills/ktl-website/templates"
librarian_in="ktl/skills/ktl-librarian/SKILL.md"
# The pin, as the template writes it: one dependency line naming one release.
pin_re='^[[:space:]]*"ktl==([0-9]+\.[0-9]+\.[0-9]+)"[[:space:]]*,?[[:space:]]*(#.*)?$'

# The manifest's header says what each rule means. The rules this copy of
# the script knows:
manifest="knowledge-sync.manifest"
rules="copy titled always needs"
# The site files a host owns. The sync keeps the rest of the site templates,
# and the deploy workflow, current where site.toml is in website/ or
# ktl-website/.
website_owned=("site.toml" "README.md" "assets/css/custom.css")

usage() {
  sed -n '/^# Usage:/,/^# Exit 0/p' "$0" | sed -e '$d' -e 's/^# \{0,1\}//' >&2
  exit 2
}
die() { echo "knowledge-sync: $*" >&2; exit 2; }

# The run's temporary folder, and the undo for a stop between moving the
# pin and reading the release: the pin's two files, and in branch mode the
# branch the host was on.
work=""
undo_host=""; undo_previous=""; undo_branch=""
# shellcheck disable=SC2329 # main runs it from `trap cleanup EXIT`
cleanup() {
  if [[ -n "$undo_host" ]]; then
    local f
    for f in "$pyproject" "$lock"; do
      if [[ -f "$work/undo/${f##*/}" ]]; then cat "$work/undo/${f##*/}" > "$undo_host/$f"; else rm -f "$undo_host/$f"; fi
    done
    if [[ -n "$undo_branch" ]]; then
      git -C "$undo_host" switch --quiet "$undo_previous" 2>/dev/null && git -C "$undo_host" branch --quiet -D "$undo_branch" 2>/dev/null || true
    fi
  fi
  [[ -z "$work" ]] || rm -rf "$work"
}

# The version a host's pyproject.toml pins ktl to, or nothing: <file>.
pinned() { sed -nE "s/$pin_re/\\1/p" "$1" | head -n 1; }

# The ktl entry of a project's lock, with its hashes, as a requirements file
# uv reads: <project folder>. Nothing when the lock does not name ktl.
locked() {
  (cd "$1" && uv export --frozen --quiet --no-header --no-annotate --no-emit-project 2>/dev/null) \
    | awk '/^ktl==/ { p = 1 } p { print; if ($0 !~ /\\$/) exit }' || true
}

# Add the entry to the "### Security" section under "## [Unreleased]", and
# add that section at the end of Unreleased when it is missing. A file with
# CRLF line endings keeps them, and the added lines get them too. Return 3
# when the file has no "## [Unreleased]" heading.
add_entry() {
  local file="$1" entry="$2" tmp
  tmp="$(mktemp)"
  if awk -v entry="$entry" '
    { line[NR] = $0; key[NR] = $0; sub(/\r$/, "", key[NR]) }
    END {
      u = 0; e = NR + 1; s = 0; nl = ""
      for (i = 1; i <= NR; i++) if (key[i] == "## [Unreleased]") { u = i; break }
      if (u == 0) exit 3
      if (line[u] ~ /\r$/) nl = "\r"
      for (i = u + 1; i <= NR; i++) if (key[i] ~ /^## /) { e = i; break }
      for (i = u + 1; i < e; i++) if (key[i] ~ /^### Security[ \t]*$/) { s = i; break }
      if (s) {
        t = e
        for (i = s + 1; i < e; i++) if (key[i] ~ /^### /) { t = i; break }
        last = s
        for (i = s + 1; i < t; i++) if (key[i] !~ /^[ \t]*$/) last = i
        for (i = 1; i <= last; i++) print line[i]
        if (last == s) print nl
        print entry nl
      } else {
        last = u
        for (i = u + 1; i < e; i++) if (key[i] !~ /^[ \t]*$/) last = i
        for (i = 1; i <= last; i++) print line[i]
        print nl
        print "### Security" nl
        print nl
        print entry nl
      }
      for (i = last + 1; i <= NR; i++) print line[i]
    }' "$file" > "$tmp"; then
    cat "$tmp" > "$file"
    rm -f "$tmp"
    return 0
  fi
  rm -f "$tmp"
  return 3
}

# The paths a sync may touch: the sidecar's and the site's copies, the pin,
# its lock and the changelog, in the plain characters the templates use.
sync_paths='^(\.github/workflows/knowledge-[a-z]+\.yaml|\.github/PULL_REQUEST_TEMPLATE/knowledge-[a-z]+\.md|\.lokf/scripts/knowledge-[a-z]+\.(sh|py)|\.lokf/m365/[A-Za-z0-9._-]+|\.lokf/(schema/)?domain\.yaml|\.lokf/\.gitattributes|\.lokf/\.gitignore|\.lokf/justfile|\.lokf/pyproject\.toml|\.lokf/uv\.lock|(ktl-)?website/.+|CHANGELOG\.md)$'
owned_paths='^(ktl-)?website/(site\.toml|README\.md|assets/css/custom\.css)$'
plain_path='^[]A-Za-z0-9._/@+[-]+$'

# --apply, for knowledge-sync.yaml's privileged job, which trusts nothing the
# patch's maker decided. The patch may edit and add plain files on the paths
# above, and move the pin line to <tag>'s version. `uv lock`, run here from
# the checkout's lock, must write the patch's lock, so its hashes are the
# index's (`uv lock --locked` does not compare hashes). A workflow pushed with
# a token runs on that push with the repository's secrets, so every workflow
# change goes to <held>, a patch a person applies on top.
apply_patch() {
  local patch="$1" held="$2" tag="$3" paths wrong f full lane lines err
  [[ -f "$patch" ]] || die "no such patch: $patch"
  [[ -z "$(git status --porcelain)" ]] || die "the checkout has changes of its own; --apply takes a clean one"
  paths="$(git -c core.quotePath=false apply --numstat -- "$patch" | cut -f3-)" || die "$patch is not a patch git can read"
  wrong="$(printf '%s\n' "$paths" | grep -Ev "$sync_paths" || true)"
  wrong+=$'\n'"$(printf '%s\n' "$paths" | grep -E "$owned_paths" || true)"
  wrong+=$'\n'"$(printf '%s\n' "$paths" | grep -Ev "$plain_path" || true)"
  wrong+=$'\n'"$(printf '%s\n' "$paths" | grep -iE '(^|/)\.git(/|$)' || true)"
  if [[ -n "${wrong//[$'\n\t ']/}" ]]; then
    printf '%s\n' "$wrong" | sed '/^$/d; s/^/   refused  /' >&2
    die "the patch touches paths a sync may not"
  fi
  # A sync edits and adds plain files, of mode 644 or 755.
  local summary; summary="$(git apply --summary -- "$patch")"
  wrong="$(printf '%s\n' "$summary" | grep -E '^ (delete mode|rename|copy) ' || true)"
  wrong+=$'\n'"$(printf '%s\n' "$summary" | grep -E '^ create mode ' | grep -vE '^ create mode 100(644|755) ' || true)"
  wrong+=$'\n'"$(printf '%s\n' "$summary" | grep -E '^ mode change ' | grep -vE '^ mode change 100(644|755) => 100(644|755) ' || true)"
  if [[ -n "${wrong//[$'\n\t ']/}" ]]; then
    printf '%s\n' "$wrong" | sed '/^$/d; s/^ */   refused  /' >&2
    die "the patch does more than edit and add plain files"
  fi
  git apply --index --whitespace=nowarn -- "$patch"
  # pyproject.toml: one ktl pin line out, one in, at <tag>'s version.
  if ! git diff --cached --quiet -- "$pyproject"; then
    lines="$(git diff --cached -U0 -- "$pyproject" | grep -E '^[-+]' | grep -vE '^(---|\+\+\+) ' || true)"
    if printf '%s\n' "$lines" | sed 's/^[-+]//' | grep -vqE "$pin_re" \
       || [[ "$(printf '%s\n' "$lines" | grep -c '^-')" -ne 1 || "$(printf '%s\n' "$lines" | grep -c '^+')" -ne 1 ]]; then
      git reset --quiet --hard
      die "the patch changes $pyproject on a line other than the ktl pin"
    fi
    if [[ "$(printf '%s\n' "$lines" | grep '^+' | sed 's/^+//' | sed -nE "s/$pin_re/\\1/p")" != "${tag#v}" ]]; then
      git reset --quiet --hard
      die "the patch pins another ktl release than $tag, which this run syncs to"
    fi
  fi
  if ! git diff --cached --quiet -- "$pyproject" "$lock"; then
    if ! command -v uv >/dev/null 2>&1; then
      git reset --quiet --hard
      die "uv is not installed, and the lock the patch brings is checked with it"
    fi
    err="$(mktemp)"
    if git cat-file -e "HEAD:$lock" 2>/dev/null; then git show "HEAD:$lock" > "$lock"; else rm -f "$lock"; fi
    if ! (cd .lokf && uv lock --quiet --refresh-package ktl) 2>"$err"; then
      git reset --quiet --hard
      die "uv could not lock the patch's pin ($(tr '\n' ' ' < "$err" | cut -c1-300))"
    fi
    rm -f "$err"
    if ! git diff --quiet -- "$lock"; then
      git reset --quiet --hard
      die "the patch's $lock differs from the one uv resolves from the index for its pin, so it was not taken"
    fi
  fi
  # Hold every workflow change: the branch keeps the checkout's workflows.
  full="$(git write-tree)"
  while IFS= read -r f; do
    [[ -n "$f" ]] || continue
    if git cat-file -e "HEAD:$f" 2>/dev/null; then
      git show "HEAD:$f" > "$f"
    else
      git rm --cached --quiet -- "$f"
      rm -f -- "$f"
    fi
  done < <(git -c core.quotePath=false diff --cached --name-only -- .github/workflows/)
  if [[ -d .github/workflows ]]; then git add -- .github/workflows/; fi
  lane="$(git write-tree)"
  git diff --binary "$lane" "$full" -- .github/workflows/ > "$held"
  if ! git diff --cached --quiet -- .github/workflows/; then
    die "a workflow change is still staged; nothing is pushed"
  fi
  for f in $(git -c core.quotePath=false diff --cached --name-only); do echo "   staged   $f"; done
  for f in $(git -c core.quotePath=false diff --name-only "$lane" "$full"); do echo "   held     $f (a workflow change, for a person to apply)"; done
}

main() {
  local host="" source="" tag="" changed_out="" report_out="" out
  local apply="" held=""
  local branch_mode=0 commit=0 push=0 pr=0 checks=1
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --host) [[ $# -ge 2 ]] || usage; host="$2"; shift 2 ;;
      --source) [[ $# -ge 2 ]] || usage; source="$2"; shift 2 ;;
      --branch) branch_mode=1; shift ;;
      --commit) commit=1; branch_mode=1; shift ;;
      --push) push=1; commit=1; branch_mode=1; shift ;;
      --pr) pr=1; push=1; commit=1; branch_mode=1; shift ;;
      --changed) [[ $# -ge 2 ]] || usage; changed_out="$2"; shift 2 ;;
      --report) [[ $# -ge 2 ]] || usage; report_out="$2"; shift 2 ;;
      --no-checks) checks=0; shift ;;
      --apply) [[ $# -ge 2 ]] || usage; apply="$2"; shift 2 ;;
      --held) [[ $# -ge 2 ]] || usage; held="$2"; shift 2 ;;
      -h|--help) usage ;;
      -*) echo "knowledge-sync: unknown option $1" >&2; usage ;;
      *) [[ -z "$tag" ]] || usage; tag="$1"; shift ;;
    esac
  done
  [[ -n "$tag" ]] || usage
  if [[ ! "$tag" =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
    die "'$tag' is not a release tag (vMAJOR.MINOR.PATCH); a branch or a commit would let unreleased instructions into this host"
  fi
  local version="${tag#v}"

  # The host: --host, or the nearest parent holding .lokf/.
  if [[ -z "$host" ]]; then
    local d; d="$(pwd -P)"; host="$d"
    while [[ "$d" != "/" ]]; do
      if [[ -d "$d/.lokf" ]]; then host="$d"; break; fi
      d="$(dirname "$d")"
    done
  fi
  host="$(cd "$host" 2>/dev/null && pwd -P)" || die "no such directory: $host"
  if [[ ! -d "$host/.lokf" ]]; then
    echo "   no .lokf/ in $host: not a sidecar host; skipped" >&2
    return 1
  fi
  if ! git -C "$host" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
    echo "   $host is not a git work tree: the sync leaves a diff for review, and there is no diff to leave here; skipped" >&2
    return 1
  fi
  if [[ -n "$apply" ]]; then
    [[ -n "$held" ]] || die "--apply needs --held <file>"
    apply="$(cd "$(dirname "$apply")" && pwd -P)/$(basename "$apply")"
    held="$(cd "$(dirname "$held")" && pwd -P)/$(basename "$held")"
    ( cd "$host" && apply_patch "$apply" "$held" "$tag" )
    return
  fi
  for out in "$changed_out" "$report_out"; do
    [[ -z "$out" ]] || : > "$out"
  done

  # The pin: a person adds it once, and the sync moves it.
  local old_version=""
  [[ -f "$host/$pyproject" ]] && old_version="$(pinned "$host/$pyproject")"
  if [[ -z "$old_version" ]]; then
    echo "   no ktl pin in $pyproject: add it once, from $host, and run the sync again:" >&2
    echo "" >&2
    echo "   uv add --project .lokf \"ktl==$version\"" >&2
    return 1
  fi
  local old_pin="v$old_version"
  command -v uv >/dev/null 2>&1 || die "uv is not installed, and the sync reads the release through it: https://docs.astral.sh/uv/"
  if [[ -n "$source" ]]; then
    source="$(cd "$source" 2>/dev/null && pwd -P)" || die "no such directory: $source"
  fi
  # Where uv finds packages: the host's settings, or --source alone.
  local from=()
  [[ -z "$source" ]] || from=(--no-index --find-links "$source")
  work="$(mktemp -d)"
  trap cleanup EXIT

  # The branch starts from origin's default branch and tracks nothing, so a
  # plain push goes to a branch of the same name.
  if [[ -n "$(git -C "$host" status --porcelain --untracked-files=no)" ]]; then
    echo "   uncommitted changes in $host: commit or stash them first, so the diff left for review is the sync's alone; skipped" >&2
    return 1
  fi
  local branch="sync-$tag" base="" previous=""
  if [[ "$branch_mode" -eq 1 ]]; then
    git -C "$host" fetch --quiet origin 2>/dev/null || true
    base="$(git -C "$host" symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null || true)"
    if [[ -z "$base" ]]; then
      local candidate
      for candidate in origin/main origin/master main master; do
        if git -C "$host" rev-parse -q --verify "$candidate^{commit}" >/dev/null; then base="$candidate"; break; fi
      done
    fi
    if [[ -z "$base" ]]; then
      echo "   no default branch to start from (origin/HEAD, main or master); skipped" >&2
      return 1
    fi
    if git -C "$host" rev-parse -q --verify "refs/heads/$branch" >/dev/null; then
      echo "   $branch already exists in $host: finish it, or delete it, first; skipped" >&2
      return 1
    fi
    previous="$(git -C "$host" symbolic-ref --quiet --short HEAD 2>/dev/null || git -C "$host" rev-parse HEAD)"
    if ! git -C "$host" switch --quiet --no-track -c "$branch" "$base"; then
      echo "   could not start $branch from $base (git said why above); skipped" >&2
      return 1
    fi
    echo "   branch   $branch, from $base"
    # Read the pin again: the default branch may hold another.
    old_version="$(pinned "$host/$pyproject")"
    if [[ -z "$old_version" ]]; then
      git -C "$host" switch --quiet "$previous" && git -C "$host" branch --quiet -D "$branch"
      echo "   no ktl pin in $pyproject on $base: add it there once, and run the sync again:" >&2
      echo "" >&2
      echo "   uv add --project .lokf \"ktl==$version\"" >&2
      return 1
    fi
    old_pin="v$old_version"
  fi

  # Install one release as data: <requirements file> <folder>. --no-build
  # takes wheels only, since a build runs the release's code; --no-deps keeps
  # it to one package. uv runs in .lokf/ to use the host's index settings,
  # and checks the lock's hashes when the entry has them (a --source
  # folder's has none).
  fetch() {
    local hashes=()
    grep -q -- '--hash=sha256:' "$1" && hashes=(--require-hashes)
    (cd "$host/.lokf" && uv pip install --quiet --no-deps --no-build ${hashes[@]+"${hashes[@]}"} ${from[@]+"${from[@]}"} --target "$2" -r "$1")
  }

  # The release the host pins today, from its current lock, to tell a local
  # edit from the release's change. Unreadable, every change counts as the
  # release's, and the report says so.
  local old_dir="" req
  if [[ "$old_version" != "$version" ]]; then
    req="$work/old.txt"
    locked "$host/.lokf" > "$req"
    if [[ -n "$source" && ! -s "$req" ]]; then printf 'ktl==%s\n' "$old_version" > "$req"; fi
    if grep -q "^ktl==$old_version\\b" "$req" && fetch "$req" "$work/old" >/dev/null 2>&1; then
      old_dir="$work/old"
    fi
  fi

  # Move the pin and lock it. Until the manifest is checked, a stop undoes it.
  mkdir -p "$work/undo"
  [[ ! -f "$host/$lock" ]] || cp "$host/$lock" "$work/undo/uv.lock"
  cp "$host/$pyproject" "$work/undo/pyproject.toml"
  undo_host="$host"
  if [[ "$branch_mode" -eq 1 ]]; then undo_previous="$previous"; undo_branch="$branch"; fi
  local said
  if [[ "$old_version" != "$version" ]]; then
    sed -i.sync-bak -E "s/^([[:space:]]*\"ktl==)[0-9]+\.[0-9]+\.[0-9]+(\")/\\1$version\\2/" "$host/$pyproject"
    rm -f "$host/$pyproject.sync-bak"
  fi
  echo "   locking  ktl==$version"
  if ! said="$(cd "$host/.lokf" && uv lock --quiet --refresh-package ktl ${from[@]+"${from[@]}"} 2>&1)"; then
    if printf '%s' "$said" | grep -qF "no version of ktl=="; then
      die "no release $tag of ktl on the index: publish the release first, then sync (that order is the point)"
    elif printf '%s' "$said" | grep -qF "ktl was not found"; then
      die "the index this host's uv settings name has no ktl package, or could not be read; name an index that mirrors PyPI in .lokf/pyproject.toml or uv.toml"
    fi
    die "uv could not lock ktl==$version ($(printf '%s' "$said" | tr '\n' ' ' | cut -c1-300)). A private index needs its credential in UV_INDEX_KNOWLEDGE_USERNAME and UV_INDEX_KNOWLEDGE_PASSWORD"
  fi
  req="$work/new.txt"
  locked "$host/.lokf" > "$req"
  if [[ -n "$source" && ! -s "$req" ]]; then printf 'ktl==%s\n' "$version" > "$req"; fi
  if ! grep -q "^ktl==$version\\b" "$req"; then
    die "$lock names no ktl==$version after uv lock, so there is no locked release to read"
  fi
  if [[ -z "$source" ]] && ! grep -q -- '--hash=sha256:' "$req"; then
    die "$lock holds no hash for ktl==$version, so the release cannot be read at a hash a person merged"
  fi
  if ! said="$(fetch "$req" "$work/new" 2>&1)"; then
    die "ktl==$version could not be installed as data ($(printf '%s' "$said" | tr '\n' ' ' | cut -c1-300))"
  fi
  local new_dir="$work/new"
  [[ "$old_version" != "$version" ]] || old_dir="$new_dir"
  local new_t="$new_dir/$sidecar_in" old_t=""
  [[ -z "$old_dir" ]] || old_t="$old_dir/$sidecar_in"
  if [[ ! -f "$new_dir/$librarian_in" ]]; then
    die "ktl $version has no ${librarian_in#ktl/}; the librarian's install step installs that skill, so a host pinned to it fails every scheduled run"
  fi
  if [[ ! -f "$new_t/$manifest" ]]; then
    die "ktl $version has no ${sidecar_in#ktl/}/$manifest, so it predates the sync this script does; sync to a release that carries it"
  fi

  # Read the manifest as data, in the release's order. A copy path must stay
  # in the host's tree and use the templates' plain characters. An unknown
  # rule is kept to report; a line with a field missing stops the sync.
  local pairs=() titled=() always=() needs=() unknown=() rule a b rest line
  while IFS= read -r line; do
    line="${line%%#*}"
    read -r rule a b rest <<< "$line" || true
    [[ -n "$rule" ]] || continue
    case " $rules " in
      *" $rule "*) ;;
      *) unknown+=("$rule $a"); continue ;;
    esac
    [[ -n "$a" && -n "$b" ]] || die "$tag's $manifest has a $rule line with a field missing: $line"
    case "$rule" in
      copy|titled)
        if [[ ! "$b" =~ ^[A-Za-z0-9._/@+-]+$ || "$b" == /* || "$b" == *..* || "$a" == /* || "$a" == *..* ]]; then
          die "$tag's $manifest names a path outside the host, or with a character no template uses: $line"
        fi
        # A copy under .git is git configuration, which can name a command.
        if [[ "/$b/" =~ /\.[Gg][Ii][Tt]/ ]]; then
          die "$tag's $manifest names a path inside a .git folder: $line"
        fi
        pairs+=("$a:$b")
        [[ "$rule" != titled ]] || titled+=("$a") ;;
      always) always+=("$a|$b${rest:+ $rest}") ;;
      needs) needs+=("$a:$b:${rest:-is here}") ;;
    esac
  done < "$new_t/$manifest"
  [[ ${#pairs[@]} -gt 0 ]] || die "$tag's $manifest lists nothing to sync"
  # The manifest is checked: the moved pin stays.
  undo_host=""

  # A template at a release, by default the one being synced:
  # <template> [<templates folder>].
  tpl() { cat "${2:-$new_t}/$1"; }
  # The template as the host should carry it: <template> <host copy>
  # [<templates folder>].
  rendered() {
    local t
    for t in ${titled[@]+"${titled[@]}"}; do
      if [[ "$t" == "$1" ]]; then
        head -n 1 "$2"
        tpl "$1" "${3:-}" | tail -n +2 | OWN="$(grep -m 1 '^schema := ' "$2" || true)" \
          awk '/^schema := / && ENVIRON["OWN"] != "" { print ENVIRON["OWN"]; next } { print }'
        return
      fi
    done
    tpl "$1" "${3:-}"
  }
  # Why the host needs a template it lacks, or nothing: <template>.
  needed() {
    local entry
    for entry in ${always[@]+"${always[@]}"}; do
      if [[ "${entry%%|*}" == "$1" ]]; then echo "ktl-sidecar's ${entry##*|} installs it on every host"; return; fi
    done
    for entry in ${needs[@]+"${needs[@]}"}; do
      local t="${entry%%:*}" rest="${entry#*:}"
      local copy="${rest%%:*}" why="${rest#*:}"
      if [[ "$t" == "$1" && -f "$host/$copy" ]]; then echo "$copy $why"; return; fi
    done
  }
  # Whether a host copy differs from its template at the host's release:
  # <host copy> <that release's copy>.
  edited_here() { [[ -n "$old_dir" ]] && ! cmp -s "$2" "$1"; }

  local copied=() same=() added=() absent=() pins_only=() overwrote=() pair src dst why want was
  for pair in "${pairs[@]}"; do
    src="${pair%%:*}"; dst="${pair##*:}"
    [[ -f "$new_t/$src" ]] || continue  # a template this release did not have yet
    if [[ ! -f "$host/$dst" ]]; then
      why="$(needed "$src")"
      if [[ -z "$why" ]]; then
        absent+=("$dst")
        continue
      fi
      mkdir -p "$(dirname "$host/$dst")"
      tpl "$src" > "$host/$dst"
      [[ ! -x "$new_t/$src" ]] || chmod +x "$host/$dst"
      added+=("$dst ($why)")
      continue
    fi
    want="$(mktemp)"
    rendered "$src" "$host/$dst" > "$want"
    if cmp -s "$want" "$host/$dst"; then
      same+=("$dst")
    else
      # The copy as the host's release wrote it, else the host's copy.
      was="$(mktemp)"
      if [[ -n "$old_t" && -f "$old_t/$src" ]]; then
        rendered "$src" "$host/$dst" "$old_t" > "$was"
      else
        cat "$host/$dst" > "$was"
      fi
      # A copy that differs only on `uses:` lines was bumped by Dependabot;
      # the template's pins win, and the report says so. awk reads the whole
      # diff and decides, since diff exits 1 and would fail a pipeline.
      if awk '/^[<>]/ { if (/uses: /) pin = 1; else other = 1 } END { exit (pin && !other) ? 0 : 1 }' <(diff "$want" "$host/$dst"); then
        pins_only+=("$dst")
        copied+=("$dst")
      elif edited_here "$host/$dst" "$was"; then
        overwrote+=("$dst")
      else
        copied+=("$dst")
      fi
      cat "$want" > "$host/$dst"
      rm -f "$was"
    fi
    rm -f "$want"
  done

  # The site: every template is synced, and a missing one added.
  local website=0 site="" rel skip o new_w="$new_dir/$website_in" old_w=""
  [[ -z "$old_dir" ]] || old_w="$old_dir/$website_in"
  for o in website ktl-website; do
    if [[ -z "$site" && -f "$host/$o/site.toml" ]]; then site="$o"; fi
  done
  if [[ -n "$site" && -d "$new_w/website" ]]; then
    website=1
    while IFS= read -r rel; do
      # The same plain set as --apply's.
      if [[ ! "$rel" =~ $plain_path ||"/$rel/" =~ /\.[Gg][Ii][Tt]/ || "/$rel/" == */../* ]]; then
        die "$tag's website templates hold a path a host may not carry: $rel"
      fi
      skip=0; for o in "${website_owned[@]}"; do [[ "$rel" == "$o" ]] && skip=1; done
      [[ "$skip" -eq 1 ]] && continue
      dst="$site/$rel"; [[ "$rel" == gitignore ]] && dst="$site/.gitignore"
      if [[ ! -f "$host/$dst" ]]; then
        mkdir -p "$(dirname "$host/$dst")"
        cat "$new_w/website/$rel" > "$host/$dst"
        [[ ! -x "$new_w/website/$rel" ]] || chmod +x "$host/$dst"
        added+=("$dst (the site cannot build without it)")
      elif cmp -s "$new_w/website/$rel" "$host/$dst"; then
        same+=("$dst")
      else
        if [[ -n "$old_w" && -f "$old_w/website/$rel" ]] && ! cmp -s "$old_w/website/$rel" "$host/$dst"; then
          overwrote+=("$dst")
        else
          copied+=("$dst")
        fi
        cat "$new_w/website/$rel" > "$host/$dst"
        [[ ! -x "$new_w/website/$rel" ]] || chmod +x "$host/$dst"
      fi
    done < <(cd "$new_w/website" && find . -type f ! -path '*/__pycache__/*' | sed 's#^\./##' | LC_ALL=C sort)
    local wsrc="github/knowledge-website.yaml" wdst=".github/workflows/knowledge-website.yaml"
    if [[ -f "$new_w/$wsrc" ]]; then
      if [[ ! -f "$host/$wdst" ]]; then
        absent+=("$wdst")
      elif cmp -s "$new_w/$wsrc" "$host/$wdst"; then
        same+=("$wdst")
      else
        if [[ -n "$old_w" && -f "$old_w/$wsrc" ]] && ! cmp -s "$old_w/$wsrc" "$host/$wdst"; then
          overwrote+=("$wdst")
        else
          copied+=("$wdst")
        fi
        cat "$new_w/$wsrc" > "$host/$wdst"
      fi
    fi
  fi

  # Host files where the templates go that the manifest does not name: a
  # template the release dropped or renamed, or the host's own. Reported.
  local unlisted=() known=" " f
  while IFS= read -r line; do
    line="${line%%#*}"
    read -r rule a b rest <<< "$line" || true
    [[ -z "$b" ]] || known+="$b "
  done < "$new_t/$manifest"
  known+=".github/workflows/knowledge-website.yaml "
  while IFS= read -r f; do
    case "$known" in *" $f "*) ;; *) unlisted+=("$f") ;; esac
  done < <(cd "$host" && find .lokf/scripts .github/workflows -maxdepth 1 -type f \( -name 'knowledge-*.sh' -o -name 'knowledge-*.py' -o -name 'knowledge-*.yaml' -o -name 'knowledge-*.yml' \) 2>/dev/null | sed 's#^\./##' | LC_ALL=C sort)

  # Whether the pin's two files changed: the version, or a lock uv wrote again.
  local pin_moved=0 lock_files=() pin_line
  for f in "$pyproject" "$lock"; do
    [[ -z "$(git -C "$host" status --porcelain -- "$f")" ]] || lock_files+=("$f")
  done
  [[ "$old_version" == "$version" ]] || pin_moved=1

  for f in ${copied[@]+"${copied[@]}"}; do echo "   copied   $f"; done
  for f in ${overwrote[@]+"${overwrote[@]}"}; do echo "   local    $f differed from its template at $old_pin, a local edit; the copy from $tag is written over it"; done
  for f in ${same[@]+"${same[@]}"}; do echo "   same     $f"; done
  for f in ${added[@]+"${added[@]}"}; do echo "   added    $f"; done
  for f in ${absent[@]+"${absent[@]}"}; do echo "   absent   $f (never installed here: ktl-sidecar's Step 5 decides, not this script)"; done
  for f in ${pins_only[@]+"${pins_only[@]}"}; do echo "   pins     $f differed only on its action pins, which Dependabot bumped here first; the template's pins are back until the skills repository bumps them"; done
  for f in ${unknown[@]+"${unknown[@]}"}; do echo "   unknown  $f: a manifest rule this copy of knowledge-sync.sh does not know; it is left for the next sync, once the copy $tag brings is merged"; done
  for f in ${unlisted[@]+"${unlisted[@]}"}; do echo "   unlisted $f: no line of $tag's manifest names it, so the sync left it as it is"; done
  if [[ "$pin_moved" -eq 0 ]]; then
    pin_line="already $tag"
  elif [[ "$(printf '%s\n%s\n' "$old_version" "$version" | sort -V | tail -n 1)" == "$old_version" ]]; then
    pin_line="$old_pin back to $tag: an older release than the host had"
  else
    pin_line="$old_pin to $tag"
  fi
  echo "   pin      $pin_line"
  # Whether ktl-librarian changed between the two releases.
  local skill_line=""
  if [[ "$pin_moved" -eq 1 && -n "$old_dir" ]]; then
    local n; n="$( (diff -rq "$old_dir/ktl/skills/ktl-librarian" "$new_dir/ktl/skills/ktl-librarian" || true) | wc -l | tr -d ' ')"
    if [[ "$n" -gt 0 ]]; then skill_line="ktl-librarian changed in $n file(s) between $old_pin and $tag"; else skill_line="ktl-librarian unchanged between $old_pin and $tag"; fi
    echo "   skill    $skill_line"
  elif [[ "$pin_moved" -eq 1 ]]; then
    echo "   skill    $old_pin could not be read from the lock and the index, so each changed copy is reported as the release's"
  fi
  if [[ "$website" -eq 1 ]]; then
    echo "   website  the site's copies are synced; build it there to check: bash $site/scripts/build.sh"
  fi

  if [[ ${#copied[@]} -eq 0 && ${#added[@]} -eq 0 && ${#overwrote[@]} -eq 0 && ${#lock_files[@]} -eq 0 ]]; then
    if [[ "$branch_mode" -eq 1 ]]; then
      git -C "$host" switch --quiet "$previous" && git -C "$host" branch --quiet -D "$branch"
      echo "   nothing to sync; back on $previous, and $branch removed"
    else
      echo "   nothing to sync"
    fi
    return 0
  fi

  # The changelog entry, from what the sync did. The link compares the two
  # pins. "No plugin change" is added for an Obsidian plugin, whose root
  # manifest.json names minAppVersion.
  local link tail="" entry list=() i changelog_line
  if [[ -n "$old_pin" && "$old_pin" != "$tag" ]]; then
    link="$repo_url/compare/$old_pin...$tag"
  else
    link="$repo_url/blob/$tag/CHANGELOG.md"
  fi
  if [[ -f "$host/manifest.json" ]] && grep -q '"minAppVersion"' "$host/manifest.json"; then
    tail=" No plugin change."
  fi
  # A list of paths in code spans, joined with commas and a last "and".
  joined() {
    local out="" k=1 n=$#
    for f in "$@"; do
      if [[ "$k" -eq 1 ]]; then out="\`$f\`"; elif [[ "$k" -eq "$n" ]]; then out+=" and \`$f\`"; else out+=", \`$f\`"; fi
      k=$((k + 1))
    done
    printf '%s' "$out"
  }
  local local_tail=""
  if [[ ${#overwrote[@]} -gt 0 ]]; then
    local_tail=" The sync also wrote the template over a local edit of $(joined "${overwrote[@]}")."
  fi
  if [[ ${#copied[@]} -eq 0 && ${#added[@]} -eq 0 ]]; then
    entry="- **The skills pin is at Knowledge Trust Ladder [$tag]($link).** None of the sidecar copies this repository carries changed.$local_tail$tail"
    [[ ${#overwrote[@]} -eq 0 ]] || entry="- **The skills pin is at Knowledge Trust Ladder [$tag]($link).**$local_tail$tail"
  else
    for f in ${copied[@]+"${copied[@]}"} ${added[@]+"${added[@]}"}; do list+=("${f%% (*}"); done
    entry="- **The sidecar copies and the skills pin are at Knowledge Trust Ladder [$tag]($link).** The release changed $(joined "${list[@]}") here.$local_tail$tail"
  fi
  local changed=()
  for f in ${copied[@]+"${copied[@]}"} ${overwrote[@]+"${overwrote[@]}"}; do changed+=("$f"); done
  for f in ${added[@]+"${added[@]}"}; do changed+=("${f%% (*}"); done
  for f in ${lock_files[@]+"${lock_files[@]}"}; do changed+=("$f"); done
  if [[ ! -f "$host/CHANGELOG.md" ]]; then
    changelog_line="There is no CHANGELOG.md here, so no entry was written."
  elif grep -qF "[$tag]($link)" "$host/CHANGELOG.md"; then
    changelog_line="CHANGELOG.md already has the entry for $tag."
  elif add_entry "$host/CHANGELOG.md" "$entry"; then
    changelog_line="CHANGELOG.md has the entry, under its Unreleased heading and Security."
    changed+=("CHANGELOG.md")
  else
    changelog_line="CHANGELOG.md has no Unreleased heading, so add the entry by hand:"$'\n'"   $entry"
  fi
  echo "   entry    $changelog_line"

  # The sidecar's checks, as the host's gate runs them. `set -e` is off in a
  # subshell followed by `||`, so each check records its own failure.
  local ok=1 check_lines=() status=0
  if [[ "$checks" -eq 1 ]]; then
    local verdicts; verdicts="$(mktemp)"
    (
      rc=0
      cd "$host/.lokf"
      if [[ -x scripts/knowledge-preflight.sh ]]; then
        echo "preflight: $(bash scripts/knowledge-preflight.sh | tail -1)"
      fi
      if command -v uv >/dev/null 2>&1; then
        # The recipe, with the just uv.lock pins where it pins one. just's
        # closing line on a failure is dropped, to show lokf's verdict.
        just=(uvx --from rust-just==1.47.0 just)
        if grep -qx 'name = "rust-just"' uv.lock 2>/dev/null; then just=(uv run --locked just); fi
        if out="$("${just[@]}" lokf-check-refs 2>&1 | grep -v '^error: Recipe ' | tail -1)"; then
          echo "lokf validate --check-refs: $out"
        else
          echo "lokf validate --check-refs: failed, $out"; rc=1
        fi
      else
        echo "lokf validate --check-refs: skipped, uv is not installed; the conventions script runs without its parser's half"
      fi
      # With uv, --strict fails a rule it could not check. Without uv, the
      # shell half runs alone and the line says so.
      if [[ -f scripts/knowledge-conventions.sh ]]; then
        if command -v uv >/dev/null 2>&1; then strict="--strict"; pass="pass"; else strict=""; pass="the shell half passes; the rules that need uv were not checked, since it is not installed"; fi
        if out="$(bash scripts/knowledge-conventions.sh knowledge ${strict:+"$strict"} 2>&1)"; then
          echo "conventions: $pass"
        else
          echo "conventions: failed"; printf '%s\n' "$out" | sed 's/^/    /'; rc=1
        fi
      fi
      exit "$rc"
    ) > "$verdicts" || ok=0
    while IFS= read -r f; do check_lines+=("$f"); echo "   check    $f"; done < "$verdicts"
    rm -f "$verdicts"
    if [[ "$ok" -eq 0 ]]; then
      echo "   FAIL     a check above failed: fix the bundle in the same change, or the host's gate fails on it"
      status=1
    fi
  else
    check_lines+=("skipped (--no-checks)")
    echo "   check    skipped (--no-checks)"
  fi

  # The files to stage, by name: what the sync changed, and what it added.
  if [[ -n "$changed_out" ]]; then printf '%s\n' "${changed[@]}" > "$changed_out"; fi
  # The report as Markdown, for a pull request body or a job summary.
  local body; body="$(mktemp)"
  {
    if [[ -n "$old_pin" && "$old_pin" != "$tag" ]]; then
      echo "Brings the sidecar copies and the skills pin of this repository to Knowledge Trust Ladder [$tag]($link), from $old_pin."
    else
      echo "Brings the sidecar copies and the skills pin of this repository to Knowledge Trust Ladder [$tag]($link)."
    fi
    if [[ ${#copied[@]} -gt 0 ]]; then
      if [[ -n "$old_dir" ]]; then
        echo; echo "The release changed these copies:"; echo
      else
        echo; echo "These copies differed from the templates at $tag, and the release's copy is written over each; $old_pin could not be read to tell a release's change from a local edit:"; echo
      fi
      for f in "${copied[@]}"; do echo "- \`$f\`"; done
    fi
    if [[ ${#overwrote[@]} -gt 0 ]]; then
      echo; echo "A local edit this sync overwrote, since the copy differed from its template at $old_pin. Restore it from git history if it should stay, and propose it to the skills repository:"; echo
      for f in "${overwrote[@]}"; do echo "- \`$f\`"; done
    fi
    if [[ ${#added[@]} -gt 0 ]]; then
      echo; echo "Added, because a file here needs it:"; echo
      for f in "${added[@]}"; do
        local path="${f%% (*}" why="${f#* (}"; why="${why%)}"
        case "$why" in .*) why="\`${why%% *}\` ${why#* }" ;; esac
        echo "- \`$path\`: $why"
      done
    fi
    if [[ ${#absent[@]} -gt 0 ]]; then
      echo; echo "Not added, for ktl-sidecar's Step 5 to decide:"; echo
      for f in "${absent[@]}"; do echo "- \`$f\`"; done
    fi
    if [[ ${#unknown[@]} -gt 0 ]]; then
      echo; echo "Left for the next sync, since this copy of knowledge-sync.sh does not know their rule:"; echo
      for f in "${unknown[@]}"; do echo "- \`${f//\`/}\`"; done
    fi
    if [[ ${#unlisted[@]} -gt 0 ]]; then
      echo; echo "No line of $tag's manifest names these files, so the sync left them as they are. A release may have dropped or renamed the template:"; echo
      for f in "${unlisted[@]}"; do echo "- \`${f//\`/}\`"; done
    fi
    echo
    if [[ "$pin_moved" -eq 1 ]]; then
      echo "The skills pin, \`ktl\` in \`$pyproject\`, moves from $old_pin to $tag, and \`$lock\` holds the package's hashes.${skill_line:+ $skill_line.}"
    else
      echo "The skills pin: $pin_line."
    fi
    echo; echo "The sidecar's checks on the synced copies:"; echo
    for f in ${check_lines[@]+"${check_lines[@]}"}; do echo "- $f"; done
    echo; echo "$changelog_line" | head -1
  } > "$body"
  if [[ -n "$report_out" ]]; then cat "$body" > "$report_out"; fi

  local subject="security(sidecar): sync copies and skills pin from $tag"
  if [[ "$commit" -eq 1 ]]; then
    git -C "$host" add -- "${changed[@]}"
    git -C "$host" commit --quiet -m "$subject"
    echo "   commit   $(git -C "$host" rev-parse --short HEAD) $subject"
  else
    echo ""
    local where="the current branch"; [[ "$branch_mode" -eq 0 ]] || where="$branch"
    echo "   Then commit, from $host, on $where:"
    echo ""
    local staged=("${changed[@]}")
    for i in "${!staged[@]}"; do
      local line="     ${staged[$i]}"; [[ "$i" -eq 0 ]] && line="   git add ${staged[$i]}"
      if [[ "$i" -lt $((${#staged[@]} - 1)) ]]; then echo "$line \\"; else echo "$line"; fi
    done
    echo "   git commit -m \"$subject\""
  fi
  # The pull request body: the report, then the host's template with the
  # reviewer's checklist, kept under .git/ out of every commit.
  local gitdir body_file
  gitdir="$(git -C "$host" rev-parse --absolute-git-dir 2>/dev/null || printf '%s' "$host/.git")"
  body_file="$gitdir/knowledge-sync-body.md"
  {
    cat "$body"
    if [[ -f "$host/.github/PULL_REQUEST_TEMPLATE/knowledge-sync.md" ]]; then
      echo
      cat "$host/.github/PULL_REQUEST_TEMPLATE/knowledge-sync.md"
    fi
  } > "$body_file" 2>/dev/null || body_file="$body"
  if [[ "$push" -eq 1 ]]; then
    git -C "$host" push --quiet --set-upstream origin "$branch"
    echo "   pushed   origin/$branch"
  fi
  if [[ "$pr" -eq 1 ]]; then
    if ! command -v gh >/dev/null 2>&1; then
      echo "   gh is not installed, so the pull request was not opened; the branch is pushed" >&2
      return 1
    fi
    local url
    url="$(cd "$host" && gh pr create --title "$subject" --body-file "$body_file" --head "$branch" --base "${base#origin/}")"
    echo "   pr       $url"
  elif [[ "$push" -eq 1 ]]; then
    echo ""
    echo "   Then open the pull request, from $host:"
    echo ""
    echo "   gh pr create --title \"$subject\" --body-file \"$body_file\""
  fi
  [[ "$body_file" == "$body" ]] || rm -f "$body"
  return "$status"
}

main "$@"; exit
# Bash reads a script as it runs, so after main a running copy would read on
# into the file the sync wrote over it; the exit stops it. An older copy
# ending in a bare `main "$@"` reads " exit" next from this file, and stops.
