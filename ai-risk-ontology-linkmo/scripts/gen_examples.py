"""Write one example per class with records, for gen-doc's --example-directory.

Run it with `just gen-examples`. `just gen-doc` runs it before gen-doc. With --validate it
also checks each example against its class with linkml's validator and exits 1 when one
fails. The work is in src/ai_linkmo/examples.py.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def main(argv: list[str] | None = None) -> int:
    from ai_linkmo.examples import choose_examples, validate_examples, write_examples
    from ai_linkmo.schema import schema_view
    from ai_linkmo.sources import rows_by_class

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("directory", type=Path, help="where gen-doc will look for examples")
    parser.add_argument("--validate", action="store_true", help="validate every example")
    args = parser.parse_args(argv)
    logging.disable(logging.WARNING)
    view = schema_view()
    rows = rows_by_class()
    examples = choose_examples(view, rows)
    paths = write_examples(view, examples, args.directory)
    print(f"wrote {len(paths)} examples to {args.directory}")
    skipped = sorted(set(rows) - set(examples))
    if skipped:
        print(f"no example for the abstract classes with records: {', '.join(skipped)}")
    if args.validate:
        failures = validate_examples(view, examples)
        for class_name, messages in sorted(failures.items()):
            for message in messages:
                print(f"{class_name}: {message}", file=sys.stderr)
        print(f"validated {len(examples)} examples, {len(failures)} failed")
        return 1 if failures else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
