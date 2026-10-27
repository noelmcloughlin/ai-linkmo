"""Build a SQLite database and its Datasette metadata from the schema and the records.

Datasette turns any SQLite file into table and row pages with filters, facets, labelled
foreign-key links, the links from other tables on each row page, full-text search, a JSON
API and CSV export. What it needs is a database whose tables and foreign keys follow the
schema. This module makes one from the schema and the project's data source, and names no
class or slot of its own. It is generalised from ai-linkmo's lib/browse.

The tables come from linkml's ``SQLTableGenerator``, the Python side of ``gen-sqltables``.
It makes one table per class, abstract classes and mixins included with their inherited
columns, a foreign key for each single-valued reference to the table of the slot's declared
range, and a link table for each multivalued slot.

A foreign key points at the table of the slot's declared range, which is often an abstract
parent of the record's own class. So each record is written to its class table and to the
table of every ancestor that shares its identifier, and each multivalued slot to the link
table of each of those classes. Every table then holds the whole extent of its class, and a
reference resolves whichever class its range names. The link tables that stay empty are
dropped once the rows are in. Every class table stays, so every foreign key keeps its parent.

The database is a build artefact. ``just build-browse`` writes it under ``browse/`` with
``metadata.yaml`` beside it, and ``just browse`` serves that folder with Datasette. Building
needs the ``browse`` dependency group: linkml, sqlite-utils and datasette.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.metadata
import re
import sqlite3
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from linkml_runtime.linkml_model import SchemaDefinition
from linkml_runtime.utils.schemaview import SchemaView

from . import settings

DATA_DIR = settings.PROJECT_DIR / "browse"
DDL_FILE = "schema.sql"
METADATA_FILE = "metadata.yaml"

# The class LinkML provides as an open range, which no table can stand for.
LINKML_ANY = "https://w3id.org/linkml/Any"

# Slots whose URI says they hold a record's label or its description. The first one a class
# has is its label column in Datasette, and both are indexed for full-text search. They are
# matched by URI rather than by name, so any schema using these vocabularies is served.
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
# A slot named like a label or a description serves when no slot has one of those URIs.
LABEL_NAMES = ("name", "label", "title", "prefLabel")
DESCRIPTION_NAMES = ("description", "definition", "comment")

# Datasette shows thirty values of a facet by default, so a column with more is a list.
FACET_LIMIT = 30


def database_name(view: SchemaView) -> str:
    return re.sub(r"[^A-Za-z0-9_-]+", "_", view.schema.name or "records")


def database_path(view: SchemaView, data_dir: Path = DATA_DIR) -> Path:
    return data_dir / f"{database_name(view)}.sqlite"


def quote(name: str) -> str:
    """An SQL identifier in double quotes, since a class may be named after a keyword."""
    return '"' + name.replace('"', '""') + '"'


def plain(text: str | None) -> str:
    """A schema description on one line, as Datasette shows it."""
    return " ".join((text or "").split())


def table_schema(view: SchemaView) -> SchemaDefinition:
    """The schema the tables are generated from: the source schema with two changes.

    A slot whose range is ``linkml:Any`` is stored as text, since a foreign key to an
    ``Any`` table would make every value a dead link. And a tree root holds the records
    rather than being one, so it gets no table, unless something refers to it.
    """
    schema = copy.deepcopy(view.schema)
    classes = view.all_classes()
    open_ranges = {name for name, cls in classes.items() if view.get_uri(cls, expand=True) == LINKML_ANY}
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
        schema.classes.pop(name, None)
    return schema


def schema_digest(view: SchemaView) -> str:
    """A digest of what the DDL depends on: the schema files, linkml, and this module."""
    digest = hashlib.sha256(f"linkml {importlib.metadata.version('linkml')}".encode())
    sources = {Path(s.source_file) for s in view.schema_map.values() if s.source_file}
    for path in [*sorted(sources), Path(__file__)]:
        if path.is_file():
            digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def generate_ddl(view: SchemaView, cache: Path | None = None) -> str:
    """The SQLite DDL for the schema, kept in ``cache`` under the schema's digest.

    Generating it takes about ten seconds for a schema of a hundred classes, and the result
    changes only with the schema or with linkml, so a cached copy is reused while it matches.
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
    """An in-memory database with every table of the DDL. The build happens in memory and
    ``save`` writes it out in one step, so a failed build leaves no half-written file."""
    connection = sqlite3.connect(":memory:")
    connection.execute("pragma page_size = 1024")
    connection.executescript(f"begin;\n{ddl}\ncommit;")
    return connection


def table_columns(connection: sqlite3.Connection) -> dict[str, list[str]]:
    names = [
        name
        for (name,) in connection.execute(
            "select name from sqlite_master where type = 'table' and name not like 'sqlite_%'"
        )
    ]
    return {name: [row[1] for row in connection.execute(f"pragma table_info({quote(name)})")] for name in names}


@dataclass(frozen=True)
class Target:
    """Where one slot's values go in one class table: a column of the table itself, or a
    link table whose ``key_column`` holds the record's identifier and ``column`` a value."""

    table: str
    column: str
    key_column: str | None = None


def table_plan(view: SchemaView, tables: dict[str, list[str]], table: str, key: str) -> dict[str, Target]:
    """Where each slot of the class ``table`` is stored, by the generator's naming rules.

    A slot keeps its name, or its alias, as a column. An inlined reference becomes a column
    named after the slot and the range's identifier. A multivalued slot becomes the table
    ``<class>_<singular name>``. A list of inlined objects matches none of these. It is left
    out, and its values are counted as unplaced.
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

    rows: Counter = field(default_factory=Counter)
    links: Counter = field(default_factory=Counter)
    # Rows SQLite refused per class table: a duplicate identifier or a missing required value.
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


def _insert(connection: sqlite3.Connection, table: str, columns: list[str], rows: list[tuple]) -> int:
    if not rows:
        return 0
    names = ", ".join(quote(column) for column in columns)
    marks = ", ".join("?" for _ in columns)
    return connection.executemany(f"insert or ignore into {quote(table)} ({names}) values ({marks})", rows).rowcount


def _write_class(connection, view: SchemaView, tables, class_name: str, records: list[dict[str, Any]], report: LoadReport) -> None:
    """Write the records of one class to its table, its ancestors' tables and their link tables."""
    key = view.get_identifier_slot(class_name)
    if key is None:
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
            report.links[target.table] += _insert(connection, target.table, [target.key_column, target.column], pairs)


def load_rows(connection: sqlite3.Connection, view: SchemaView, rows: dict[str, list[dict[str, Any]]]) -> LoadReport:
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
    """The label column of a class table and the columns full-text search indexes."""
    label = description = None
    slots = [s for s in view.class_induced_slots(table) if (s.alias or s.name) in columns and not s.multivalued]
    for slot in slots:
        uri = view.get_uri(slot, expand=True)
        if label is None and uri in LABEL_URIS:
            label = slot.alias or slot.name
        elif description is None and uri in DESCRIPTION_URIS:
            description = slot.alias or slot.name
    names = {slot.alias or slot.name for slot in slots}
    label = label or next((n for n in LABEL_NAMES if n in names), None)
    description = description or next((n for n in DESCRIPTION_NAMES if n in names and n != label), None)
    return label, [column for column in (label, description) if column]


def enable_search(connection: sqlite3.Connection, view: SchemaView, report: LoadReport) -> list[str]:
    """Index the label and description of every class table with rows, and list those tables.

    sqlite-utils creates ``<table>_fts`` with the table as its content, which is the layout
    Datasette looks for, so each of these tables gets a search box.
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
    """Drop the link tables that received no rows. No foreign key points at a link table,
    and Datasette does work for every table each time it lists a database."""
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
    """Per (table, parent table), the values that name a row the parent lacks: references in
    the data to records the data does not contain."""
    return Counter((table, parent) for table, _, parent, _ in connection.execute("pragma foreign_key_check"))


def save(connection: sqlite3.Connection, path: Path) -> None:
    """Write the in-memory database to ``path``, compacted, replacing any earlier file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.unlink(missing_ok=True)
    connection.execute("vacuum into ?", (str(path),))


# Datasette metadata. The keys are those Datasette 0.65 reads from its metadata file.
# Datasette 1.0 reads the table settings from datasette.yaml instead.


def search_tables(connection: sqlite3.Connection) -> set[str]:
    """The full-text tables, which Datasette hides by itself, and their shadow tables."""
    virtual = [
        name for (name,) in connection.execute("select name from sqlite_master where sql like 'CREATE VIRTUAL TABLE%'")
    ]
    return {
        name
        for name in table_columns(connection)
        if any(name == table or name.startswith(f"{table}_") for table in virtual)
    }


def facets(connection: sqlite3.Connection, view: SchemaView, table: str, slots: dict[str, Any], rows: int) -> list[str]:
    """The enum and reference columns of ``table`` with two to thirty distinct values."""
    classes, enums = view.all_classes(), view.all_enums()
    chosen = []
    for column, slot in slots.items():
        if slot.range not in enums and slot.range not in classes:
            continue
        (distinct,) = connection.execute(f"select count(distinct {quote(column)}) from {quote(table)}").fetchone()
        if 2 <= distinct <= min(FACET_LIMIT, rows - 1):
            chosen.append(column)
    return chosen


def database_metadata(connection: sqlite3.Connection, view: SchemaView, description: str) -> dict[str, Any]:
    """One database's metadata: its description, each full table's description, label column,
    facets and column descriptions, and each empty class table hidden."""
    tables = table_columns(connection)
    hidden_by_datasette = search_tables(connection)
    counts = {
        table: connection.execute(f"select count(*) from {quote(table)}").fetchone()[0]
        for table in tables
        if table not in hidden_by_datasette
    }
    classes = view.all_classes()
    entries: dict[str, dict[str, Any]] = {}
    for table in sorted(t for t, count in counts.items() if count and t in classes):
        slots = {slot.alias or slot.name: slot for slot in view.class_induced_slots(table)}
        key = view.get_identifier_slot(table)
        plan = table_plan(view, tables, table, key.name) if key else {}
        own = {t.column: slots[t.column] for t in plan.values() if t.key_column is None and t.column in slots}
        entry: dict[str, Any] = {"description": plain(classes[table].description)}
        label, _ = text_columns(view, table, tables[table])
        if label:
            entry["label_column"] = label
        chosen = facets(connection, view, table, own, counts[table])
        if chosen:
            entry["facets"] = chosen
        columns = {column: plain(slot.description) for column, slot in own.items() if slot.description}
        if columns:
            entry["columns"] = columns
        entries[table] = entry
        for name, target in plan.items():
            if target.key_column is None or not counts.get(target.table):
                continue
            entries[target.table] = {
                "description": f"Links each {table} row to its {name} values, one value per row.",
                "columns": {
                    target.key_column: f"The {table} row.",
                    target.column: plain(view.induced_slot(name, table).description) or f"One {name} value.",
                },
            }
    # Datasette also hides every table whose name starts with a hidden table's name, so an
    # empty table whose name begins a full one's is left visible rather than hiding both.
    full = [table for table, count in counts.items() if count]
    for table in sorted(t for t, count in counts.items() if not count):
        if not any(other.startswith(table) for other in full):
            entries[table] = {"hidden": True}
    return {"description": description, "tables": entries}


def build_metadata(view: SchemaView, path: Path) -> dict[str, Any]:
    schema = view.schema
    metadata: dict[str, Any] = {"title": schema.title or schema.name, "description": plain(schema.description)}
    if schema.version:
        metadata["source"] = f"{schema.name} {schema.version}"
        metadata["source_url"] = schema.id
    if schema.license:
        metadata["license"] = schema.license
        if schema.license.startswith(("http://", "https://")):
            metadata["license_url"] = schema.license
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    try:
        description = f"The records of the {schema.name} schema, read from {settings.DATA}."
        metadata["databases"] = {path.stem: database_metadata(connection, view, description)}
    finally:
        connection.close()
    return metadata


def write_metadata(view: SchemaView, path: Path) -> Path:
    """Write ``metadata.yaml`` beside the database, where ``datasette serve`` reads it."""
    target = path.parent / METADATA_FILE
    body = yaml.safe_dump(build_metadata(view, path), sort_keys=False, allow_unicode=True, width=100)
    target.write_text("# Written by `just build-browse` from the schema and the database; not edited.\n" + body, encoding="utf-8")
    return target


@dataclass
class BuildReport:
    path: Path
    metadata: Path
    load: LoadReport
    ddl_tables: int
    ddl_foreign_keys: int
    tables: int
    foreign_keys: int
    searchable: list[str]
    dangling: Counter
    ddl_seconds: float
    seconds: float


def build(data_dir: Path = DATA_DIR, rows: dict[str, list[dict[str, Any]]] | None = None) -> BuildReport:
    """Build the database and its metadata from the project's data source."""
    from .schema import schema_view
    from .sources import rows_by_class

    started = time.perf_counter()
    view = schema_view()
    ddl = generate_ddl(view, data_dir / DDL_FILE)
    ddl_seconds = time.perf_counter() - started
    rows = rows if rows is not None else rows_by_class()
    path = database_path(view, data_dir)
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
    metadata = write_metadata(view, path)
    return BuildReport(
        path=path,
        metadata=metadata,
        load=load,
        ddl_tables=ddl_tables,
        ddl_foreign_keys=ddl_foreign_keys,
        tables=tables,
        foreign_keys=foreign_keys,
        searchable=searchable,
        dangling=dangling,
        ddl_seconds=ddl_seconds,
        seconds=time.perf_counter() - started,
    )
