"""Build SQLite databases from the schema and the data, for browsing in Datasette.

Datasette turns any SQLite file into table and row pages with filters, facets, labelled
foreign-key links, the links from other tables on each row page, full-text search, a JSON
API and CSV export. What it needs is a database whose tables and foreign keys follow the
schema. This module makes one from the schema and the records, and names no class or slot
of its own, so it serves any LinkML schema whose records come grouped by class.

The tables come from linkml's ``SQLTableGenerator``, the Python side of ``gen-sqltables``.
It makes one table per class, abstract classes and mixins included with their inherited
columns, a foreign key for each single-valued reference to the table of the slot's declared
range, and a link table for each multivalued slot. linkml-sqldb, the loader written for
that DDL, failed four different ways on the ontology schema when it was measured, so the
rows are written here from the same records the DuckDB store loads.

The rule the loader has to respect is that a foreign key points at the table of the slot's
declared range, which is often an abstract parent of the record's own class. So each
record is written to its class table and to the table of every ancestor that shares its
identifier, and each multivalued slot to the link table of each of those classes. Every
table then holds the whole extent of its class, and a reference resolves whichever class
its range names. Everything is written in one transaction with ``executemany``.

The DDL also has a link table for every multivalued slot of every class, and most stay
empty. Those are dropped once the rows are in (see ``drop_empty_link_tables``), while every
class table stays so that every foreign key keeps its parent.

The databases are build artefacts. ``just build-browse`` writes them under
``lib/browse/data/`` with the Datasette metadata beside them (see ``metadata.py``), and
``just browse`` serves that directory.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

from lib.store.loader import DATABASES

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "lib" / "browse" / "data"
DDL_FILE = "schema.sql"

# The class LinkML provides as an open range, which no table can stand for.
LINKML_ANY = "https://w3id.org/linkml/Any"

# Slots whose URI says they hold a record's label or its description. The first one a class
# has is its label column in Datasette, and both are indexed for full-text search. They are
# matched by URI rather than by name so that any schema using these vocabularies is served.
LABEL_URIS = frozenset(
    {
        "http://schema.org/name",
        "https://schema.org/name",
        "http://www.w3.org/2000/01/rdf-schema#label",
        "http://www.w3.org/2004/02/skos/core#prefLabel",
        "http://purl.org/dc/terms/title",
    }
)
DESCRIPTION_URIS = frozenset(
    {
        "http://schema.org/description",
        "https://schema.org/description",
        "http://purl.org/dc/terms/description",
        "http://www.w3.org/2004/02/skos/core#definition",
        "http://www.w3.org/2000/01/rdf-schema#comment",
    }
)


# What each database holds, for its page in Datasette.
DATABASE_DESCRIPTIONS = {
    False: "The packaged data.",
    True: "The packaged data with the bring-your-own files under byo/data added.",
}


def database_path(byod: bool, data_dir: Path = DATA_DIR) -> Path:
    """The SQLite file for ``byod``, named like the DuckDB store's database."""
    return data_dir / f"{DATABASES[byod]}.sqlite"


def quote(name: str) -> str:
    """An SQL identifier in double quotes, since a class may be named after a keyword."""
    return '"' + name.replace('"', '""') + '"'


def table_schema(view: SchemaView) -> SchemaDefinition:
    """The schema the tables are generated from: the source schema with two changes.

    ``view`` must have its imports merged, as ``lib.api.exposure.schema_view()`` does. A
    slot whose range is ``linkml:Any`` is stored as text. The generator would otherwise make
    it a foreign key to an ``Any`` table that never holds a row, so every value would be a
    dead link. And a tree root holds the records rather than being one, so it gets no table;
    otherwise every class it holds would carry an empty foreign key column back to it. A
    class that something still refers to keeps its table.
    """
    schema = copy.deepcopy(view.schema)
    classes = view.all_classes()
    open_ranges = {
        name for name, cls in classes.items() if view.get_uri(cls, expand=True) == LINKML_ANY
    }
    definitions = list(schema.slots.values())
    for cls in schema.classes.values():
        definitions += list(cls.slot_usage.values()) + list(cls.attributes.values())
    for definition in definitions:
        if definition.range in open_ranges:
            definition.range = "string"
    referenced = {definition.range for definition in definitions}
    for cls in schema.classes.values():
        referenced.update([cls.is_a, *cls.mixins])
    roots = {name for name, cls in classes.items() if cls.tree_root}
    for name in (open_ranges | roots) - referenced:
        del schema.classes[name]
    return schema


def schema_digest(view: SchemaView) -> str:
    """A digest of everything the DDL depends on: the schema files, linkml, and this module.

    The files are hashed rather than the merged schema, because ``SchemaView`` fills in
    fields of the merged schema as it is read, so two dumps of it in one process differ.
    """
    digest = hashlib.sha256(f"linkml {importlib.metadata.version('linkml')}".encode())
    sources = {Path(s.source_file) for s in view.schema_map.values() if s.source_file}
    for path in [*sorted(sources), Path(__file__)]:
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def generate_ddl(view: SchemaView, cache: Path | None = None) -> str:
    """The SQLite DDL for the schema, written by linkml's ``SQLTableGenerator``.

    Generating it takes about ten seconds for a schema of a hundred classes, nearly all of
    it in linkml's relational transform, and the result changes only with the schema or with
    linkml. So when ``cache`` names a file, the DDL is kept there under the schema's digest
    and reused while the digest still matches.
    """
    from linkml.generators.sqltablegen import SQLTableGenerator

    if cache is None:
        return SQLTableGenerator(table_schema(view)).generate_ddl()
    header = f"-- Written by linkml's SQLTableGenerator for schema digest {schema_digest(view)}.\n"
    if cache.exists():
        cached = cache.read_text(encoding="utf-8")
        if cached.startswith(header):
            return cached
    ddl = header + SQLTableGenerator(table_schema(view)).generate_ddl()
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_text(ddl, encoding="utf-8")
    return ddl


def create_database(ddl: str) -> sqlite3.Connection:
    """An in-memory database holding every table of the DDL, all of them empty.

    The build happens in memory and ``save`` writes the result out in one step, so a failed
    build never leaves half a file behind. Most of the thousand or so tables and indexes
    stay empty, and each takes at least a page, so the pages are 1 KB rather than SQLite's
    4 KB.
    """
    connection = sqlite3.connect(":memory:")
    connection.execute("pragma page_size = 1024")
    connection.executescript(f"begin;\n{ddl}\ncommit;")
    return connection


def table_columns(connection: sqlite3.Connection) -> dict[str, list[str]]:
    """Every table of the database with its column names, in creation order."""
    names = [
        name
        for (name,) in connection.execute(
            "select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"
        )
    ]
    return {
        name: [row[1] for row in connection.execute(f"pragma table_info({quote(name)})")]
        for name in names
    }


@dataclass(frozen=True)
class Target:
    """Where one slot's values go in one class table.

    A single-valued slot is a column of the table itself, and ``key_column`` is None. A
    multivalued slot is a link table with two columns: ``key_column`` holds the record's
    identifier and ``column`` one value.
    """

    table: str
    column: str
    key_column: str | None = None


def table_plan(
    view: SchemaView, tables: dict[str, list[str]], table: str, key: str
) -> dict[str, Target]:
    """Where each slot of the class ``table`` is stored, found by the generator's naming rules.

    A slot keeps its name (or its alias) as a column. An inlined reference becomes a column
    named after the slot and the range's identifier. A multivalued slot becomes the table
    ``<class>_<singular name>``, whose first column is ``<class>_<identifier>``. A list of
    inlined objects matches none of these, because the generator stores it as a column in
    the objects' own table that points back at their owner. Such a slot is left out of the
    plan, and its values are counted as unplaced rather than loaded.
    """
    classes = view.all_classes()
    columns = set(tables[table])
    plan: dict[str, Target] = {}
    for slot in view.class_induced_slots(table):
        name = slot.alias or slot.name
        if name in columns:
            plan[slot.name] = Target(table, name)
            continue
        identifier = view.get_identifier_slot(slot.range) if slot.range in classes else None
        if identifier is not None and f"{name}_{identifier.name}" in columns:
            plan[slot.name] = Target(table, f"{name}_{identifier.name}")
            continue
        link = f"{table}_{slot.singular_name or name}"
        key_column = f"{table}_{key}"
        if link in tables and key_column in tables[link]:
            value_column = next(column for column in tables[link] if column != key_column)
            plan[slot.name] = Target(link, value_column, key_column)
    return plan


@dataclass
class LoadReport:
    """What a load wrote, what SQLite refused, and what had nowhere to go."""

    # Rows written per class table, and per link table.
    rows: Counter = field(default_factory=Counter)
    links: Counter = field(default_factory=Counter)
    # Rows SQLite refused per class table: an identifier already present, or a required
    # value missing. Both are data defects, and the build reports them.
    refused: Counter = field(default_factory=Counter)
    # Values per "Class.slot" that no column or link table could take.
    unplaced: Counter = field(default_factory=Counter)
    seconds: float = 0.0

    @property
    def records(self) -> int:
        return sum(self.rows.values())

    @property
    def link_rows(self) -> int:
        return sum(self.links.values())


def _insert(
    connection: sqlite3.Connection, table: str, columns: list[str], rows: list[tuple]
) -> int:
    """Insert ``rows`` into ``table`` and return how many SQLite kept."""
    if not rows:
        return 0
    names = ", ".join(quote(column) for column in columns)
    marks = ", ".join("?" for _ in columns)
    cursor = connection.executemany(
        f"insert or ignore into {quote(table)} ({names}) values ({marks})", rows
    )
    return cursor.rowcount


def _write_class(
    connection: sqlite3.Connection,
    view: SchemaView,
    tables: dict[str, list[str]],
    class_name: str,
    records: list[dict[str, Any]],
    report: LoadReport,
) -> None:
    """Write the records of one class to its table, its ancestors' tables and their link tables."""
    key = view.get_identifier_slot(class_name)
    if key is None:
        # Without an identifier there is nothing a link row or a reference could hold.
        report.unplaced[f"{class_name} (no identifier)"] += len(records)
        return
    for table in view.class_ancestors(class_name):
        if table not in tables:
            continue
        table_key = view.get_identifier_slot(table)
        if table_key is None or table_key.name != key.name:
            continue
        plan = table_plan(view, tables, table, key.name)
        columns: dict[str, None] = {}
        values: list[dict[str, Any]] = []
        links: dict[str, list[tuple]] = {}
        for record in records:
            row: dict[str, Any] = {}
            for name, value in record.items():
                target = plan.get(name)
                if target is None:
                    if table == class_name:
                        report.unplaced[f"{class_name}.{name}"] += 1
                    continue
                if target.key_column is None:
                    if isinstance(value, (list, dict)):
                        report.unplaced[f"{class_name}.{name}"] += 1
                        continue
                    row[target.column] = value
                    columns[target.column] = None
                    continue
                for item in value if isinstance(value, list) else [value]:
                    if isinstance(item, dict):
                        report.unplaced[f"{class_name}.{name}"] += 1
                        continue
                    links.setdefault(name, []).append((record[key.name], item))
            values.append(row)
        names = list(columns)
        kept = _insert(connection, table, names, [tuple(r.get(n) for n in names) for r in values])
        report.rows[table] += kept
        report.refused[table] += len(values) - kept
        for name, pairs in links.items():
            target = plan[name]
            report.links[target.table] += _insert(
                connection, target.table, [target.key_column, target.column], pairs
            )


def load_rows(
    connection: sqlite3.Connection, view: SchemaView, rows: dict[str, list[dict[str, Any]]]
) -> LoadReport:
    """Write every record of ``rows``, keyed by class, in one transaction."""
    started = time.perf_counter()
    tables = table_columns(connection)
    report = LoadReport()
    for class_name in sorted(rows):
        _write_class(connection, view, tables, class_name, rows[class_name], report)
    connection.commit()
    report.refused = +report.refused
    report.seconds = time.perf_counter() - started
    return report


def text_columns(view: SchemaView, table: str, columns: list[str]) -> tuple[str | None, list[str]]:
    """The label column of a class table and the columns full-text search should index.

    The label is the first slot whose URI is a label's (``LABEL_URIS``), and the indexed
    columns are the label and the first slot whose URI is a description's.
    """
    label = description = None
    for slot in view.class_induced_slots(table):
        name = slot.alias or slot.name
        if name not in columns or slot.multivalued:
            continue
        uri = view.get_uri(slot, expand=True)
        if label is None and uri in LABEL_URIS:
            label = name
        elif description is None and uri in DESCRIPTION_URIS:
            description = name
    return label, [column for column in (label, description) if column]


def enable_search(
    connection: sqlite3.Connection, view: SchemaView, report: LoadReport
) -> list[str]:
    """Index the label and description of every class table with rows, and list those tables.

    sqlite-utils creates ``<table>_fts`` with the table as its content, which is the layout
    Datasette looks for, so each of these tables gets a search box. The Porter stemmer lets
    a search for "outputs" find "output". No triggers are made, since the file is never
    written again after the build.
    """
    import sqlite_utils

    database = sqlite_utils.Database(connection)
    tables = table_columns(connection)
    searchable = []
    for table in sorted(t for t, count in report.rows.items() if count):
        _, columns = text_columns(view, table, tables[table])
        if columns:
            database.table(table).enable_fts(columns, tokenize="porter", create_triggers=False)
            searchable.append(table)
    return searchable


def drop_empty_link_tables(connection: sqlite3.Connection, view: SchemaView) -> int:
    """Drop the link tables that received no rows, and return how many there were.

    The DDL has a link table for every multivalued slot of every class, and for this schema
    nearly nine hundred of them stay empty. Datasette does some work for every table each
    time it lists a database, which with them took forty seconds and without them three. No
    foreign key ever points at a link table, so dropping one breaks no reference. Every
    class table stays, empty or not, so every foreign key keeps its parent table.
    """
    classes = view.all_classes()
    empty = [
        table
        for table in table_columns(connection)
        if table not in classes
        and connection.execute(f"select exists (select 1 from {quote(table)})").fetchone()[0] == 0
    ]
    for table in empty:
        connection.execute(f"drop table {quote(table)}")
    connection.commit()
    return len(empty)


def foreign_key_count(connection: sqlite3.Connection) -> int:
    return sum(
        len(connection.execute(f"pragma foreign_key_list({quote(table)})").fetchall())
        for table in table_columns(connection)
    )


def dangling_references(connection: sqlite3.Connection) -> Counter:
    """Count, per table and parent table, the values that name a row the parent lacks.

    SQLite reports these whether or not it enforces foreign keys. Each one is a reference
    in the data to a record the data does not contain. The keys are (table, parent) pairs.
    """
    return Counter(
        (table, parent) for table, _, parent, _ in connection.execute("pragma foreign_key_check")
    )


def save(connection: sqlite3.Connection, path: Path) -> None:
    """Write the in-memory database to ``path``, compacted, replacing any earlier file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    connection.execute("vacuum into ?", (str(path),))


@dataclass
class BuildReport:
    """One database's build: where it is, what it holds and how long it took."""

    path: Path
    load: LoadReport
    # The DDL's tables and foreign keys, and those left once the empty link tables are gone.
    ddl_tables: int
    ddl_foreign_keys: int
    tables: int
    foreign_keys: int
    searchable: list[str]
    dangling: Counter
    seconds: float


def build_database(
    byod: bool, ddl: str, view: SchemaView, data_dir: Path = DATA_DIR
) -> BuildReport:
    """Build the SQLite file for ``byod`` from ``ddl`` and the records the library loads."""
    from lib.store.loader import load_container, rows_by_class

    started = time.perf_counter()
    path = database_path(byod, data_dir)
    rows = rows_by_class(load_container(byod))
    connection = create_database(ddl)
    try:
        ddl_tables = len(table_columns(connection))
        ddl_foreign_keys = foreign_key_count(connection)
        load = load_rows(connection, view, rows)
        drop_empty_link_tables(connection, view)
        tables = len(table_columns(connection))
        foreign_keys = foreign_key_count(connection)
        dangling = dangling_references(connection)
        searchable = enable_search(connection, view, load)
        save(connection, path)
    finally:
        connection.close()
    return BuildReport(
        path=path,
        load=load,
        ddl_tables=ddl_tables,
        ddl_foreign_keys=ddl_foreign_keys,
        tables=tables,
        foreign_keys=foreign_keys,
        searchable=searchable,
        dangling=dangling,
        seconds=time.perf_counter() - started,
    )


@dataclass
class Build:
    """A whole build: the DDL step, each database, and the metadata written after them."""

    ddl_seconds: float
    databases: list[BuildReport]
    metadata: Path


def build_all(data_dir: Path = DATA_DIR, which: Iterable[bool] = (False, True)) -> Build:
    """Build the requested databases from one DDL, then the metadata for all that exist."""
    from lib.api.exposure import schema_view
    from lib.browse.metadata import write_metadata

    view = schema_view()
    started = time.perf_counter()
    ddl = generate_ddl(view, data_dir / DDL_FILE)
    ddl_seconds = time.perf_counter() - started
    reports = [build_database(byod, ddl, view, data_dir) for byod in which]
    return Build(ddl_seconds, reports, write_metadata(view, data_dir))
