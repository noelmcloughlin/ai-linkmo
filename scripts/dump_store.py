"""Dump the store as YAML or JSON, one file per database, with one key per class.

Run it through ``just dump-store``, which writes ``lib/store/data/dump/atlas.yaml`` and
``byod.yaml``. The dump is the merged, per-class view of the data the store holds, in a form
that needs no DuckDB to read: every class with records is a key and its records are the list
under it. ``--only`` picks one database and ``--format json`` writes JSON.

linkml-store's ``Database.export_database`` writes this shape for a database it created, but
on one reattached from its file with the schema view set it lists every class of the schema,
66 of them empty, pads each record with every null column, and misses ``Group``, whose table
is ``GroupRecords`` (see ``collection_name`` in the loader); without the schema view its
introspection found 15 of the 34 tables. So the document is assembled here from the tables
that exist and rendered with the same ``render_output`` the export uses.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# The justfile runs this file by path, which puts scripts/ rather than the project root on
# sys.path, so the root is added before the project's own imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from lib.store.loader import DATA_DIR  # noqa: E402

FORMATS = ("yaml", "json")


def dump_database(byod: bool, output_dir: Path, *, data_dir: Path = DATA_DIR, fmt: str = "yaml") -> Path:
    """Write the records of every class that has a table, keyed by class, and return the path.

    Null columns are left out of each record, as the loader left them out of the rows, so the
    dump reads like the YAML the data came from.
    """
    from linkml_store.utils.format_utils import Format, render_output

    from lib.store.loader import DATABASES, collection_name, open_database
    from lib.store.search import tables

    database = open_database(byod, data_dir)
    present = tables(database)
    dump: dict[str, list[dict]] = {}
    for class_name in sorted(database.schema_view.all_classes()):
        alias = collection_name(class_name)
        if class_name.startswith("internal__") or alias not in present:
            continue
        rows = database.get_collection(alias, type=class_name).find({}, limit=-1).rows
        dump[class_name] = [{key: value for key, value in row.items() if value is not None} for row in rows]
    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f"{DATABASES[byod]}.{fmt}"
    path.write_text(render_output(dump, Format(fmt)), encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    from lib.store.loader import DATABASES

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--only", choices=sorted(DATABASES.values()))
    parser.add_argument("--format", choices=FORMATS, default="yaml")
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    for byod, alias in DATABASES.items():
        if args.only not in (None, alias):
            continue
        try:
            path = dump_database(byod, args.output_dir, data_dir=args.data_dir, fmt=args.format)
        except FileNotFoundError as error:
            print(error, file=sys.stderr)
            return 1
        print(f"wrote {path} ({path.stat().st_size / 1e6:.1f} MB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
