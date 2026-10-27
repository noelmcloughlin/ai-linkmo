"""The AIAtlasNexus library instances that the handlers share.

There are two: one of the packaged ontology, and one of the packaged ontology
with the bring-your-own-data files under ``byo/data/``. Each is built on first
use and kept for the life of the process, because building one parses every
YAML file. The server builds the first at startup through the linkmo project's
data source, ``src/ai_linkmo/atlas.py``.

``ai_atlas_nexus`` is imported only when an instance is first built, so a
process that never asks the library does not pay for the import.
"""

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from fastapi import HTTPException

if TYPE_CHECKING:
    from ai_atlas_nexus import AIAtlasNexus  # noqa: F401

# The path is absolute, so the instance reads the right files from any working
# directory.
BYOD_PATH = str(Path(__file__).resolve().parent.parent.parent / "byo" / "data")

# One instance per value of byod.
_ran_cache: Dict[bool, Any] = {}


def get_ran_instance(byod: bool = False) -> Any:  # Returns AIAtlasNexus
    """The cached AIAtlasNexus instance for ``byod``, built on first use.

    Raises:
        HTTPException: If the instance cannot be built
    """
    if byod in _ran_cache:
        return _ran_cache[byod]
    try:
        from ai_atlas_nexus import AIAtlasNexus

        # The library logs each instance it builds at INFO, which the command
        # line would print before every answer in local mode.
        logging.getLogger("ai_atlas_nexus.library").setLevel(logging.WARNING)
        _ran_cache[byod] = AIAtlasNexus(base_dir=BYOD_PATH) if byod else AIAtlasNexus()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize AIAtlasNexus: {e}")
    return _ran_cache[byod]


def clear_ran_cache(byod: bool = True) -> None:
    """Forget the instance for ``byod``, after ``PUT /byo`` changes its files."""
    _ran_cache.pop(byod, None)


def initialize_ran(byod: bool = False, taxonomy: Optional[str] = None) -> Any:  # Returns AIAtlasNexus
    """The instance for ``byod``, after checking that ``taxonomy``, if given, exists."""
    ran = get_ran_instance(byod)
    if taxonomy:
        validate_taxonomy(ran, taxonomy)
    return ran


def validate_taxonomy(ran, taxonomy):
    """The taxonomy with this id, or a 400 that names the id asked for."""
    if not taxonomy:
        return None
    resolved = ran.get_taxonomy_by_id(taxonomy)
    if resolved:
        return resolved
    raise HTTPException(status_code=400, detail=f"Invalid taxonomy ID: {taxonomy}")
