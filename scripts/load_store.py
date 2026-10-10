"""Build the DuckDB store under lib/store/data from the packaged and bring-your-own data.

Run it through ``just load-store``. ``--only atlas`` or ``--only byod`` builds one database.
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
    from lib.store.loader import DATA_DIR, DATABASES, build_all

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR)
    parser.add_argument("--only", choices=sorted(DATABASES.values()))
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    which = [byod for byod, alias in DATABASES.items() if args.only in (None, alias)]
    started = time.time()
    config = build_all(args.data_dir, which)
    print(f"wrote {config.parent} in {time.time() - started:.1f} s")
    return 0


if __name__ == "__main__":
    sys.exit(main())
