"""Build the trigram search index of the store, which `GET /search` and `./ai search` read.

Run it through ``just index-store`` after ``just load-store``. ``--only atlas`` or ``--only
byod`` indexes one database; ``--scope risk --scope control`` indexes the collections those
scopes cover instead of every exposed class's. The work is in ``lib/store/search.py``.
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


def main(argv: list[str] | None = None) -> int:
    from lib.api.exposure import load_exposure
    from lib.store.loader import DATA_DIR, DATABASES
    from lib.store.search import index_database

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--only", choices=sorted(DATABASES.values()))
    parser.add_argument(
        "--scope",
        action="append",
        choices=sorted(load_exposure().by_scope),
        help="index the collections of this scope only; repeat for several",
    )
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    for byod, alias in DATABASES.items():
        if args.only not in (None, alias):
            continue
        started = time.time()
        try:
            report = index_database(byod, data_dir=args.data_dir, scopes=args.scope)
        except FileNotFoundError as error:
            print(error, file=sys.stderr)
            return 1
        for entry in report:
            print(f"{alias}: {entry.class_name} {entry.rows} rows in {entry.seconds:.1f} s")
        rows = sum(entry.rows for entry in report)
        print(f"{alias}: indexed {rows} rows in {len(report)} collections in {time.time() - started:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
