"""The handlers behind the API's endpoints.

``query_class`` answers every class listing that ``lib/api/api.yaml`` exposes; the API
kernel in ``lib/api/server_kernel.py`` routes each listing to it, and the CLI calls it
directly in local mode. The functions after it, ``graph``, ``schemaview``, ``crosswalk``,
``ares``, ``inference``, ``byo`` and ``byo_put``, are the hand-written operations the
overlay of the same file describes.

Importing ``ai_atlas_nexus`` at module level hangs in some environments, so the ontology
models are resolved lazily through ``_get_model``.
"""
import logging
import os
import re
import shutil
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import aiofiles
import yaml
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from lib.cli.utils import (
    clear_ran_cache,
    get_ran_instance,
    initialize_ran,
    validate_and_serialize_entities,
    validate_taxonomy,
)

logger = logging.getLogger(__name__)

# Repository anchors used by all path-bound handlers. Computing them once at
# import time means handlers no longer depend on the current working
# directory of whoever launched uvicorn / pytest / the CLI.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_GRAPH_DIR = _PROJECT_ROOT / "graph"
_GRAPH_DEFAULT_YAML = _GRAPH_DIR / "ai-risk-ontology.yaml"
# Where scripts/fetch_cypher.py saves the Cypher export that ai-atlas-nexus publishes.
_GRAPH_CYPHER = _GRAPH_DIR / "cypher" / "ai-risk-ontology.cypher"

# Constants
BYO_BASE_DIR = (_PROJECT_ROOT / "byo" / "data").resolve()
# Max allowed body size for BYO uploads (10 MiB).
BYO_MAX_UPLOAD_BYTES = 10 * 1024 * 1024
# Allowed filename extensions for BYO uploads.
_BYO_ALLOWED_SUFFIXES = {".yaml", ".yml"}
# Max risks accepted by /ares in a single call (defence-in-depth against OOM).
_MAX_ARES_RISKS = 200
# Characters allowed in user-supplied export filename segments (e.g. taxonomy IDs
# used to derive crosswalk filenames). Anything else is rejected to keep us safely
# inside the export directory.
_SAFE_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")


@lru_cache(maxsize=None)
def _get_model(name: str):
    """Resolve an ``ai_atlas_nexus`` ontology model class by name.

    Centralised so that future handlers don't need to copy the heavy module
    path; existing handlers keep their inline imports because CPython already
    caches them in ``sys.modules`` after the first call.
    """
    from ai_atlas_nexus.ai_risk_ontology.datamodel import ai_risk_ontology as _ont

    try:
        return getattr(_ont, name)
    except AttributeError as exc:  # pragma: no cover - defensive
        raise HTTPException(
            status_code=500, detail=f"Unknown ontology model: {name}"
        ) from exc


def _safe_byo_path(filename: str) -> Path:
    """Resolve ``filename`` under :data:`BYO_BASE_DIR` and reject traversal.

    Raises:
        HTTPException(400): if the filename is empty, contains path
            separators, uses a disallowed extension, or resolves outside
            ``BYO_BASE_DIR``.
    """
    if not filename or filename in {".", ".."}:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    # Reject any path separators (forward and back) or null bytes before
    # resolving. We reject both regardless of platform: even on POSIX a
    # backslash in a YAML filename is almost certainly an attacker probing
    # for Windows-style traversal, and we control the legitimate filenames
    # written to ``byo/data``.
    if "/" in filename or "\\" in filename or "\x00" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    candidate = (BYO_BASE_DIR / filename).resolve()
    try:
        candidate.relative_to(BYO_BASE_DIR)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid filename.")
    if candidate.suffix.lower() not in _BYO_ALLOWED_SUFFIXES:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type. Allowed: {sorted(_BYO_ALLOWED_SUFFIXES)}",
        )
    return candidate


def _safe_export_segment(value: str, field: str) -> str:
    """Validate a single user-supplied identifier used inside an export path.

    We never let arbitrary strings (e.g. taxonomy IDs from the query string)
    flow into output filenames unchecked - that's a path-traversal vector.
    """
    if not value or not _SAFE_SEGMENT_RE.match(value):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid value for '{field}': only [A-Za-z0-9._-] allowed.",
        )
    return value


# ============================================================================
# CLASS LISTINGS
# ============================================================================
#
# Every exposed class is served by ``query_class``. The class and its filters come from
# lib/api/api.yaml and the schema through ``load_exposure``. The
# only per-class knowledge kept here is how the library looks records up by a related risk.


def _related_adapters(ran, risk_id: str, filters: Dict[str, Any]) -> list:
    """Adapters carry the risk on ``hasRelatedRisk``, so a plain query finds them."""
    query = {k: v for k, v in filters.items() if v is not None}
    return ran.query(class_name="adapters", hasRelatedRisk=risk_id, **query) or []


# Class name to the library call that returns its records for one risk id. Each takes the
# library, the risk id and the other filters, of which only the taxonomy (and the task for
# intrinsics) reaches the library; the rest are ignored on this path, as they always were.
RELATED_LOOKUPS: Dict[str, Callable[[Any, str, Dict[str, Any]], list]] = {
    "Action": lambda ran, risk, f: ran.get_related_actions(
        id=risk, taxonomy=f.get("isDefinedByTaxonomy")
    ),
    "RiskControl": lambda ran, risk, f: ran.get_related_risk_controls(
        id=risk, taxonomy=f.get("isDefinedByTaxonomy")
    ),
    "RiskIncident": lambda ran, risk, f: ran.get_related_risk_incidents(
        risk_id=risk, taxonomy=f.get("isDefinedByTaxonomy")
    ),
    "AiEval": lambda ran, risk, f: ran.get_related_evaluations(
        risk_id=risk, taxonomy=f.get("isDefinedByTaxonomy")
    ),
    "BenchmarkMetadataCard": lambda ran, risk, f: ran.get_benchmark_metadata_cards(
        risk_id=risk
    ),
    "LLMIntrinsic": lambda ran, risk, f: ran.get_related_intrinsics(
        risk_id=risk, taxonomy=f.get("isDefinedByTaxonomy"), aitask_id=f.get("requiredByTask")
    ),
    "Adapter": _related_adapters,
}


def _matches(record: Any, name: str, value: Any) -> bool:
    """A record matches a filter when the field equals it, or its list holds it."""
    field = getattr(record, name, None)
    if field is None:
        return False
    if isinstance(field, list):
        return value in field or str(value) in [str(item) for item in field]
    return field == value or str(field) == str(value)


def _related_records(ran, exposed, risk_id: str, related: bool, filters: Dict[str, Any]) -> list:
    """Records of ``exposed`` for one risk, or for every risk related to it when ``related``."""
    lookup = RELATED_LOOKUPS.get(exposed.name)
    if lookup is None:
        raise HTTPException(
            status_code=500, detail=f"No related lookup is defined for {exposed.name}."
        )
    try:
        if not related:
            return lookup(ran, risk_id, filters) or []
        records: list = []
        for risk in ran.get_related_risks(id=risk_id) or []:
            if risk is not None:
                records.extend(lookup(ran, risk.id, filters) or [])
        return records
    except (AttributeError, TypeError) as exc:
        # The library fails this way when the risk id does not exist.
        logger.debug("Related lookup for %s with %s failed: %s", exposed.name, risk_id, exc)
        return []


def _library_instances(ran, model_cls) -> list:
    """Every instance of ``model_cls`` the library holds, whichever data file placed it.

    The library files records by collection, and a collection can hold several classes:
    831 of the 848 ``controls`` are Actions. A scope lists a class, so it reads every
    collection, which is also what the store does with one collection per class.
    """
    container = ran._atlas_explorer._data
    return [
        record
        for slot in type(container).model_fields
        for record in (getattr(container, slot) or [])
        if isinstance(record, model_cls)
    ]


def query_class(
    class_name: str,
    *,
    byod: bool = False,
    id: Optional[str] = None,
    related: bool = False,
    related_ids: bool = False,
    **filters: Any,
) -> Dict[str, Any]:
    """List, filter or fetch the records of one exposed class.

    ``filters`` are slot names of the class with the value a record must carry. With ``id``
    the answer is ``{"item": record}``; otherwise it is the envelope the web UI reads,
    ``{"items", "count", "validation_errors"}``. ``hasRelatedRisk`` on a class marked
    ``related`` in api.yaml switches to the library's related-risk lookup, and ``related``
    widens that to every risk related to the given one. A risk's own ``id`` with ``related``
    returns the risks related to it.
    """
    from lib.api.exposure import load_exposure

    exposed = load_exposure().classes.get(class_name)
    if exposed is None:
        raise HTTPException(status_code=404, detail=f"{class_name} is not exposed.")
    unknown = sorted(set(filters) - set(exposed.slot_names) - {"hasRelatedRisk"})
    if unknown:
        raise HTTPException(
            status_code=422, detail=f"{class_name} has no filter named {', '.join(unknown)}."
        )
    from lib.store.source import store_has_taxonomy, store_records, using_store

    store = using_store()
    taxonomy = filters.get("isDefinedByTaxonomy")
    model_cls = _get_model(class_name)
    active = {k: v for k, v in filters.items() if v is not None}
    risk_id = active.pop("hasRelatedRisk", None) if exposed.related else None
    # The related lookups always run on the library; the plain listings run on the store
    # when it is the configured source, and then the library is never loaded at all.
    related_lookup = (class_name == "Risk" and id and (related or related_ids)) or risk_id is not None
    ran = get_ran_instance(byod) if related_lookup or not store else None
    if taxonomy:
        if ran is not None:
            validate_taxonomy(ran, taxonomy)
        elif not store_has_taxonomy(taxonomy, byod):
            raise HTTPException(status_code=400, detail=f"Invalid taxonomy ID: {taxonomy}")

    try:
        if class_name == "Risk" and id and (related or related_ids):
            records = ran.get_related_risks(id=id, taxonomy=taxonomy) or []
            # The library ignores its taxonomy argument, so apply it here.
            if taxonomy:
                records = [r for r in records if r.isDefinedByTaxonomy == taxonomy]
        elif risk_id is not None:
            records = _related_records(ran, exposed, risk_id, related or related_ids, active)
        elif store:
            multivalued = {p.name for p in exposed.parameters if p.multivalued}
            # Each row is built with its own class's model, as the library's instances are.
            records = [
                _get_model(name)(**row)
                for name, row in store_records(class_name, active, multivalued, byod)
            ]
            if id:
                record = next((r for r in records if getattr(r, "id", None) == id), None)
                return {"item": record.model_dump() if record is not None else None}
        else:
            records = [
                r
                for r in _library_instances(ran, model_cls)
                if all(_matches(r, k, v) for k, v in active.items())
            ]
            if id:
                record = next((r for r in records if getattr(r, "id", None) == id), None)
                return {"item": record.model_dump() if record is not None else None}
        if related_ids:
            records = [r.id for r in records if hasattr(r, "id")]
        serialized, errors, _ = validate_and_serialize_entities(records, model_cls)
        return {"items": serialized, "count": len(serialized), "validation_errors": errors}
    except HTTPException:
        raise
    except Exception:
        logger.exception("query_class failed for %s", class_name)
        raise HTTPException(status_code=500, detail=f"Failed to fetch {class_name}.")




def search(q: str, byod: bool = False, scope: Optional[str] = None, limit: int = 20) -> Dict[str, Any]:
    """Full-text search over the store's records, through linkml-store's trigram index.

    ``scope`` narrows the search to one exposed class, named by its CLI scope such as
    ``risk``; without it every exposed class is searched. The work is in ``lib/store/search``.
    """
    from lib.store.search import search as search_store

    return search_store(q, byod=byod, scope=scope, limit=limit)


def graph(export: bool=False, id: Optional[str]=None, byod: bool=False) -> Dict[str, Any]:
    """Fetch the Cypher export, write the merged ontology as YAML, or return that YAML.

    ``id="cypher"`` with ``export`` fetches the Cypher export that ai-atlas-nexus commits for
    the installed version, through ``scripts/fetch_cypher.py``, and says which version landed
    where. That artefact is built upstream from the packaged data alone, so ``byod`` is refused
    here with a 400 rather than silently ignored. ``export`` without an id writes the merged
    ontology, with the ``byo/data`` files when ``byod`` is set, to ``graph/``; no argument
    returns that YAML.

    All filesystem paths are resolved relative to the repository root, not the caller's
    working directory, so this handler behaves the same from uvicorn, pytest or the CLI.
    """
    if id == "cypher" and export:
        if byod:
            raise HTTPException(
                status_code=400,
                detail=(
                    "The Cypher export is the artefact ai-atlas-nexus publishes for its "
                    "packaged data, so it cannot include the files under byo/data; "
                    "request it without byod."
                ),
            )
        from scripts.fetch_cypher import FetchError, artefact_url, fetch, installed_version

        version = installed_version()
        try:
            path = fetch(version=version, output=_GRAPH_CYPHER)
        except FetchError as error:
            logger.error("Cypher fetch failed: %s", error)
            raise HTTPException(status_code=502, detail=str(error))
        relative = str(path.relative_to(_PROJECT_ROOT))
        return {
            "status": "success",
            "message": f"ai-atlas-nexus {version} Cypher export is at {relative}",
            "ai_atlas_nexus": version,
            "source": artefact_url(version),
            "path": relative,
        }

    elif export:
        # Initialize AIAtlasNexus instance
        ran = initialize_ran(byod)

        _GRAPH_DIR.mkdir(parents=True, exist_ok=True)
        logger.info("Exporting graph data to %s", _GRAPH_DIR)
        ran.export(str(_GRAPH_DIR) + os.sep)
        success_msg = f"Graph exported to: {_GRAPH_DEFAULT_YAML}"
        logger.info(success_msg)
        return {
            "status": "success",
            "message": success_msg,
            "path": str(_GRAPH_DEFAULT_YAML.relative_to(_PROJECT_ROOT)),
        }

    else:
        logger.info("No argument passed - returning entire graph: %s", _GRAPH_DEFAULT_YAML)
        if _GRAPH_DEFAULT_YAML.is_file():
            content = _GRAPH_DEFAULT_YAML.read_text(encoding="utf-8")
            return {
                "status": "success",
                "message": "Graph data retrieved",
                "file": str(_GRAPH_DEFAULT_YAML.relative_to(_PROJECT_ROOT)),
                "content_length": len(content),
                "content": content,
            }
        error_msg = f"File '{_GRAPH_DEFAULT_YAML.name}' not found in '{_GRAPH_DIR}'."
        logger.error(error_msg)
        return {"status": "error", "message": error_msg}


def schemaview(introspect: bool = True) -> Dict[str, Any]:
    """View and introspect the schema using the AIAtlasNexus library.

    Returns a JSON-serializable summary of the schema (name, description,
    counts, sample class/slot hierarchies) instead of only logging it.
    """
    # Initialize AIAtlasNexus instance to retrieve SCHEMA
    ran = initialize_ran()
    view = ran.get_schema()

    summary: Dict[str, Any] = {
        "name": getattr(view.schema, "name", None),
        "description": getattr(view.schema, "description", None),
        "counts": {
            "classes": len(view.all_classes()),
            "slots": len(view.all_slots()),
            "subsets": len(view.all_subsets()),
        },
    }

    if introspect:
        summary["risk"] = {
            "ancestors": list(view.class_ancestors("Risk")),
            "ancestor_uris": [view.get_uri(c) for c in view.class_ancestors("Risk")],
            "ancestor_uris_expanded": [
                view.get_uri(c, expand=True) for c in view.class_ancestors("Risk")
            ],
            "ancestors_without_mixins": list(
                view.class_ancestors("Risk", mixins=False)
            ),
        }
        summary["refersToRisk"] = {
            "ancestors": list(view.slot_ancestors("refersToRisk")),
            "children": list(view.slot_children("refersToRisk")),
        }

    return summary


def all_classes_endpoint(
    class_name: Optional[str] = None,
    taxonomy: Optional[str] = None,
    vocabulary: Optional[str] = None,
) -> Dict[str, Any]:
    """List all classes known to the AIAtlasNexus schema.

    Optional filters narrow the result:
    - ``class_name``: return only the class whose name matches (case-insensitive).
    - ``taxonomy`` / ``vocabulary``: reserved for future use; currently ignored
      so the response shape is stable.
    """
    ran = initialize_ran()
    view = ran.get_schema()
    classes = sorted(view.all_classes().keys())

    if class_name:
        target = class_name.lower()
        classes = [c for c in classes if c.lower() == target]

    return {
        "count": len(classes),
        "classes": classes,
        "filters": {
            "class_name": class_name,
            "taxonomy": taxonomy,
            "vocabulary": vocabulary,
        },
    }


def crosswalk(byod: bool = False, isDefinedByTaxonomy: Optional[str] = None,
              isDefinedByTaxonomy2: Optional[str] = None, export: bool = False) -> Dict[str, Any]:
    """
    Crosswalk between two taxonomies.
    """
    if not (isDefinedByTaxonomy and isDefinedByTaxonomy2):
        error_msg = "Both isDefinedByTaxonomy and isDefinedByTaxonomy2 must be provided."
        logger.error(error_msg)
        return {"error": error_msg}

    # Initialize AIAtlasNexus instance - this validates the first taxonomy.
    ran = initialize_ran(byod, isDefinedByTaxonomy)
    # Explicitly validate the second taxonomy too so a bad value fails fast
    # with a 400 instead of producing an empty CSV.
    from lib.cli.utils import validate_taxonomy as _validate_taxonomy
    _validate_taxonomy(ran, isDefinedByTaxonomy2)

    taxonomies = ran.query(class_name='taxonomies')
    logger.info("Taxonomies: %d  IDs: %s", len(taxonomies), [x.id for x in taxonomies])

    from collections import defaultdict
    from functools import lru_cache

    import pandas as pd
    from pydantic import BaseModel

    logger.info(
        "Comparing taxonomy %r with taxonomy %r", isDefinedByTaxonomy, isDefinedByTaxonomy2
    )

    class RiskSimplified(BaseModel):
        id: str
        name: str
        isPartOf: str | None
        isDefinedByTaxonomy: str | None

    # Memoize get_risk to avoid the N+1 lookup pattern that previously
    # called ran.get_risk(id=...) inside each apply().
    @lru_cache(maxsize=None)
    def _get_risk_cached(risk_id: str):
        return ran.get_risk(id=risk_id)

    def expand_risks(list_of_risk_ids):
        """Retrieve content for the related risk IDs and return a string

        Args:
            list_of_risk_ids: List[str]

        Return:
            str
            Result containing Formatted string for the dataframe
        """
        risks = [
            item for item in (
                _get_risk_cached(risk_id) for risk_id in list_of_risk_ids if risk_id is not None) if item is not None]
        grouped_risks = defaultdict(list)

        for risk in risks:
            selected_fields_risk = RiskSimplified(
                id=risk.id,
                name=risk.name,
                isPartOf=risk.isPartOf,
                isDefinedByTaxonomy=risk.isDefinedByTaxonomy)
            grouped_risks[risk.isDefinedByTaxonomy].append(
                selected_fields_risk)

        return str(dict(grouped_risks))

    def construct_crosswalk_df(taxonomy_1, taxonomy_2):
        """Construct a crosswalk dataframe

        Args:
            taxonomy_1: str
                taxonomy identifier
            taxonomy_2: str
                taxonomy identifier

        Return:
            pd.DataFrame
            Results in form of a pd.Dataframe
        """
        # get all risks from taxonomy 1 into a dataframe
        df = pd.DataFrame([res.model_dump() for res in ran.query(
            class_name="risks", isDefinedByTaxonomy=taxonomy_1)])

        # we only need to show a subset of columns
        df = df[['id', 'name', 'description', 'hasRelatedAction', 'isPartOf',
                 'close_mappings', 'exact_mappings', 'broad_mappings', 'narrow_mappings',
                 'related_mappings']]

        # show only risk content relating to the second taxonomy
        def filter_by_taxonomy(list_risks):
            if list_risks is None:
                return None
            kept = []
            for rid in list_risks:
                risk = _get_risk_cached(rid)
                if risk is not None and risk.isDefinedByTaxonomy == taxonomy_2:
                    kept.append(rid)
            return kept

        for col in ('close_mappings', 'exact_mappings', 'broad_mappings',
                    'narrow_mappings', 'related_mappings'):
            df[col] = df[col].apply(filter_by_taxonomy)
        df.rename(columns={"id": "RAN ID"})
        df['expanded_risks'] = df.apply(lambda row: expand_risks((row['close_mappings'] or []) +
                                                                 (row['exact_mappings'] or []) +
                                                                 (row['broad_mappings'] or []) +
                                                                 (row['narrow_mappings'] or []) +
                                                                 (row['related_mappings'] or [])), axis=1)
        return df

    # Use the helper functions in the crosswalk function
    logger.info(
        "Constructing crosswalk between taxonomy %r and taxonomy %r",
        isDefinedByTaxonomy, isDefinedByTaxonomy2,
    )
    df = construct_crosswalk_df(isDefinedByTaxonomy, isDefinedByTaxonomy2)
    if export:
        # Sanitize both taxonomy IDs before letting them flow into a filename:
        # this prevents a request with a crafted ID from writing outside the
        # ``graph/`` directory.
        safe_tax1 = _safe_export_segment(isDefinedByTaxonomy, "isDefinedByTaxonomy")
        safe_tax2 = _safe_export_segment(isDefinedByTaxonomy2, "isDefinedByTaxonomy2")
        _GRAPH_DIR.mkdir(parents=True, exist_ok=True)
        out_path = _GRAPH_DIR / f"crosswalk_{safe_tax1}_to_{safe_tax2}.csv"
        # Defence in depth: confirm the resolved path is still inside the
        # graph directory.
        try:
            out_path.resolve().relative_to(_GRAPH_DIR)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid export path.")
        logger.info("Exporting crosswalk data to %s", out_path)
        df.to_csv(out_path, index=False)
        return {
            "exported": True,
            "path": str(out_path.relative_to(_PROJECT_ROOT)),
        }
    else:
        # Return the DataFrame as a list of dicts for API/JSON use
        return {"crosswalk": df.to_dict(orient="records")}


def ares(risks, inference_engine, target):
    """
    Run ARES evaluation.
    """
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import (
        Risk)
    if not isinstance(risks, list):
        raise HTTPException(
            status_code=400, detail="'risks' must be a JSON array."
        )
    if len(risks) > _MAX_ARES_RISKS:
        # Defence in depth against memory exhaustion via a giant payload.
        raise HTTPException(
            status_code=413,
            detail=f"'risks' exceeds maximum of {_MAX_ARES_RISKS} entries.",
        )
    # Validate and convert risks to Risk objects
    risk_objs = []
    errors = []
    for r in risks:
        try:
            risk_obj = Risk(**r) if not isinstance(r, Risk) else r
            risk_objs.append(risk_obj)
        except Exception as e:
            errors.append(str(e))

    return {
        "result": {
            "risks": [r.model_dump() for r in risk_objs],
            "inference_engine": inference_engine,
            "target": target,
            "status": "ARES evaluation completed",
            "validation_errors": errors
        }
    }


def inference(
    engine: str = "vllm",
    parameters: Optional[str] = None,
    byod: bool = False,
    isDefinedByTaxonomy: str = "ibm-risk-atlas",
    usecase: Optional[str] = None,
    id: Optional[str] = None,
) -> Dict[str, Any]:
    """Identify risks for a usecase using a configured inference engine.

    ``parameters`` is a JSON object string mapping engine parameter names
    to scalar values, e.g. ``{"max_tokens": 1000, "temperature": 0.7}``.
    The legacy ``key=value, key=value`` format is rejected because parsing
    it previously relied on ``eval`` (code injection vector).
    """
    if not usecase:
        raise HTTPException(status_code=400, detail="'usecase' is required")
    if not id:
        raise HTTPException(status_code=400, detail="'id' (model id) is required")

    engine_key = (engine or "").lower()
    engine_registry = {
        "vllm": ("VLLMInferenceEngine", "VLLMInferenceEngineParams"),
        "wml": ("WMLInferenceEngine", "WMLInferenceEngineParams"),
        "ollama": ("OllamaInferenceEngine", "OllamaInferenceEngineParams"),
    }
    if engine_key not in engine_registry:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid inference engine '{engine}'. Allowed: {sorted(engine_registry)}",
        )

    # Parse parameters as JSON (safe). Empty/None -> defaults.
    params_dict: Dict[str, Any] = {}
    if parameters:
        import json

        try:
            parsed = json.loads(parameters)
        except (TypeError, ValueError) as exc:
            raise HTTPException(
                status_code=400,
                detail=f"'parameters' must be a JSON object string: {exc}",
            )
        if not isinstance(parsed, dict):
            raise HTTPException(
                status_code=400,
                detail="'parameters' must decode to a JSON object",
            )
        # Constrain values to JSON scalars to avoid surprises downstream.
        for k, v in parsed.items():
            if not isinstance(v, (str, int, float, bool)) and v is not None:
                raise HTTPException(
                    status_code=400,
                    detail=f"Parameter '{k}' must be a scalar value",
                )
        params_dict = parsed

    engine_cls_name, params_cls_name = engine_registry[engine_key]
    engine_module = __import__(
        "ai_atlas_nexus.blocks.inference", fromlist=[engine_cls_name]
    )
    params_module = __import__(
        "ai_atlas_nexus.blocks.inference.params", fromlist=[params_cls_name]
    )
    engine_cls = getattr(engine_module, engine_cls_name)
    params_cls = getattr(params_module, params_cls_name)
    logger.info("Using %s for inference", engine_cls_name)

    inference_engine = engine_cls(
        model_name_or_path=id,
        gpu_memory_utilization=0.8,
        parameters=params_cls(**params_dict),
    )

    ran = initialize_ran(byod, isDefinedByTaxonomy)
    risks = ran.identify_risks_from_usecases(
        usecases=[usecase],
        inference_engine=inference_engine,
        taxonomy=isDefinedByTaxonomy,
    )

    serialized_risks = []
    for r in risks:
        try:
            serialized_risks.append(
                r.model_dump() if hasattr(r, "model_dump") else dict(r)
            )
        except Exception:  # pragma: no cover - defensive
            serialized_risks.append({"id": getattr(r, "id", None)})

    return {
        "usecase": usecase,
        "engine": engine_key,
        "isDefinedByTaxonomy": isDefinedByTaxonomy,
        "count": len(serialized_risks),
        "risks": serialized_risks,
    }


async def byo_put(filename: str, request: Request) -> Dict[str, str]:
    """Handler to upload a file to 'byo/data/'.

    Hardens uploads in three ways:

    * Path traversal is rejected up front via :func:`_safe_byo_path`.
    * Body size is capped (``Content-Length`` *and* streaming check) to
      prevent OOM attacks.
    * Content is validated as YAML before atomically replacing any existing
      file. The previous file is preserved as ``<name>.bak`` so an admin
      can roll back.
    """
    file_path = _safe_byo_path(filename)
    BYO_BASE_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = file_path.with_suffix(file_path.suffix + ".bak")

    # Check Content-Length upfront when the client provides it.
    try:
        declared_len = int(request.headers.get("content-length", "0") or 0)
    except ValueError:
        declared_len = 0
    if declared_len > BYO_MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"Payload too large. Max {BYO_MAX_UPLOAD_BYTES} bytes.",
        )

    # Stream the body to a temp file inside the target directory and enforce
    # the size cap incrementally. Writing within the same dir guarantees the
    # eventual ``os.replace`` is atomic.
    tmp_fd, tmp_name = tempfile.mkstemp(
        prefix=f".{file_path.name}.", suffix=".part", dir=str(BYO_BASE_DIR)
    )
    tmp_path = Path(tmp_name)
    bytes_written = 0
    try:
        async with aiofiles.open(tmp_fd, "wb") as tmp_f:
            async for chunk in request.stream():
                bytes_written += len(chunk)
                if bytes_written > BYO_MAX_UPLOAD_BYTES:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Payload too large. Max {BYO_MAX_UPLOAD_BYTES} bytes.",
                    )
                await tmp_f.write(chunk)

        # Validate YAML well-formedness so a broken upload doesn't poison the
        # next BYOD load. We only parse - schema validation happens later
        # when the cache is rebuilt.
        try:
            with open(tmp_path, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
        except yaml.YAMLError as exc:
            raise HTTPException(
                status_code=400,
                detail=f"Uploaded content is not valid YAML: {exc}",
            )

        # Backup existing file before overwriting; tolerate failures so we
        # never abort the upload over a missing backup destination.
        if file_path.exists():
            try:
                shutil.copy2(file_path, backup_path)
            except OSError:
                logger.exception("Failed to back up %s before overwrite", file_path)

        # Atomic replace - same filesystem so this is rename(2) under the hood.
        os.replace(tmp_path, file_path)
        tmp_path = None  # ownership transferred; skip cleanup below.

        # Clear BYOD cache so next request picks up new data.
        clear_ran_cache(byod=True)
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Failed to write BYO file %s", filename)
        raise HTTPException(status_code=500, detail="Failed to write file.") from exc
    finally:
        # Best-effort cleanup of the temp file when we didn't promote it.
        if tmp_path is not None:
            try:
                tmp_path.unlink()
            except OSError:
                pass

    return {"detail": f"File '{filename}' uploaded successfully."}


def byo(filename: str) -> FileResponse:
    """Handler to serve files from 'byo/data/'."""
    file_path = _safe_byo_path(filename)

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/octet-stream",
        filename=filename,
    )
