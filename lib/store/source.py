"""Choose where the class listings read their records: the DuckDB store or the library.

``AI_LINKMO_DATA_SOURCE`` names the source. ``store`` reads the DuckDB files that
``just load-store`` builds through linkml-store, which answers a filter in milliseconds.
``library`` keeps the ``AIAtlasNexus`` instance the project started with, which re-parses
the YAML on first use. ``auto``, the default, is the store when its files exist and the
library otherwise, so a checkout that has never run ``just load-store`` still works.

Only the plain listings go through here: list, filter and fetch by id. The related-risk
lookups, crosswalks, inference, SHACL and SPARQL stay on the library whichever source is
chosen, because linkml-store has no join or traversal to carry them.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Any

from lib.store.loader import collection_name, database_path

SOURCES = ("auto", "store", "library")


def configured_source() -> str:
    """The source named by the environment, with ``auto`` resolved to a real one."""
    name = os.getenv("AI_LINKMO_DATA_SOURCE", "auto").strip().lower() or "auto"
    if name not in SOURCES:
        raise ValueError(f"AI_LINKMO_DATA_SOURCE must be one of {', '.join(SOURCES)}, not {name!r}")
    if name == "auto":
        return "store" if database_path(False).exists() else "library"
    return name


def using_store() -> bool:
    return configured_source() == "store"


@lru_cache(maxsize=2)
def store_database(byod: bool):
    """The attached store database for ``byod``, opened once per process."""
    from lib.store.loader import open_database

    return open_database(byod)


def reset_store_cache() -> None:
    """Forget the attached databases, after the store is rebuilt or the byo data changes."""
    store_database.cache_clear()
    _tables.cache_clear()


def store_where(filters: dict[str, Any], multivalued: set[str]) -> dict[str, Any]:
    """Translate slot filters into a linkml-store ``where`` mapping.

    A single-valued slot is an equality. A multivalued slot holds a list, which DuckDB
    cannot compare with a scalar, so it becomes ``$contains``, which linkml-store renders as
    ``ARRAY_CONTAINS``. That is the same meaning the library's filter has: a record matches
    when its list holds the value.
    """
    where: dict[str, Any] = {}
    for name, value in filters.items():
        where[name] = {"$contains": value} if name in multivalued else value
    return where


@lru_cache(maxsize=2)
def _tables(byod: bool) -> frozenset[str]:
    """The tables the DuckDB file holds; ``list_collection_names`` lists schema classes too."""
    result = store_database(byod).execute_sql("select table_name from information_schema.tables")
    return frozenset(row["table_name"] for row in result.rows)


def class_collections(byod: bool, class_name: str) -> list[tuple[str, Any]]:
    """The classes below ``class_name`` that have a collection, each with its collection.

    The store keeps one collection per concrete class, so a scope bound to a class with
    subclasses, such as ``Group`` or ``RiskControl``, reads all of them.
    """
    database = store_database(byod)
    wanted = dict.fromkeys([class_name, *database.schema_view.class_descendants(class_name)])
    return [
        (name, database.get_collection(collection_name(name)))
        for name in wanted
        if collection_name(name) in _tables(byod)
    ]


def store_records(
    class_name: str, filters: dict[str, Any], multivalued: set[str], byod: bool
) -> list[tuple[str, dict]]:
    """Every record of ``class_name`` or a subclass matching ``filters``.

    Each record comes with the name of its own class, so the caller can build it with the
    right model: a ``RiskGroup`` row has slots a ``Group`` does not. A filter on a slot that
    one subclass lacks matches nothing there, which is what the library's match does too.
    Null columns are dropped, so the row holds only what the file said.
    """
    where = store_where(filters, multivalued)
    view = store_database(byod).schema_view
    records: list[tuple[str, dict]] = []
    for name, collection in class_collections(byod, class_name):
        columns = {slot.name for slot in view.class_induced_slots(name)}
        if not set(where) <= columns:
            continue
        for row in collection.find(where, limit=-1).rows:
            records.append((name, {k: v for k, v in row.items() if v is not None}))
    return records


def store_has_taxonomy(taxonomy: str, byod: bool) -> bool:
    """True when a taxonomy of any class carries this id, which is what the library checks."""
    for _, collection in class_collections(byod, "Taxonomy"):
        if collection.find({"id": taxonomy}).num_rows:
            return True
    return False
