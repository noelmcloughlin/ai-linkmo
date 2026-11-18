"""Runs `lokf export` with the diataxis.md at the bundle's root read as no concept.

    python scripts/lokf-export.py <lokf export's arguments>

KTL Registrar keeps its map in that file, and the report script and the
site's pages read it as no concept. The toolkit reserves index.md and log.md
alone, so its export would write the map as a node. A diataxis.md in a
folder stays a concept.
"""

from __future__ import annotations

import sys

import lokf.model
from lokf.cli import app

stock = lokf.model.load_bundle


def load_bundle(path):
    bundle = stock(path)
    bundle.concepts = [c for c in bundle.concepts if c.concept_id != "diataxis"]
    return bundle


if __name__ == "__main__":
    lokf.model.load_bundle = load_bundle
    sys.argv = ["lokf", "export", *sys.argv[1:]]
    app()
