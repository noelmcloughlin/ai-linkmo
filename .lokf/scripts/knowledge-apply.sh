#!/usr/bin/env bash
# The pen, the librarian's only way to write the bundle. ktl-librarian
# describes each change to the bundle as an operation in .lokf/patch.yaml and
# never edits .lokf/knowledge/ itself; this script checks every operation and
# writes the files, or refuses the whole file and writes nothing. The rules live in the Python half beside it,
# knowledge-apply.py, which this script runs through `uv run` (the script's
# own header names pyyaml) or, without uv, through python3 where pyyaml is
# installed. The scheduled wrapper runs it after the agent has finished.
#
# Usage: knowledge-apply.sh [--dry-run] [--keep] [--handoff <file>] [--root <repo-root>] [<patch-file>]
#        knowledge-apply.sh --format
#   --dry-run   report every finding and what would be written; write nothing
#   --keep      leave the patch file in place after applying it
#   --handoff   after applying, write the patch's lines for the reviewer to
#               <file>, or leave it empty when the patch has none
#   --root      the repository root; default: two levels above this script
#   --format    print the patch file's shape, every operation with its keys,
#               and exit, so the format comes from the script that enforces it
# Exit 0 applied (or would apply); 1 findings, nothing written; 2 usage or no runner.
[ -n "${BASH_VERSION:-}" ] || { echo "run this with bash: bash ${0##*/} [--dry-run] [--keep] [--format] [--handoff <file>] [--root <dir>] [<patch-file>]" >&2; exit 2; }
set -u
usage() { echo "usage: ${0##*/} [--dry-run] [--keep] [--format] [--handoff <file>] [--root <dir>] [<patch-file>]" >&2; exit 2; }
here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
root=""
args=()
while [ $# -gt 0 ]; do
  case "$1" in
    --root) [ $# -ge 2 ] || usage; root="$2"; shift 2 ;;
    --handoff) [ $# -ge 2 ] || usage; args+=("$1" "$2"); shift 2 ;;
    --dry-run|--keep|--format) args+=("$1"); shift ;;
    -h|--help) usage ;;
    --) shift; while [ $# -gt 0 ]; do args+=("$1"); shift; done ;;
    -*) echo "unknown option: $1" >&2; usage ;;
    *) args+=("$1"); shift ;;
  esac
done
[ -n "$root" ] || root="$(cd "$here/../.." && pwd)"
py="$here/knowledge-apply.py"
[ -f "$py" ] || { echo "knowledge-apply: $py is missing beside this script; run ktl-sidecar's repair path" >&2; exit 2; }
if command -v uv >/dev/null 2>&1; then
  exec uv run --quiet "$py" --root "$root" ${args[@]+"${args[@]}"}
elif command -v python3 >/dev/null 2>&1 && python3 -c 'import yaml' >/dev/null 2>&1; then
  exec python3 "$py" --root "$root" ${args[@]+"${args[@]}"}
fi
echo "knowledge-apply: needs uv, which installs pyyaml for the script, or python3 with pyyaml; nothing was written. The sidecar's references/prerequisites.md says who installs uv." >&2
exit 2
