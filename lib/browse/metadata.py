"""Write the Datasette metadata for the browse databases, generated from the schema.

Datasette reads one metadata file for titles, descriptions and table settings. This one is
written from the schema and from what each database holds, so it never needs editing:

- each class table is described by its class, and each of its columns by its slot;

- each link table says which class and multivalued slot it holds;

- a table's label column, which Datasette shows in place of a bare identifier wherever a
  row links to it, is the class's label slot (see ``text_columns`` in the loader);

- a class table with no rows is hidden (the loader has already dropped the link tables
  with no rows, which no foreign key points at);

- a table's default facets are its enum and reference columns that hold between two and
  thirty distinct values, fewer than its rows.

The keys are those Datasette 0.65 reads from its metadata file. Datasette 1.0 reads the
table settings from ``datasette.yaml`` instead, which is why the dependency stays below 1.0.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import yaml
from linkml_runtime.utils.schemaview import SchemaView

from lib.browse.loader import (
    DATA_DIR,
    DATABASE_DESCRIPTIONS,
    database_path,
    quote,
    table_columns,
    table_plan,
    text_columns,
)

METADATA_FILE = "metadata.yaml"

# Datasette shows thirty values of a facet by default, so a column with more is a list,
# not a facet.
FACET_LIMIT = 30


def plain(text: str | None) -> str:
    """A schema description on one line, as Datasette shows it."""
    return " ".join((text or "").split())


def search_tables(connection: sqlite3.Connection) -> set[str]:
    """The full-text tables, which Datasette hides by itself, and their shadow tables."""
    virtual = [
        name
        for (name,) in connection.execute(
            "select name from sqlite_master where sql like 'CREATE VIRTUAL TABLE%'"
        )
    ]
    return {
        name
        for name in table_columns(connection)
        if any(name == table or name.startswith(f"{table}_") for table in virtual)
    }


def facets(
    connection: sqlite3.Connection, view: SchemaView, table: str, slots: dict[str, Any], rows: int
) -> list[str]:
    """The enum and reference columns of ``table`` worth a facet, in schema order."""
    classes = view.all_classes()
    enums = view.all_enums()
    chosen = []
    for column, slot in slots.items():
        if slot.range not in enums and slot.range not in classes:
            continue
        (distinct,) = connection.execute(
            f"select count(distinct {quote(column)}) from {quote(table)}"
        ).fetchone()
        if 2 <= distinct <= min(FACET_LIMIT, rows - 1):
            chosen.append(column)
    return chosen


def database_metadata(
    connection: sqlite3.Connection, view: SchemaView, description: str
) -> dict[str, Any]:
    """The metadata of one database: its description and the settings of each table."""
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
        own = {
            target.column: slots[target.column]
            for target in plan.values()
            if target.key_column is None and target.column in slots
        }
        entry: dict[str, Any] = {"description": plain(classes[table].description)}
        label, _ = text_columns(view, table, tables[table])
        if label:
            entry["label_column"] = label
        chosen = facets(connection, view, table, own, counts[table])
        if chosen:
            entry["facets"] = chosen
        columns = {
            column: plain(slot.description) for column, slot in own.items() if slot.description
        }
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
                    target.column: plain(view.induced_slot(name, table).description)
                    or f"One {name} value.",
                },
            }
    # Datasette also hides every table whose name starts with a hidden table's name, so an
    # empty table whose name begins a non-empty one's is left visible rather than hiding both.
    full = [table for table, count in counts.items() if count]
    for table in sorted(t for t, count in counts.items() if not count):
        if not any(other.startswith(table) for other in full):
            entries[table] = {"hidden": True}
    return {"description": description, "tables": entries}


def build_metadata(view: SchemaView, data_dir: Path = DATA_DIR) -> dict[str, Any]:
    """The metadata for every browse database present in ``data_dir``."""
    schema = view.schema
    metadata: dict[str, Any] = {
        "title": schema.title or schema.name,
        "description": plain(schema.description),
    }
    if schema.version:
        metadata["source"] = f"{schema.name} {schema.version}"
        metadata["source_url"] = schema.id
    if schema.license:
        metadata["license"] = schema.license
        if schema.license.startswith(("http://", "https://")):
            metadata["license_url"] = schema.license
    databases = {}
    for byod, description in DATABASE_DESCRIPTIONS.items():
        path = database_path(byod, data_dir)
        if not path.exists():
            continue
        connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            databases[path.stem] = database_metadata(connection, view, description)
        finally:
            connection.close()
    metadata["databases"] = databases
    return metadata


def write_metadata(view: SchemaView, data_dir: Path = DATA_DIR) -> Path:
    """Write ``metadata.yaml`` beside the databases, which ``datasette serve`` reads from there."""
    path = data_dir / METADATA_FILE
    header = "# Written by `just build-browse` from the schema and the databases; not edited.\n"
    metadata = build_metadata(view, data_dir)
    body = yaml.safe_dump(metadata, sort_keys=False, allow_unicode=True, width=100)
    path.write_text(header + body, encoding="utf-8")
    return path
