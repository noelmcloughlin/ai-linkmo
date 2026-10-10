"""Full-text search over the store, through linkml-store's trigram index.

``just index-store`` builds the index with ``index_database`` and ``GET /search``, which is
also ``./ai search``, queries it with ``search``. A scope is an exposed class together with
every class below it, each stored as its own collection (see ``lib/store/loader.py``), so
``control`` covers RiskControl and Action, and no scope covers every exposed class at once.

How linkml-store keeps the index, as read from its source and checked against the store.
The simple indexer hashes the trigrams of a record's text into a vector of 1000 counts, and
``Collection.attach_indexer`` writes those vectors into a shadow table in the same DuckDB
file, ``internal__index__<collection>__simple``, which holds every column of the record plus
``__index__``, with the indexer's settings in a second table ending in ``__metadata``. The
index therefore outlives the process, and a database reattached from the file finds it under
the default index name ``simple``. Two consequences shape the code here. A second
``attach_indexer`` in a fresh process appends a duplicate set of rows, because its replace
step only fires when the induced index class is already in the schema, so ``index_database``
drops the two tables before indexing. And ``Collection.search`` reads every vector back
through a new DuckDB connection on each call, which measured 7.7 s across the 25 collections
of the packaged data, so ``search`` reads a collection's vectors once per process, keeps them
until the file changes, and ranks with the indexer's own ``search`` method, which took 12 ms
for the 630 risks.

The text indexed is ``{{ id }} {{ name }} {{ description }}`` rather than the whole record.
Measured on the risks, the whole record ranked ``eticas-input-output-logging`` above
``atlas-toxic-output`` for the query "toxic output", because the reference lists and dates
dilute the trigrams; the three text slots rank it first with twice the margin. A query is
vectorised the same way whichever text was indexed.

A collection whose index is missing makes the search a 409 that names the collections and
the recipe. Building the index on request would take seconds per collection inside an API
call (4.8 s for the risks), and the classes linkml-store induces for the shadow tables would
land in the ``SchemaView`` that ``load_exposure`` and ``/schemaview`` share.
"""

from __future__ import annotations

import math
import time
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Iterable

import numpy as np
from fastapi import HTTPException

from lib.store.loader import DATA_DIR, collection_name, database_path, open_database, widen_duckdb_types

INDEX_NAME = "simple"
INDEX_TEXT = "{{ id }} {{ name }} {{ description }}"
DEFAULT_LIMIT = 20


def indexer():
    """The indexer every collection is indexed with. Its name is the one a reattached
    database looks the shadow table up under."""
    from linkml_store.index import get_indexer

    return get_indexer(INDEX_NAME, text_template=INDEX_TEXT)


def index_table(collection) -> str:
    """The shadow table linkml-store keeps this collection's index in."""
    return collection.get_index_collection_name(indexer())


def tables(database) -> frozenset[str]:
    """Every table in the file. ``list_collection_names`` lists the schema's classes
    instead once a schema view is set, so it cannot say which classes hold records."""
    rows = database.execute_sql("select table_name from information_schema.tables").rows
    return frozenset(row["table_name"] for row in rows)


def scope_classes(scope: str | None) -> list[str]:
    """The classes a scope covers, or those of every exposed class when ``scope`` is None.

    Each class is listed once, in exposure order with its descendants after it. An unknown
    scope is a 422.
    """
    from lib.api.exposure import load_exposure

    exposure = load_exposure()
    if scope is None:
        roots = [exposed.name for exposed in exposure.classes.values()]
    else:
        exposed = exposure.by_scope.get(scope)
        if exposed is None:
            raise HTTPException(
                status_code=422,
                detail=f"{scope} is not a scope; the scopes are {', '.join(sorted(exposure.by_scope))}.",
            )
        roots = [exposed.name]
    classes: list[str] = []
    for root in roots:
        for name in [root, *exposure.schema_view.class_descendants(root)]:
            if name not in classes:
                classes.append(name)
    return classes


def _collections(database, present: frozenset[str], classes: Iterable[str]) -> list[tuple[str, Any]]:
    """The collection of each class that has a table, paired with the class name.

    The class is passed as the collection's type so that a collection whose table is not
    named after it, ``GroupRecords`` for ``Group``, still knows its identifier slot.
    """
    found = []
    for class_name in classes:
        alias = collection_name(class_name)
        if alias in present:
            found.append((class_name, database.get_collection(alias, type=class_name)))
    return found


@dataclass
class _Loaded:
    """What one process keeps of one database file, dropped when the file changes."""

    stamp: tuple[int, int]
    tables: frozenset[str]
    # Collection alias to its (id, vector) pairs, read on the first search that needs them.
    vectors: dict[str, list[tuple[str, np.ndarray]]] = field(default_factory=dict)
    # Collection alias to its records by id, with null columns left out, read the same way.
    records: dict[str, dict[str, dict[str, Any]]] = field(default_factory=dict)


_LOADED: dict[Path, _Loaded] = {}


@lru_cache(maxsize=4)
def _database(byod: bool, data_dir: Path):
    return open_database(byod, data_dir)


def _loaded(byod: bool, data_dir: Path) -> tuple[Any, _Loaded]:
    """The attached database and what this process holds of it, checked against the file.

    The file's modification time and size change whenever ``just load-store`` or ``just
    index-store`` writes it, which is when the vectors and records held here go stale.
    """
    path = database_path(byod, data_dir)
    try:
        database = _database(byod, data_dir)
        stat = path.stat()
    except FileNotFoundError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    stamp = (stat.st_mtime_ns, stat.st_size)
    loaded = _LOADED.get(path)
    if loaded is None or loaded.stamp != stamp:
        loaded = _Loaded(stamp=stamp, tables=tables(database))
        _LOADED[path] = loaded
    return database, loaded


def _vectors(database, loaded: _Loaded, collection) -> list[tuple[str, np.ndarray]]:
    if collection.alias not in loaded.vectors:
        id_field = collection.identifier_attribute_name
        sql = f'select "{id_field}", "{indexer().index_field}" from "{index_table(collection)}"'
        rows = database.execute_sql(sql).rows
        loaded.vectors[collection.alias] = [
            (row[id_field], np.asarray(row[indexer().index_field], dtype=float)) for row in rows
        ]
    return loaded.vectors[collection.alias]


def _records(loaded: _Loaded, collection) -> dict[str, dict[str, Any]]:
    if collection.alias not in loaded.records:
        id_field = collection.identifier_attribute_name
        loaded.records[collection.alias] = {
            row[id_field]: {key: value for key, value in row.items() if value is not None}
            for row in collection.find({}, limit=-1).rows
        }
    return loaded.records[collection.alias]


def search(
    q: str,
    *,
    byod: bool = False,
    scope: str | None = None,
    limit: int = 20,
    data_dir: Path = DATA_DIR,
) -> dict[str, Any]:
    """The records whose text is nearest to ``q``, best first, across the scope's classes.

    Each item is the record with ``score``, the cosine similarity of the trigram vectors,
    and ``type``, its class, which is also what the record's own ``type`` slot says where
    the class has one. The classes are searched one by one, each for its ``limit`` best,
    and the lists are merged and cut to ``limit``. The route hands over None for a query
    parameter the client left out, so None means the default here.
    """
    limit = DEFAULT_LIMIT if limit is None else limit
    byod = bool(byod)
    if limit < 1:
        raise HTTPException(status_code=422, detail="limit must be at least 1.")
    ranker = indexer()
    if not np.any(ranker.text_to_vector(q or "")):
        raise HTTPException(
            status_code=422, detail="q has no trigram to search with; give at least three characters."
        )
    classes = scope_classes(scope)
    database, loaded = _loaded(byod, data_dir)
    targets = _collections(database, loaded.tables, classes)
    unindexed = [name for name, collection in targets if index_table(collection) not in loaded.tables]
    if unindexed:
        raise HTTPException(
            status_code=409,
            detail=f"No search index for {', '.join(unindexed)}; run `just index-store`.",
        )
    hits: list[tuple[float, str, Any, str]] = []
    for class_name, collection in targets:
        for score, record_id in ranker.search(q, _vectors(database, loaded, collection), limit=limit):
            # A record whose indexed text was empty has a zero vector and no similarity.
            if not math.isnan(score):
                hits.append((float(score), class_name, collection, record_id))
    hits.sort(key=lambda hit: hit[0], reverse=True)
    items = []
    for score, class_name, collection, record_id in hits[:limit]:
        record = _records(loaded, collection).get(record_id)
        if record is not None:
            items.append({**record, "score": score, "type": class_name})
    return {"items": items, "count": len(items), "query": q}


@dataclass(frozen=True)
class IndexedCollection:
    """One collection's indexing, for the report ``just index-store`` prints."""

    class_name: str
    rows: int
    seconds: float


def _forget_induced_classes(view) -> None:
    """Remove the classes linkml-store induced for the shadow tables from the schema view.

    Inducing them is how it types a shadow table, but the view is the one the whole process
    shares, and a class induced from one database's rows would type the other database's
    table too, so each database starts from the schema alone and leaves it that way.
    """
    induced = [name for name in view.schema.classes if name.startswith("internal__")]
    for name in induced:
        del view.schema.classes[name]
    if induced:
        view.set_modified()


def index_database(
    byod: bool, *, data_dir: Path = DATA_DIR, scopes: Iterable[str] | None = None
) -> list[IndexedCollection]:
    """Index every collection the scopes cover, or every exposed class's, and say how long each took.

    A collection's two index tables are dropped first, so that running this again replaces
    the index instead of doubling it. The integer columns are widened before anything is
    written because the shadow table copies every column of the record, and
    ``numParameters`` does not fit the 32-bit column linkml-store would give it (see the
    loader). Raises ``FileNotFoundError`` when the store has not been built.
    """
    from sqlalchemy import text

    widen_duckdb_types()
    database = open_database(byod, data_dir)
    if scopes is None:
        classes = scope_classes(None)
    else:
        classes = []
        for scope in scopes:
            classes += [name for name in scope_classes(scope) if name not in classes]
    report = []
    _forget_induced_classes(database.schema_view)
    try:
        for class_name, collection in _collections(database, tables(database), classes):
            started = time.monotonic()
            shadow = index_table(collection)
            with database.engine.begin() as connection:
                for table in (shadow, f"{shadow}__metadata"):
                    connection.execute(text(f'drop table if exists "{table}"'))
            collection.attach_indexer(indexer())
            report.append(IndexedCollection(class_name, collection.size(), time.monotonic() - started))
    finally:
        _forget_induced_classes(database.schema_view)
        _LOADED.pop(database_path(byod, data_dir), None)
    return report
