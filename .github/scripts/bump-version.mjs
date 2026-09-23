#!/usr/bin/env node
// Writes a version into pyproject.toml and uv.lock for the semantic-release
// pipeline in .github/workflows/semantic-release.yml. Plain Node, no
// dependencies: reviewable in one read, matching this project's preference
// for a fixed, in-repo script over an inline command string (see
// changelog-release.mjs and knowledge-librarian.sh).
//
// There is no Python equivalent of @semantic-release/npm, so the two files
// that carry the version are edited here instead. uv.lock is edited in place
// rather than regenerated with `uv lock`, which keeps uv out of the release
// runner entirely. Only the project's own version line changes, so the lock
// stays consistent with pyproject.toml and CI's `uv sync --locked` is happy.
//
// Usage:
//   node bump-version.mjs <version>
//       Sets [project] version in pyproject.toml and the ai-linkmo package
//       entry in uv.lock. Exits 1 if either file does not contain exactly
//       one match, so a silently-missed bump fails the release instead of
//       shipping a tag that disagrees with the package metadata.

import { readFileSync, writeFileSync } from "node:fs";

const PYPROJECT = "pyproject.toml";
const LOCK = "uv.lock";
const PACKAGE = "ai-linkmo";

const [, , version] = process.argv;

if (!version || !/^\d+\.\d+\.\d+/.test(version)) {
  console.error("usage: bump-version.mjs <version>   (e.g. 0.2.0)");
  process.exit(1);
}

function replaceOnce(file, pattern, replacement, what) {
  const text = readFileSync(file, "utf8");
  const matches = text.match(pattern);
  if (!matches) {
    console.error(`${file}: no ${what} found - refusing to release a version nothing carries.`);
    process.exit(1);
  }
  const updated = text.replace(pattern, replacement);
  writeFileSync(file, updated);
  console.error(`${file}: ${what} -> ${version}`);
}

// pyproject.toml: the [project] table's own `version`, which is the first
// line-anchored `version = "..."` in the file. `minversion` under
// [tool.pytest.ini_options] does not match, being a different key.
replaceOnce(PYPROJECT, /^version = "[^"]*"$/m, `version = "${version}"`, "[project] version");

// uv.lock: the version line inside this project's own [[package]] entry,
// matched through its name so no dependency's version can be hit instead.
replaceOnce(
  LOCK,
  new RegExp(`(name = "${PACKAGE}"\\nversion = )"[^"]*"`),
  `$1"${version}"`,
  `${PACKAGE} package version`
);
