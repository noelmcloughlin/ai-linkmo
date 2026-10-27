"""Operations written by hand, beside the class listings the kernels generate.

A function here becomes an operation when the exposure file's overlay binds a path to it
with ``operationId: hand.<function name>``. The API registers it with the parameters the
overlay declares, and the command line offers it as a command with the same parameters.
The function may return any JSON-like value, pydantic models included, and may raise
``QueryError`` to answer with an HTTP status.

The linkmo template created this file once and never overwrites it: it is the place for
this project's own logic, such as lookups across classes that the schema cannot express.

ai-linkmo's operations are in ``lib/api/handlers.py``, beside the related-risk lookups
they share with the listings, so the exposure file's seven paths bind to the names this
module imports from there. ``summary`` is the template's, and no path binds it.
"""

from __future__ import annotations

from typing import Any

from . import atlas  # noqa: F401  # puts ai-linkmo's lib on the path
from .exposure import load_exposure
from .handlers import QueryError, query_class

from lib.api.handlers import (  # noqa: E402, F401
    ares,
    byo,
    byo_put,
    crosswalk,
    graph,
    inference,
    schemaview,
    search,
)


def summary(scope: str | None = None) -> dict[str, Any]:
    """The number of records of each exposed class, or of one class named by its command."""
    exposure = load_exposure()
    if scope is not None:
        if scope not in exposure.by_scope:
            raise QueryError(404, f"No class is exposed as {scope}")
        classes = [exposure.by_scope[scope]]
    else:
        classes = list(exposure.classes.values())
    return {exposed.scope: query_class(exposed.name)["count"] for exposed in classes}
