"""ai-linkmo's records for the two kernels: the store or the library, with the related-risk
lookups and the bring-your-own data.

The exposure file adds ``byod`` to every class, and ``hasRelatedRisk``, ``related`` and
``related_ids`` to the classes whose records a risk relates to. The kernels pass them here
unchanged, and ``lib.api.handlers.query_records`` answers them as ai-linkmo always has.
The answer is model instances, so each record keeps its own class, or ids with
``related_ids``. The settings name this object as the project's Python data source, and
the template puts the host root, where ``lib`` is, on the path before importing it.
"""

from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from lib.api import handlers

from .handlers import QueryError


class AtlasSource:
    """Answers ``query(class_name, **filters)`` through ai-linkmo's handlers."""

    def __init__(self) -> None:
        from lib.api.library import get_ran_instance
        from lib.store.source import using_store

        # Load the library at startup, as ai-linkmo's own server did, unless the store
        # answers the listings and the library waits for a related-risk lookup.
        if not using_store():
            get_ran_instance(False)

    def query(self, class_name: str, **filters: Any) -> list[Any]:
        try:
            return handlers.query_records(class_name, **filters)
        except HTTPException as exc:
            raise QueryError(exc.status_code, str(exc.detail)) from exc
