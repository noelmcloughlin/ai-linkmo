"""Print answers as JSON and errors as plain text, for the command line.

Answers go to stdout as one line of JSON, so that a pipe into ``jq`` works, or indented on
a terminal and with ``--pretty``. Errors go to stderr, so they never corrupt that JSON.
"""

from __future__ import annotations

import datetime
import json
import sys
from typing import Any


def _default(value: Any) -> Any:
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    raise TypeError(f"{type(value).__name__} is not JSON serialisable")


def to_json(result: Any, pretty: bool = False) -> str:
    return json.dumps(result, indent=2 if pretty else None, ensure_ascii=False, default=_default)


def count_of(result: Any) -> Any:
    """The number a ``--count`` prints: the listing's count, or 1 or 0 for one record."""
    if isinstance(result, dict) and "count" in result:
        return result["count"]
    if isinstance(result, dict) and "item" in result:
        return 1 if result["item"] is not None else 0
    if isinstance(result, list):
        return len(result)
    return result


def display_result(result: Any, count_only: bool = False, pretty: bool = False) -> None:
    print(count_of(result) if count_only else to_json(result, pretty or sys.stdout.isatty()))


def display_error(title: str, message: str) -> None:
    print(f"{title}: {message}", file=sys.stderr)
