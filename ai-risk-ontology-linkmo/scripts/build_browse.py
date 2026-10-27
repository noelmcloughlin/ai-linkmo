"""Build the SQLite database and its Datasette metadata under browse/.

Run it with `just build-browse`, then `just browse` to serve the folder with Datasette. The
work is in src/ai_linkmo/browse.py. It needs the browse dependency group.

`--param name=value` asks the data source each question with a parameter the exposure file
adds, such as one that brings in more data, and `--data-dir` keeps that database apart:
`just build-browse --data-dir browse-more --param more=true`.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def plural(number: int, noun: str) -> str:
    return f"{number} {noun}" if number == 1 else f"{number} {noun}s"


def main(argv: list[str] | None = None) -> int:
    from ai_linkmo.browse import DATA_DIR, build

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument(
        "--param",
        action="append",
        default=[],
        metavar="NAME=VALUE",
        help="A parameter for each question to the data source; give it once per parameter",
    )
    args = parser.parse_args(argv)
    params = {}
    for given in args.param:
        name, equals, value = given.partition("=")
        if not name or not equals:
            parser.error(f"--param {given!r} is not written as name=value")
        params[name] = value
    logging.disable(logging.WARNING)
    report = build(args.data_dir, params=params)
    load = report.load
    print(
        f"{report.path.name}: {load.records} rows in {sum(1 for n in load.rows.values() if n)} class tables "
        f"and {load.link_rows} in {sum(1 for n in load.links.values() if n)} link tables; kept "
        f"{report.tables} of the DDL's {report.ddl_tables} tables and {report.foreign_keys} of its "
        f"{report.ddl_foreign_keys} foreign keys; {len(report.searchable)} tables searchable; "
        f"DDL in {report.ddl_seconds:.1f} s, built in {report.seconds:.1f} s"
    )
    for table, refused in sorted(load.refused.items()):
        print(f"  {table}: {plural(refused, 'row')} refused, a duplicate identifier or a missing required value")
    for slot, unplaced in sorted(load.unplaced.items()):
        print(f"  {slot}: {plural(unplaced, 'value')} with no column or link table to go in")
    for (table, parent), dangling in sorted(report.dangling.items()):
        print(f"  {table}: {plural(dangling, 'reference')} to {parent} rows that do not exist")
    print(f"wrote {report.metadata}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
