#!/usr/bin/env bash
# Builds the knowledge website. Hugo and Pagefind come from PyPI through uv,
# at the versions and hashes uv.lock holds, so the build needs bash, git and
# uv, and no Node.js. Behind a package mirror, scripts/uv-env.sh installs the
# same files from the index uv reads.
#
#   scripts/build.sh           dist/, with its raw HTML cleaned, the search
#                              index, and every link between its pages checked
#   scripts/build.sh serve     http://localhost:1313/<the site's path>/,
#                              rebuilt as you edit, with the search index of
#                              the moment it started
#   scripts/build.sh preview   the site as it will be published, at
#                              http://localhost:1313/
#
# PORT=<n> moves serve and preview off port 1313. serve shows raw HTML as
# written and leaves the security policy off, since Hugo's reload script
# would break it.
set -euo pipefail
here=$(cd "$(dirname "$0")/.." && pwd)
cd "$here"
mode=$(scripts/uv-env.sh "$here")
tool=(uv run --project "$here" "$mode" --quiet)
# hugo.toml is the same on every site, and site.toml holds this repository's
# own values, read second so that they win.
# shellcheck disable=SC2054 # one --config value: Hugo takes the files as a comma-separated list
port=${PORT:-1313}

if grep -qE '<(REPO|PROJ|SITE)_[A-Z]+>' site.toml; then
  echo "build.sh: site.toml still holds a <PLACEHOLDER>; give it this repository's values first" >&2
  exit 1
fi

scripts/prepare.sh
config=hugo.toml,site.toml
# The mounts of a source folder, which prepare.sh writes when site.toml names one.
[ -f generated/source.toml ] && config=$config,generated/source.toml
hugo=("${tool[@]}" hugo --config "$config")
# Links to repository files name the commit the site was built from, or the
# branch where there is no git.
if ref=$(git -C "$here/.." rev-parse HEAD 2>/dev/null); then export HUGO_PARAMS_REF=$ref; fi
# A build never publishes static/pagefind, the preview server's index.
rm -rf static/pagefind .preview

case "${1:-}" in
  "")
    # --cleanDestinationDir removes what an earlier build left in dist/. It is
    # not set in hugo.toml, where a running preview server would act on it too.
    # The mark, new each build, sets off each page's raw HTML for clean-html.py.
    mark=$("${tool[@]}" python -c 'import secrets; print(secrets.token_hex(12))')
    HUGO_PARAMS_RAWMARK=$mark "${hugo[@]}" --gc --minify --cleanDestinationDir
    "${tool[@]}" python scripts/clean-html.py dist "$mark"
    "${tool[@]}" python -m pagefind --site dist
    "${tool[@]}" python scripts/check-links.py dist "$("${hugo[@]}" config | sed -n 's/^baseurl = //p' | tr -d "\"'")"
    ;;
  serve)
    # Pagefind indexes built pages, so one build gives the server an index.
    "${hugo[@]}" --quiet -d .preview
    "${tool[@]}" python -m pagefind --site .preview --output-path static/pagefind
    rm -rf .preview
    # In memory, so the server never writes over a build in dist/.
    exec "${hugo[@]}" server --disableFastRender --renderToMemory --port "$port"
    ;;
  preview)
    mark=$("${tool[@]}" python -c 'import secrets; print(secrets.token_hex(12))')
    HUGO_PARAMS_RAWMARK=$mark "${hugo[@]}" --gc --minify -d .preview --baseURL "http://localhost:$port/"
    "${tool[@]}" python scripts/clean-html.py .preview "$mark"
    "${tool[@]}" python -m pagefind --site .preview
    exec "${tool[@]}" python -m http.server "$port" --bind 127.0.0.1 --directory .preview
    ;;
  *)
    echo "usage: scripts/build.sh [serve|preview]" >&2
    exit 2
    ;;
esac
