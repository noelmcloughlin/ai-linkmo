"""Fetch the Cypher export that ai-atlas-nexus commits, pinned to the installed version.

Upstream regenerates ``graph_export/cypher/ai-risk-ontology.cypher`` on every merge and tags
each release, so the artefact at the tag of the installed ``ai-atlas-nexus`` package is built
from the same packaged data this project serves. Fetching it leaves no schema-specific graph
code here. The artefact describes the packaged data only; nothing under ``byo/data`` is in it.

The saved file starts with three ``//`` comment lines recording where it came from, which
version it belongs to and when it was fetched. Cypher treats ``//`` as a line comment, so
``cypher-shell`` loads the file unchanged. A later run reads only those lines, and downloads
again only when the recorded version differs from the installed one or ``--force`` is given.

Usage::

    uv run python scripts/fetch_cypher.py [output] [--version 1.2.5] [--force]

``lib/api/handlers.graph`` calls :func:`fetch` directly when asked for the Cypher export.
"""
from __future__ import annotations

import argparse
import datetime as _dt
import importlib.metadata
import os
import shutil
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional

PACKAGE = "ai-atlas-nexus"
REPOSITORY = "IBM/ai-atlas-nexus"
ARTEFACT_PATH = "graph_export/cypher/ai-risk-ontology.cypher"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "graph" / "cypher" / "ai-risk-ontology.cypher"

VERSION_COMMENT = f"// {PACKAGE}: "
_USER_AGENT = "ai-linkmo fetch_cypher (urllib)"
_TIMEOUT_SECONDS = 120


class FetchError(Exception):
    """The artefact could not be fetched; the message says why in one sentence."""


def installed_version() -> str:
    """Return the version of the installed ai-atlas-nexus package."""
    return importlib.metadata.version(PACKAGE)


def normalise_version(version: str) -> str:
    """Return the version without a leading ``v``, so ``v1.2.5`` and ``1.2.5`` agree."""
    version = version.strip()
    return version[1:] if version.startswith("v") else version


def artefact_url(version: str) -> str:
    """Return the raw GitHub URL of the Cypher export at the release tag for ``version``."""
    return (
        f"https://raw.githubusercontent.com/{REPOSITORY}/v{normalise_version(version)}/"
        f"{ARTEFACT_PATH}"
    )


def provenance_header(url: str, version: str, fetched: Optional[_dt.date] = None) -> str:
    """Return the three comment lines written at the top of the saved file."""
    day = fetched or _dt.date.today()
    return (
        f"// source: {url}\n"
        f"{VERSION_COMMENT}{normalise_version(version)}\n"
        f"// fetched: {day.isoformat()}\n"
    )


def recorded_version(path: Path) -> Optional[str]:
    """Return the version named in ``path``'s provenance header, or None when there is none.

    Only the first few lines are read, so a stale or hand-edited file costs nothing to check.
    """
    if not path.is_file():
        return None
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for _ in range(3):
            line = handle.readline()
            if line.startswith(VERSION_COMMENT):
                return line[len(VERSION_COMMENT):].strip()
    return None


def fetch(
    version: Optional[str] = None,
    output: Path = DEFAULT_OUTPUT,
    force: bool = False,
) -> Path:
    """Download the Cypher export for ``version`` to ``output`` and return that path.

    ``version`` defaults to the installed package's. When ``output`` already records the same
    version in its header the download is skipped unless ``force`` is true. The file is written
    beside its final name and moved into place, so a failed download leaves no partial file.

    Raises :class:`FetchError` when the tag or the file does not exist upstream, when the
    network is unreachable, or when the response does not look like Cypher.
    """
    version = normalise_version(version or installed_version())
    output = Path(output)
    if not force and recorded_version(output) == version:
        return output

    url = artefact_url(version)
    request = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        response = urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            raise FetchError(
                f"No Cypher export at {url}. Check that {REPOSITORY} has a v{version} tag and "
                f"that the tag carries {ARTEFACT_PATH}."
            ) from error
        raise FetchError(f"Fetching {url} failed with HTTP {error.code}.") from error
    except urllib.error.URLError as error:
        raise FetchError(f"Could not reach {url}: {error.reason}.") from error

    output.parent.mkdir(parents=True, exist_ok=True)
    partial = output.with_name(output.name + ".part")
    with response, partial.open("wb") as handle:
        first = response.read(65536)
        if not (first.startswith(b"MERGE") or first.startswith(b"//")):
            partial.unlink(missing_ok=True)
            raise FetchError(f"The response from {url} does not start like a Cypher file.")
        handle.write(provenance_header(url, version).encode("utf-8"))
        handle.write(first)
        shutil.copyfileobj(response, handle)
    os.replace(partial, output)
    return output


def main(argv: Optional[list[str]] = None) -> int:
    """Command-line entry point. Returns the process exit code."""
    parser = argparse.ArgumentParser(
        description="Fetch the Cypher export ai-atlas-nexus commits for the installed version."
    )
    parser.add_argument(
        "output",
        nargs="?",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"where to save the file (default: {DEFAULT_OUTPUT.relative_to(PROJECT_ROOT)})",
    )
    parser.add_argument(
        "--version",
        default=None,
        help="release tag to fetch, with or without the leading v (default: the installed version)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="download again even when the file already records the same version",
    )
    args = parser.parse_args(argv)

    version = normalise_version(args.version or installed_version())
    try:
        path = fetch(version=version, output=args.output, force=args.force)
    except FetchError as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    print(f"{PACKAGE} {version} Cypher export at {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
