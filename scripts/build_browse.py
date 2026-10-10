"""Build the SQLite databases and the Datasette metadata under lib/browse/data.

Run it through ``just build-browse``, then ``just browse`` to serve them. ``--only atlas`` or
``--only byod`` rebuilds one database; the metadata is always rewritten for every database
present. The work is in ``lib/browse/loader.py`` and ``lib/browse/metadata.py``.
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from pathlib import Path

# The justfile runs this file by path, which puts scripts/ rather than the project root on
# sys.path, so the root is added before the project's own imports.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def plural(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def count(rows_per_table) -> int:
    """How many tables received rows."""
    return sum(1 for rows in rows_per_table.values() if rows)


def main(argv: list[str] | None = None) -> int:
    from lib.browse.loader import DATA_DIR, DDL_FILE, build_all
    from lib.store.loader import DATABASES

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--only", choices=sorted(DATABASES.values()))
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    which = [byod for byod, alias in DATABASES.items() if args.only in (None, alias)]
    started = time.perf_counter()
    build = build_all(args.data_dir, which)
    print(f"DDL in {build.ddl_seconds:.1f} s ({args.data_dir / DDL_FILE})")
    for report in build.databases:
        load = report.load
        print(
            f"{report.path.stem}: {load.records} rows in {count(load.rows)} class tables and "
            f"{load.link_rows} in {count(load.links)} link tables, "
            f"loaded in {load.seconds:.1f} s; kept {report.tables} of the DDL's "
            f"{report.ddl_tables} tables, with {report.foreign_keys} of its "
            f"{report.ddl_foreign_keys} foreign keys; {len(report.searchable)} tables searchable; "
            f"built in {report.seconds:.1f} s, {report.path.stat().st_size / 1e6:.1f} MB"
        )
        for table, refused in sorted(load.refused.items()):
            print(
                f"  {table}: {plural(refused, 'row')} refused, "
                "a duplicate identifier or a missing required value"
            )
        for slot, unplaced in sorted(load.unplaced.items()):
            print(f"  {slot}: {plural(unplaced, 'value')} with no column or link table to go in")
        for (table, parent), dangling in sorted(report.dangling.items()):
            print(f"  {table}: {plural(dangling, 'reference')} to {parent} rows that do not exist")
    print(f"wrote {build.metadata} in {time.perf_counter() - started:.1f} s in all")
    return 0


if __name__ == "__main__":
    sys.exit(main())
