"""Helpers the generated tests share: the count table, and a command line as API parameters."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Any

import yaml

TESTS_DIR = Path(__file__).resolve().parent
PROJECT_DIR = TESTS_DIR.parent


def load_cases() -> list[dict[str, Any]]:
    """The cases of tests/expected_counts.yaml, each with ``args`` and ``count``."""
    document = yaml.safe_load((TESTS_DIR / "expected_counts.yaml").read_text(encoding="utf-8")) or {}
    return list(document.get("cases") or [])


def case_id(case: dict[str, Any]) -> str:
    return " ".join(str(a) for a in case["args"])


def to_query(exposure, args: list[str]) -> tuple[str, dict[str, str]]:
    """The API path and query parameters that ask what a command line asks.

    A bare word after the command is the record's identifier, ``--name value`` is a
    filter, and ``--name`` or ``--no-name`` on a boolean slot is true or false.
    """
    scope, rest = str(args[0]), [str(a) for a in args[1:]]
    exposed = exposure.by_scope.get(scope)
    flags = {p.name for p in exposed.parameters if p.kind == "boolean"} if exposed else set()
    params: dict[str, str] = {}
    index = 0
    while index < len(rest):
        token = rest[index]
        if token.startswith("--no-") and token[5:] in flags:
            params[token[5:]] = "false"
            index += 1
        elif token.startswith("--") and token[2:] in flags:
            params[token[2:]] = "true"
            index += 1
        elif token.startswith("--") and index + 1 < len(rest) and not rest[index + 1].startswith("--"):
            params[token[2:]] = rest[index + 1]
            index += 2
        elif token.startswith("--"):
            # An option without a value is a flag the exposure file added.
            params[token[2:]] = "true"
            index += 1
        else:
            params[exposed.identifier if exposed and exposed.identifier else "id"] = token
            index += 1
    return f"/{scope}", params


def load_script(name: str):
    """A module of scripts/, loaded by path so that no other package named scripts shadows it."""
    path = PROJECT_DIR / "scripts" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(f"linkmo_script_{name}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
