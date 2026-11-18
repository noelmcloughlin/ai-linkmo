#!/usr/bin/env bash
# Writes assets/vendor/<name>.js for each library hugo.toml names under
# [params.vendor], from its npm package, for a network that blocks the CDN.
#
#   scripts/vendor.sh              cytoscape and mermaid
#   scripts/vendor.sh mermaid      one of them
#
# npm fetches the package from the registry it is set to read, in .npmrc or
# npm_config_registry. The package and version are the ones in the address
# hugo.toml names, and a file is kept only when its SHA-256 is the one
# hugo.toml holds. Commit the files: the build takes them before the address.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
command -v npm >/dev/null 2>&1 || { echo "vendor.sh: npm not found; it fetches each package from the registry it reads" >&2; exit 1; }
mode=$("$here/scripts/uv-env.sh" "$here")
# name, package@version, path in the package and SHA-256, one line each.
tool=(uv run --project "$here" "$mode" --quiet)
wanted=$("${tool[@]}" python -I - "$here/hugo.toml" "$@" <<'PY'
import re, sys, tomllib
with open(sys.argv[1], "rb") as file:
    vendor = tomllib.load(file)["params"]["vendor"]
for name in sys.argv[2:] or sorted(vendor):
    if name not in vendor:
        sys.exit(f"vendor.sh: hugo.toml names no library {name}; it names {', '.join(sorted(vendor))}")
    found = re.fullmatch(r"https://cdn\.jsdelivr\.net/npm/((?:@[a-z0-9._-]+/)?[a-z0-9._-]+@[0-9][A-Za-z0-9.+-]*)/([A-Za-z0-9._/-]+)", vendor[name]["url"])
    if not found or ".." in found.group(2) or not re.fullmatch(r"[0-9a-f]{64}", vendor[name]["sha256"]):
        sys.exit(f"vendor.sh: hugo.toml's address for {name} is not a jsDelivr npm address with a SHA-256")
    print(name, found.group(1), found.group(2), vendor[name]["sha256"])
PY
)
work=$(mktemp -d "${TMPDIR:-/tmp}/vendor.XXXXXX")
trap 'rm -rf "$work"' EXIT
mkdir -p "$here/assets/vendor"
while read -r name package path sha; do
  [ -n "$name" ] || continue
  mkdir "$work/$name"
  (cd "$work/$name" && npm pack --silent --ignore-scripts "$package" >/dev/null) || { echo "vendor.sh: npm could not fetch $package from the registry it reads" >&2; exit 1; }
  tar -xzf "$work/$name"/*.tgz -C "$work/$name" "package/$path" || { echo "vendor.sh: $package holds no $path" >&2; exit 1; }
  got=$("${tool[@]}" python -I -c 'import hashlib, sys; print(hashlib.sha256(open(sys.argv[1], "rb").read()).hexdigest())' "$work/$name/package/$path")
  [ "$got" = "$sha" ] || { echo "vendor.sh: $package's $path has SHA-256 $got, not the $sha that hugo.toml names; no file is written" >&2; exit 1; }
  cp "$work/$name/package/$path" "$here/assets/vendor/$name.js"
  echo "vendor.sh: wrote assets/vendor/$name.js from $package"
done <<<"$wanted"
