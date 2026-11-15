#!/usr/bin/env bash
# Writes what Hugo cannot work out for itself into generated/, which is never
# committed: the four files `lokf export` writes, the pages gen-doc writes for
# a LinkML schema, and the trust labels and health line knowledge-report.sh
# prints. It also writes the repository's tags, and the data when site.toml
# names it. Hugo reads everything else from the repository through the mounts
# in hugo.toml.
#
# Any step that fails stops the build: a site with no labels would show every
# concept as unchecked.
set -euo pipefail

here=$(cd "$(dirname "$0")/.." && pwd)
root=$(cd "$here/.." && pwd)
out="$here/generated"
repo_url=$(sed -n 's/^repo = "\(.*\)"$/\1/p' "$here/site.toml")
[ -n "$repo_url" ] || { echo "prepare.sh: site.toml has no repo = \"...\" line" >&2; exit 1; }
[ -f "$root/.lokf/knowledge/index.md" ] || { echo "prepare.sh: no .lokf/knowledge/index.md under $root; the ktl-sidecar skill installs the bundle" >&2; exit 1; }
# The commit of the build, or the branch where the folder is not under git.
branch=$(sed -n 's/^branch = "\(.*\)"$/\1/p' "$here/site.toml")
ref=$(git -C "$root" rev-parse HEAD 2>/dev/null || echo "${branch:-main}")
# site.toml's source: the folder the README, docs/, the changelog and
# .assets/ come from, by the mounts in generated/source.toml. Its linkml: the
# folder whose src/<name>/schema/ holds the schema.
source=$(sed -n 's/^source = "\(.*\)"$/\1/p' "$here/site.toml"); source=${source%/}
linkml=$(sed -n 's/^linkml = "\(.*\)"$/\1/p' "$here/site.toml"); linkml=${linkml%/}
src_root="$root${source:+/$source}"

# An SVG is served as a page of its own, so one that holds a script, an event
# handler or a javascript: address would run on the site's address.
if active=$(grep -rlEi --include='*.svg' '<script|<foreignObject|[[:space:]]on[a-z]+[[:space:]]*=|javascript:' "$src_root/.assets" "$src_root/docs" "$root/.lokf/knowledge" "$here/static" 2>/dev/null); then
  echo "prepare.sh: these SVG files hold a script, an event handler or a javascript: address, and the site would serve them:" >&2
  echo "$active" >&2
  exit 1
fi

rm -rf "$out"
mkdir -p "$out/knowledge"

# hugo.toml's mounts with the README, docs/, the changelog and .assets/ read
# from the source folder. build.sh reads this file last, and Hugo then takes
# its mounts in place of hugo.toml's.
if [ -n "$source" ]; then
  [ -d "$src_root" ] || { echo "prepare.sh: site.toml's source names $source, which is no folder" >&2; exit 1; }
  sed -n '/^\[\[module\.mounts\]\]/,$p' "$here/hugo.toml" | sed \
    -e "s#^source = \"\.\./README\.md\"#source = \"../$source/README.md\"#" \
    -e "s#^source = \"\.\./docs\"#source = \"../$source/docs\"#" \
    -e "s#^source = \"\.\./CHANGELOG\.md\"#source = \"../$source/CHANGELOG.md\"#" \
    -e "s#^source = \"\.\./\.assets\"#source = \"../$source/.assets\"#" >"$out/source.toml"
fi

# The bundle's own tools: lokf, and the LinkML it is built on.
lokf=(uv run --project "$root/.lokf" --frozen --quiet)

# The domain vocabulary the sidecar's justfile names, so the export carries
# its classes as `just lokf-convert` does.
schema=$(sed -n 's/^schema := "\(.*\)"$/\1/p' "$root/.lokf/justfile" 2>/dev/null || true)
"${lokf[@]}" lokf export ${schema:+--schema "$root/.lokf/$schema"} "$root/.lokf/knowledge" \
  --out-dir "$out/knowledge" \
  --source-base "$repo_url/blob/$ref/.lokf/knowledge"

# The schema: the file site.toml's schema names, or else a LinkML project's
# src/<name>/schema/<name>.yaml, in site.toml's linkml folder first, then at
# the root, then in the .linkml/ sidecar. gen-doc writes a page per class,
# slot, enumeration and type, each kind in a folder of its own, and
# gen-erdiagram writes the diagram the overview shows. The schema file is
# copied beside them, and source.txt holds its path in the repository, or
# the pkg: name of one inside a package.
gendoc() {
  # gen-doc prints a stray "None" when it ends.
  "${lokf[@]}" gen-doc --subfolder-type-separation --index-name _index -d "$out/schema" "$1" >/dev/null
  "${lokf[@]}" gen-erdiagram --format mermaid "$1" >"$out/schema/diagram.mmd"
  # Each local file it imports in turn goes beside it at the same relative
  # path, so the served copy loads as the repository's does. An import from
  # outside the schema's folder, or one named by a prefix, is not served.
  "${lokf[@]}" python - "$1" "$out/schema" <<'PY'
import shutil, sys
from pathlib import Path
import yaml
top, out = Path(sys.argv[1]).resolve(), Path(sys.argv[2])
todo, seen = [top], set()
while todo:
    f = todo.pop()
    if f in seen or not f.is_file() or not f.is_relative_to(top.parent):
        continue
    seen.add(f)
    (out / f.relative_to(top.parent)).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(f, out / f.relative_to(top.parent))
    for name in (yaml.safe_load(f.read_text(encoding="utf-8")) or {}).get("imports") or []:
        if isinstance(name, str) and ":" not in name:
            todo.append((f.parent / f"{name}.yaml").resolve())
PY
}
# site.toml's schema is a path from the root, or pkg:<package>/<path> for a
# schema inside a package that the environment of the uv project
# schemaProject names holds. The package is found, never imported.
named=$(sed -n 's/^schema = "\(.*\)"$/\1/p' "$here/site.toml")
if [ -n "$named" ]; then
  case "$named" in
    pkg:*)
      project=$(sed -n 's/^schemaProject = "\(.*\)"$/\1/p' "$here/site.toml")
      model=$(uv run --project "$root/${project:-.}" --frozen --quiet python -I -c '
import importlib.util, pathlib, sys
package, _, inner = sys.argv[1][4:].partition("/")
spec = importlib.util.find_spec(package)
if spec is None or not spec.submodule_search_locations:
    sys.exit(f"prepare.sh: site.toml names the schema {sys.argv[1]}, and the environment of {sys.argv[2]} holds no package {package}")
print(pathlib.Path(list(spec.submodule_search_locations)[0], inner))' "$named" "${project:-the root}") ;;
    *) model="$root/$named" ;;
  esac
  [ -f "$model" ] || { echo "prepare.sh: site.toml names the schema $named, which is no file" >&2; exit 1; }
  gendoc "$model"
  echo "$named" >"$out/schema/source.txt"
fi
for model in ${linkml:+"$root/$linkml"/src/*/schema/*.yaml} "$root"/src/*/schema/*.yaml "$root"/.linkml/src/*/schema/*.yaml; do
  [ ! -d "$out/schema" ] || break
  name=$(basename "$model" .yaml)
  [ -f "$model" ] && [ "$(basename "${model%/schema/*}")" = "$name" ] || continue
  gendoc "$model"
  echo "${model#"$root/"}" >"$out/schema/source.txt"
done

# With no schema of its own, the repository still has the one its bundle is
# written in: the domain vocabulary in .lokf/schema/domain.yaml, on a host
# whose bundle federates others, or else LOKF core, the copy in .lokf/schema/
# that a domain vocabulary imports, or else the one in the lokf package the
# sidecar installs. core.txt holds LOKF core's version, and source.txt the
# path of the file shown, when the repository has it.
if [ ! -d "$out/schema" ]; then
  core="$root/.lokf/schema/lokf.yaml"
  for model in "$root/.lokf/schema/domain.yaml" "$core"; do
    [ -f "$model" ] || continue
    gendoc "$model"
    echo "${model#"$root/"}" >"$out/schema/source.txt"
    break
  done
  if [ ! -d "$out/schema" ]; then
    gendoc "$("${lokf[@]}" python -c 'import lokf, pathlib; print(next(pathlib.Path(lokf.__file__).parent.rglob("lokf.yaml")))')"
  fi
  if [ -f "$core" ]; then
    sed -n 's/^version: *"\{0,1\}\([^"]*\)"\{0,1\}$/\1/p' "$core" | head -1 >"$out/schema/core.txt"
  else
    "${lokf[@]}" python -c 'import importlib.metadata; print(importlib.metadata.version("lokf"))' >"$out/schema/core.txt"
  fi
fi

# The data, when site.toml names its folder: each SQLite database in it,
# served under browse/, and its Datasette metadata as metadata.json without
# the plugins' settings, which Datasette Lite never runs and which can hold a
# credential. site.toml's browseBuild command writes the data when the folder
# holds no database. Nothing else in the folder is served.
browse=$(sed -n 's/^browse = "\(.*\)"$/\1/p' "$here/site.toml")
if [ -n "$browse" ]; then
  build=$(sed -n 's/^browseBuild = "\(.*\)"$/\1/p' "$here/site.toml")
  databases() { find "$root/$browse" -maxdepth 1 -type f \( -name '*.sqlite' -o -name '*.sqlite3' -o -name '*.db' \) 2>/dev/null; }
  if [ -z "$(databases)" ]; then
    [ -n "$build" ] || { echo "prepare.sh: site.toml's browse names $browse, which holds no database, and no browseBuild writes it" >&2; exit 1; }
    echo "prepare.sh: building $browse with \`$build\`"
    (cd "$root" && bash -c "$build")
    [ -n "$(databases)" ] || { echo "prepare.sh: \`$build\` ran, but $browse still holds no database; set browse to the folder it writes" >&2; exit 1; }
  fi
  mkdir -p "$out/browse"
  "${lokf[@]}" python - "$root/$browse" "$out" "$build" <<'PY'
import json, shutil, sys
from pathlib import Path
import yaml

folder, out, build = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
names = sorted(p.name for p in folder.iterdir() if p.is_file())
files = [n for n in names if n.endswith((".sqlite", ".sqlite3", ".db"))]
for name in files:
    for journal in (f"{name}-wal", f"{name}-journal"):
        if (folder / journal).is_file() and (folder / journal).stat().st_size > 0:
            sys.exit(f"prepare.sh: {folder / journal} is not empty: a write to {name} is unfinished or still open, so a copy could be torn")
    shutil.copyfile(folder / name, out / "browse" / name)
found = [n for n in names if n in ("metadata.yaml", "metadata.yml", "metadata.json")]
if len(found) > 1:
    sys.exit(f"prepare.sh: {folder} holds {' and '.join(found)}, and Datasette reads one: keep one")
metadata = None
if found:
    metadata = yaml.safe_load((folder / found[0]).read_text(encoding="utf-8")) or {}
    def bare(part):
        return {k: v for k, v in part.items() if k != "plugins"} if isinstance(part, dict) else part
    metadata = bare(metadata)
    if isinstance(metadata.get("databases"), dict):
        metadata["databases"] = {name: bare(db) for name, db in metadata["databases"].items()}
        for db in metadata["databases"].values():
            if isinstance(db, dict) and isinstance(db.get("tables"), dict):
                db["tables"] = {name: bare(table) for name, table in db["tables"].items()}
    (out / "browse" / "metadata.json").write_text(json.dumps(metadata) + "\n", encoding="utf-8")
listed = []
for name in files:
    stem = name.rsplit(".", 1)[0]
    about = ((metadata or {}).get("databases") or {}).get(stem) or {}
    size = (folder / name).stat().st_size
    listed.append({"file": name, "name": stem, "title": str(about.get("title") or stem), "description": str(about.get("description") or ""),
                   "size": f"{size / 1e6:.1f} MB" if size >= 1e6 else f"{max(1, round(size / 1e3))} kB"})
(out / "browse.json").write_text(json.dumps({"databases": listed, "metadata": bool(found), "build": build}) + "\n", encoding="utf-8")
PY
fi

report="$root/.lokf/scripts/knowledge-report.sh"
bash "$report" --root "$root" labels >"$out/labels.txt"
bash "$report" --root "$root" health >"$out/health.txt"
git -C "$root" tag --list >"$out/tags.txt" 2>/dev/null || : >"$out/tags.txt"

echo "prepare.sh: wrote $(find "$out/knowledge" -type f | wc -l) export files and $(wc -l <"$out/labels.txt") labels to $out"
