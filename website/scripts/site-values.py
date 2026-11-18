"""Prints the values of site.toml that prepare.sh reads, as Hugo reads them.

    python scripts/site-values.py <site.toml>

Prints `name=value` for each [params] key in KEYS that the file sets. Exits
on a file that is not TOML, two keys that differ only in case (Hugo reads
them as one), and a value that is not a string or holds a control
character, a line break among them.
"""

from __future__ import annotations

import sys
import tomllib
import unicodedata

KEYS = ("repo", "branch", "source", "linkml", "schema", "schemaProject", "browse", "browseBuild")


def main(path: str) -> int:
    try:
        with open(path, "rb") as file:
            params = tomllib.load(file).get("params", {})
    except (OSError, tomllib.TOMLDecodeError) as error:
        sys.exit(f"site-values: {path} cannot be read as TOML: {error}")
    if not isinstance(params, dict):
        sys.exit(f"site-values: {path} sets params to a value, where a [params] table is expected")
    lower: dict[str, str] = {}
    for key in params:
        if key.lower() in lower:
            sys.exit(f"site-values: {path} sets both {lower[key.lower()]} and {key}, which Hugo reads as one key: keep one")
        lower[key.lower()] = key
    for name in KEYS:
        if name.lower() not in lower:
            continue
        value = params[lower[name.lower()]]
        if not isinstance(value, str):
            sys.exit(f"site-values: {path} sets {name} to a value that is not a string")
        if any(unicodedata.category(char) == "Cc" for char in value):
            sys.exit(f"site-values: {path} sets {name} to a value that holds a line break or another control character")
        print(f"{name}={value}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
