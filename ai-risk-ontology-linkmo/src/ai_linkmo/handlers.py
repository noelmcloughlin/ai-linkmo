"""The one handler behind every class listing, and the serialisation both kernels share.

The API kernel routes each class listing here, and the command line calls it directly in
local mode, so both kernels give the same answer by construction. A listing is the
envelope ``{"items", "count", "validation_errors"}``. Giving the identifier of the class
returns ``{"item": record}`` instead, with ``null`` when no record has it, unless a
parameter the exposure file adds is given too: then the question is the data source's
own, such as the records related to that one, and the answer is a listing.
"""

from __future__ import annotations

import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel

from .exposure import load_exposure
from .sources import UnknownFilter, load_source


class QueryError(Exception):
    """A question the handler cannot answer, with the HTTP status that says why."""

    def __init__(self, status: int, detail: str):
        super().__init__(detail)
        self.status = status
        self.detail = detail


def jsonable(value: Any) -> Any:
    """A value with dates, enums and models turned into what JSON holds."""
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json", by_alias=True, exclude_none=True)
    if isinstance(value, dict):
        return {str(k): jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(v) for v in value]
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, (datetime.date, datetime.datetime)):
        return value.isoformat()
    return value


def query_class(class_name: str, **params: Any) -> dict[str, Any]:
    """List, filter or fetch the records of one exposed class.

    ``params`` are slot names of the class, plus any parameter the exposure file adds,
    with the value a record must carry. A parameter left as None is not a filter.
    """
    exposed = load_exposure().classes.get(class_name)
    if exposed is None:
        raise QueryError(404, f"{class_name} is not exposed")
    unknown = sorted(set(params) - {p.name for p in exposed.parameters})
    if unknown:
        raise QueryError(422, f"{class_name} has no parameter named {', '.join(unknown)}")
    given = {name: value for name, value in params.items() if value is not None}
    source = load_source()
    try:
        records = source.query(class_name, **given)
    except UnknownFilter as exc:
        raise QueryError(422, str(exc)) from exc
    added = {p.name for p in exposed.parameters if not p.slot}
    if exposed.identifier is not None and exposed.identifier in given and not added & set(given):
        return {"item": jsonable(records[0]) if records else None}
    items = [jsonable(record) for record in records]
    errors_for = getattr(source, "errors_for", None)
    errors = errors_for(class_name) if callable(errors_for) else []
    return {"items": items, "count": len(items), "validation_errors": errors}
