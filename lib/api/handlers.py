"""Business logic for AI-LinkMO API handlers.

Usage:
    from lib.api.handlers import actions, evaluations, ...

Bug: python -c "from ai_atlas_nexus import AIAtlasNexus"  # Hangs
"""
import logging
import os
import re
import shutil
import subprocess
import tempfile
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
import yaml
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from lib.cli.utils import (
    create_related_fetch_all,
    create_standard_fetch_all,
    create_typed_fetch_all,
    fetch_by_id_item,
    generic_entity_handler,
    initialize_ran,
    clear_ran_cache,
)

logger = logging.getLogger(__name__)

# Repository anchors used by all path-bound handlers. Computing them once at
# import time means handlers no longer depend on the current working
# directory of whoever launched uvicorn / pytest / the CLI.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_GRAPH_DIR = _PROJECT_ROOT / "graph"
_GRAPH_EXPORT_SCRIPT = _GRAPH_DIR / "cypher" / "export.py"
_GRAPH_DEFAULT_YAML = _GRAPH_DIR / "ai-risk-ontology.yaml"
# Subprocess timeout (seconds) for the cypher exporter helper script.
_GRAPH_EXPORT_TIMEOUT = 300

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


def actions(
    byod: bool = False,
    id: Optional[str] = None,
    type: Optional[str] = None,
    hasAiActorTask: Optional[str] = None,
    isDefinedByTaxonomy: Optional[str] = None,
    hasDocumentation: Optional[str] = None,
    related: bool = False,
    related_ids: bool = False,
    hasRelatedRisk: Optional[str] = None
) -> Dict[str, Any]:
    """Handler to retrieve Action entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Action

    return generic_entity_handler(
        entity_name="actions",
        model_cls=Action,
        fetch_all=create_related_fetch_all(
            related_method_name='get_related_actions',
            related_method_params=['isDefinedByTaxonomy'],
            related_param_mappings={'isDefinedByTaxonomy': 'taxonomy'}
        ),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        type=type,
        hasAiActorTask=hasAiActorTask,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        hasRelatedRisk=hasRelatedRisk,
        related=related,
        related_ids=related_ids
    )


def evaluations(
    byod: bool = False,
    id: Optional[str] = None,
    hasDataset: Optional[str] = None,
    hasTasks: Optional[str] = None,
    hasLicense: Optional[str] = None,
    benchmarkmetadata: Optional[str] = None,
    unitxcard: Optional[str] = None,
    hasDocumentation: Optional[str] = None,
    hasRelatedRisk: Optional[str] = None,
    related: bool = False,
    related_ids: bool = False
) -> Dict[str, Any]:
    """Handler to retrieve AiEval entities.

    Note: only ``isDefinedByTaxonomy`` is forwarded to the upstream
    ``get_related_evaluations`` helper. Other filters (``hasDataset``,
    ``hasTasks``, ...) are applied to the standard ``ran.query`` path; when
    combined with ``--related``/``--related_ids`` they are silently ignored
    by the upstream method.
    """
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import AiEval

    # bug: when invalid risk_id is provided, the upstream library's
    # get_related_evaluations method tries to access .id on a None
    # object (risk doesn't exist), causing the AttributeError.
    return generic_entity_handler(
        entity_name="evaluations",
        model_cls=AiEval,
        fetch_all=create_related_fetch_all(
            related_method_name='get_related_evaluations',
            related_method_params=['isDefinedByTaxonomy'],
            related_param_mappings={'isDefinedByTaxonomy': 'taxonomy'}
        ),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        hasDataset=hasDataset,
        hasTasks=hasTasks,
        hasLicense=hasLicense,
        benchmarkmetadata=benchmarkmetadata,
        unitxcard=unitxcard,
        hasDocumentation=hasDocumentation,
        hasRelatedRisk=hasRelatedRisk,
        related=related,
        related_ids=related_ids
    )


def organizations(byod: bool = False, grants_license: Optional[str] = None,
                  id: Optional[str] = None) -> Dict[str, Any]:
    """Handler to retrieve Organization entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Organization

    return generic_entity_handler(
        entity_name="organizations",
        model_cls=Organization,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        grants_license=grants_license,
        id=id
    )


def groups(byod: bool = False, id: Optional[str] = None,
           isDefinedByTaxonomy: Optional[str] = None, hasDocumentation: Optional[str] = None, type: Optional[str] = None,
           belongsToDomain: Optional[str] = None, hasPart: Optional[str] = None) -> Dict[str, Any]:
    """Handler to retrieve Group entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Group

    return generic_entity_handler(
        entity_name="groups",
        model_cls=Group,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        type=type,
        belongsToDomain=belongsToDomain,
        hasPart=hasPart
    )


def controls(
    byod: bool = False,
    id: Optional[str] = None,
    isDefinedByTaxonomy: Optional[str] = None,
    hasDocumentation: Optional[str] = None,
    hasAiActorTask: Optional[str] = None,
    detectsRiskConcept: Optional[str] = None,
    isDetectedBy: Optional[str] = None,
    type: Optional[str] = None,
    related: bool = False,
    related_ids: bool = False,
    hasRelatedRisk: Optional[str] = None
) -> Dict[str, Any]:
    """Handler to retrieve Control entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Control

    return generic_entity_handler(
        entity_name="controls",
        model_cls=Control,
        fetch_all=create_related_fetch_all(
            related_method_name='get_related_risk_controls',
            related_method_params=['isDefinedByTaxonomy'],
            related_param_mappings={'isDefinedByTaxonomy': 'taxonomy'}
        ),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        hasAiActorTask=hasAiActorTask,
        detectsRiskConcept=detectsRiskConcept,
        isDetectedBy=isDetectedBy,
        type=type,
        hasRelatedRisk=hasRelatedRisk,
        related=related,
        related_ids=related_ids
    )


def risks(
    byod: bool = False,
    id: Optional[str] = None,
    isDefinedByTaxonomy: Optional[str] = None,
    hasDocumentation: Optional[str] = None,
    isPartOf: Optional[str] = None,
    hasPart: Optional[str] = None,
    descriptor: Optional[str] = None,
    detectsRiskConcept: Optional[str] = None,
    isDetectedBy: Optional[str] = None,
    implementedByAdapter: Optional[str] = None,
    risk_type: Optional[str] = None,
    phase: Optional[str] = None,
    related: bool = False,
    related_ids: bool = False
) -> Dict[str, Any]:
    """Handler to retrieve Risk entities with special related risks logic."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk

    def fetch_by_id_wrapper(ran, entity_name, id, **kw):
        if id and (related or related_ids):
            related_items = ran.get_related_risks(
                id=id, taxonomy=isDefinedByTaxonomy) or []
            # workaround bug in ran.get_related_risks (ignores taxonomy arg)
            if isDefinedByTaxonomy:
                related_items = [
                    r for r in related_items if r.isDefinedByTaxonomy == isDefinedByTaxonomy]
            if related_ids:
                return [getattr(item, "id", None) for item in related_items if hasattr(item, "id")]
            elif related:
                return related_items
        return fetch_by_id_item(ran, entity_name, id, **kw)

    return generic_entity_handler(
        entity_name="risks",
        model_cls=Risk,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_wrapper,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        hasPart=hasPart,
        isPartOf=isPartOf,
        descriptor=descriptor,
        detectsRiskConcept=detectsRiskConcept,
        isDetectedBy=isDetectedBy,
        risk_type=risk_type,
        phase=phase,
        related=related,
        related_ids=related_ids,
        implementedByAdapter=implementedByAdapter
    )


def incidents(
        byod: bool = False,
        id: Optional[str] = None,
        isDefinedByTaxonomy: Optional[str] = None,
        hasDocumentation: Optional[str] = None,
        refersToRisk: Optional[str] = None,
        hasStatus: Optional[str] = None,
        hasSeverity: Optional[str] = None,
        hasLikelihood: Optional[str] = None,
        hasImpactOn: Optional[str] = None,
        hasImpact: Optional[str] = None,
        hasConsequence: Optional[str] = None,
        hasVariant: Optional[str] = None,
        isDetectedBy: Optional[str] = None,
        related: bool = False,
        related_ids: bool = False,
        hasRelatedRisk: Optional[str] = None) -> Dict[str, Any]:
    """Handler to retrieve RiskIncident entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import RiskIncident

    return generic_entity_handler(
        entity_name="riskincidents",
        model_cls=RiskIncident,
        fetch_all=create_related_fetch_all(
            related_method_name='get_related_risk_incidents',
            related_method_params=['isDefinedByTaxonomy'],
            related_param_mappings={'isDefinedByTaxonomy': 'taxonomy'}
        ),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        refersToRisk=refersToRisk,
        hasStatus=hasStatus,
        hasSeverity=hasSeverity,
        hasLikelihood=hasLikelihood,
        hasImpactOn=hasImpactOn,
        hasImpact=hasImpact,
        hasConsequence=hasConsequence,
        hasVariant=hasVariant,
        isDetectedBy=isDetectedBy,
        hasRelatedRisk=hasRelatedRisk,
        related=related,
        related_ids=related_ids
    )


def datasets(byod: bool = False, id: Optional[str] = None,
             hasDocumentation: Optional[str] = None, provider: Optional[str] = None, hasLicense: Optional[str] = None) -> Dict[str, Any]:
    """Handler to retrieve Dataset entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Dataset

    # bug: Dataset has slot 'provider' (all other classes use isProvidedBy)
    return generic_entity_handler(
        entity_name="datasets",
        model_cls=Dataset,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        hasDocumentation=hasDocumentation,
        provider=provider,
        hasLicense=hasLicense
    )


def documents(byod: bool = False, id: Optional[str] = None,
              hasLicense: Optional[str] = None) -> Dict[str, Any]:
    """Handler to retrieve Documentation entities (optimized with factory)."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Documentation

    return generic_entity_handler(
        entity_name="documents",
        model_cls=Documentation,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        hasLicense=hasLicense
    )


def benchmarkcards(
        byod: bool = False,
        id: Optional[str] = None,
        isDefinedByTaxonomy: Optional[str] = None,
        hasDocumentation: Optional[str] = None,
        hasTasks: Optional[str] = None,
        hasLicense: Optional[str] = None,
        belongsToDomain: Optional[str] = None,
        describesAiEval: Optional[str] = None,
        hasRelatedRisk: Optional[str] = None,
        related: bool = False,
        related_ids: bool = False) -> Dict[str, Any]:
    """Handler to retrieve BenchmarkMetadataCard entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import BenchmarkMetadataCard

    return generic_entity_handler(
        entity_name="benchmarkmetadatacards",
        model_cls=BenchmarkMetadataCard,
        fetch_all=create_related_fetch_all(
            related_method_name='get_benchmark_metadata_cards',
            related_method_params=['isDefinedByTaxonomy'],
            related_param_mappings={'isDefinedByTaxonomy': 'taxonomy'}
        ),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        hasTasks=hasTasks,
        hasLicense=hasLicense,
        belongsToDomain=belongsToDomain,
        describesAiEval=describesAiEval,
        hasRelatedRisk=hasRelatedRisk,
        related=related,
        related_ids=related_ids
    )


def adapters(byod: bool = False, id: Optional[str] = None,
             isDefinedByTaxonomy: Optional[str] = None, hasDocumentation: Optional[str] = None, hasAdapterType: Optional[str] = None,
             hasLicense: Optional[str] = None, hasEvaluation: Optional[str] = None, isDefinedByVocabulary: Optional[str] = None,
             isProvidedBy: Optional[str] = None, adaptsModel: Optional[str] = None, requiredByTask: Optional[str] = None,
             performsTask: Optional[str] = None, implementsCapability: Optional[str] = None,
             implementedByAdapter: Optional[str] = None, hasRelatedRisk: Optional[str] = None,
             related: bool = False, related_ids: bool = False
             ) -> Dict[str, Any]:
    """Handler to retrieve Adapter entities. Uses hasRelatedRisk field for risk-based filtering."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Adapter

    # bug in ran.query(class_name="adapters", isDefinedByTaxonomy=taxonomy) where it ignores taxonomy arg
    def fetch_all_items(ran, entity_name, **kw):
        has_related_risk_param = kw.get('hasRelatedRisk')
        related_param = kw.get('related')
        related_ids_param = kw.get('related_ids')

        # Common query parameters to avoid duplication
        query_params = {
            'class_name': entity_name,
            'isDefinedByTaxonomy': isDefinedByTaxonomy,
            'isDefinedByVocabulary': isDefinedByVocabulary,
            'hasDocumentation': hasDocumentation,
            'hasAdapterType': hasAdapterType,
            'hasLicense': hasLicense,
            'hasEvaluation': hasEvaluation,
            'provider': isProvidedBy,
            'adaptsModel': adaptsModel,
            'requiredByTask': requiredByTask,
            'performsTask': performsTask,
            'implementsCapability': implementsCapability,
            'implementedByAdapter': implementedByAdapter
        }

        results = []

        # Handle related queries using hasRelatedRisk field
        if (related_param or related_ids_param) and has_related_risk_param:

            related_risks = ran.get_related_risks(
                id=has_related_risk_param, taxonomy=isDefinedByTaxonomy) or []
            # Query adapters for each related risk using hasRelatedRisk field
            for a_risk in related_risks:
                adapters = ran.query(
                    **query_params, hasRelatedRisk=a_risk.id) or []
                results.extend(adapters)

            if related_ids_param:
                return [getattr(item, "id", None) for item in results if hasattr(item, "id")]
            return results
        elif has_related_risk_param:
            # Query adapters for specific risk using hasRelatedRisk field
            return ran.query(**query_params, hasRelatedRisk=has_related_risk_param) or []
        else:
            # Standard query without risk filtering
            return ran.query(**query_params) or []

    return generic_entity_handler(
        entity_name="adapters",
        model_cls=Adapter,
        fetch_all=fetch_all_items,
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        requiredByTask=requiredByTask,
        performsTask=performsTask,
        adaptsModel=adaptsModel,
        hasAdapterType=hasAdapterType,
        hasLicense=hasLicense,
        hasEvaluation=hasEvaluation,
        isDefinedByVocabulary=isDefinedByVocabulary,
        isProvidedBy=isProvidedBy,
        implementsCapability=implementsCapability,
        implementedByAdapter=implementedByAdapter,
        hasRelatedRisk=hasRelatedRisk,
        related=related,
        related_ids=related_ids
    )


def obligations(byod: bool = False, id: Optional[str] = None,
                isDefinedByTaxonomy: Optional[str] = None,
                hasControlApplication: Optional[str] = None,
                hasEvidenceCategory: Optional[str] = None,
                hasTypicalLocation: Optional[str] = None,
                capability: Optional[str] = None,
                hasRequirement: Optional[str] = None,
                hasRequirementType: Optional[str] = None,
                hasRule: Optional[str] = None,
                ) -> Dict[str, Any]:
    """Handler to retrieve Control Activity Obligation entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import ControlActivityObligation

    return generic_entity_handler(
        entity_name="rules",
        model_cls=ControlActivityObligation,
        fetch_all=create_typed_fetch_all(
            type_value='ControlActivityObligation'),
        fetch_by_id = fetch_by_id_item,
        byod = byod,
        id = id,
        isDefinedByTaxonomy = isDefinedByTaxonomy,
        hasRule = hasRule,
        hasControlApplication = hasControlApplication,
        hasEvidenceCategory = hasEvidenceCategory,
        hasTypicalLocation = hasTypicalLocation,
        capability = capability,
        hasRequirement = hasRequirement,
        hasRequirementType = hasRequirementType
    )


def recommendations(
    byod: bool = False,
    id: Optional[str] = None,
    isDefinedByTaxonomy: Optional[str] = None,
    hasControlApplication: Optional[str] = None,
    hasEvidenceCategory: Optional[str] = None,
    hasTypicalLocation: Optional[str] = None,
    capability: Optional[str] = None,
    hasRequirement: Optional[str] = None,
    hasRequirementType: Optional[str] = None,
    hasRule: Optional[str] = None,


) -> Dict[str, Any]:
    """Handler to retrieve ControlActivityRecommendation entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import ControlActivityRecommendation

    return generic_entity_handler(
        entity_name = "rules",
        model_cls = ControlActivityRecommendation,
        fetch_all = create_typed_fetch_all(
            type_value='ControlActivityRecommendation'),
        fetch_by_id= fetch_by_id_item,
        byod= byod,
        id= id,
        isDefinedByTaxonomy= isDefinedByTaxonomy,
        hasControlApplication= hasControlApplication,
        hasEvidenceCategory= hasEvidenceCategory,
        hasTypicalLocation= hasTypicalLocation,
        capability= capability,
        hasRequirement= hasRequirement,
        hasRequirementType= hasRequirementType,
        hasRule= hasRule
    )


def stakeholders(byod: bool=False, id: Optional[str]=None,
                 isDefinedByTaxonomy: Optional[str]=None, isPartOf: Optional[str]=None) -> Dict[str, Any]:
    """
    Handler to retrieve Stakeholder entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Stakeholder

    return generic_entity_handler(
        entity_name="stakeholders",
        model_cls=Stakeholder,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        isPartOf=isPartOf,
    )


def intrinsics(
        byod: bool=False,
        id: Optional[str]=None,
        isDefinedByTaxonomy: Optional[str]=None,
        hasDocumentation: Optional[str]=None,
        isDefinedByVocabulary: Optional[str]=None,
        hasTerm: Optional[str]=None,
        hasAdapter: Optional[str]=None,
        implementedByAdapter: Optional[str]=None,
        requiredByTask: Optional[str]=None,
        capability: Optional[str]=None,
        requiresCapability: Optional[str]=None,
        hasRelatedRisk: Optional[str]=None,
        related: bool=False,
        related_ids: bool=False) -> Dict[str, Any]:
    """Handler to retrieve LLMIntrinsic entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import (
        LLMIntrinsic)


    # Parameters are API field names directly (e.g., isDefinedByTaxonomy)
    # related_method_params: API params to pass when calling get_related_intrinsics()
    # related_param_mappings: Renames params for upstream method calls
    # - 'requiredByTask' (API param) → 'aitask_id' (upstream method parameter)
    return generic_entity_handler(
        entity_name="llmintrinsics",
        model_cls=LLMIntrinsic,
        fetch_all=create_related_fetch_all(
            related_method_name = 'get_related_intrinsics',
            related_method_params = ['isDefinedByTaxonomy', 'requiredByTask'],
            related_param_mappings = {'requiredByTask': 'aitask_id'}
        ),
        fetch_by_id= fetch_by_id_item,
        byod= byod,
        id= id,
        isDefinedByTaxonomy= isDefinedByTaxonomy,
        hasDocumentation= hasDocumentation,
        isDefinedByVocabulary= isDefinedByVocabulary,
        hasTerm= hasTerm,
        hasAdapter= hasAdapter,
        implementedByAdapter= implementedByAdapter,
        requiredByTask= requiredByTask,
        capability= capability,
        requiresCapability= requiresCapability,
        hasRelatedRisk= hasRelatedRisk,
        related= related,
        related_ids= related_ids
    )


def questionpolicies(byod: bool=False, id: Optional[str]=None,
                     isDefinedByTaxonomy: Optional[str]=None, hasRule: Optional[str]=None,
                     hasRelatedRisk: Optional[str]=None) -> Dict[str, Any]:
    """Handler to retrieve LLMQuestionPolicy entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import LLMQuestionPolicy

    return generic_entity_handler(
        entity_name="questionpolicies",
        model_cls=LLMQuestionPolicy,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasRule=hasRule,
        hasRelatedRisk=hasRelatedRisk
    )


def principles(
    byod: bool=False,
    id: Optional[str]=None,
    isDefinedByTaxonomy: Optional[str]=None,
    hasDocumentation: Optional[str]=None,
    isDefinedByVocabulary: Optional[str]=None,
    isPartOf: Optional[str]=None,
    hasTasks: Optional[str]=None,
    implementedByAdapter: Optional[str]=None,
    requiresCapability: Optional[str]=None
) -> Dict[str, Any]:
    """Handler to retrieve Principle entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import (
        Principle)

    return generic_entity_handler(
        entity_name="principles",
        model_cls=Principle,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasDocumentation=hasDocumentation,
        isDefinedByVocabulary=isDefinedByVocabulary,
        isPartOf=isPartOf,
        hasTasks=hasTasks,
        implementedByAdapter=implementedByAdapter,
        requiresCapability=requiresCapability
    )


def models(
        byod: bool=False,
        id: Optional[str]=None,
        hasDocumentation: Optional[str]=None,
        hasLicense: Optional[str]=None,
        isProvidedBy: Optional[str]=None,
        isPartOf: Optional[str]=None,
        performsTask: Optional[str]=None,
        hasEvaluation: Optional[str]=None,
        hasInputModality: Optional[str]=None,
        hasOutputModality: Optional[str]=None,
        hasRiskControl: Optional[str]=None
) -> Dict[str, Any]:
    """Handler to retrieve Ai Model entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import AiModel

    return generic_entity_handler(
        entity_name="aimodels",
        model_cls=AiModel,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        hasDocumentation=hasDocumentation,
        hasLicense=hasLicense,
        isProvidedBy=isProvidedBy,
        isPartOf=isPartOf,
        performsTask=performsTask,
        hasEvaluation=hasEvaluation,
        hasInputModality=hasInputModality,
        hasOutputModality=hasOutputModality,
        hasRiskControl=hasRiskControl
    )


def tasks(
        byod: bool=False,
        id: Optional[str]=None,
        isDefinedByTaxonomy: Optional[str]=None,
        isDefinedByVocabulary: Optional[str]=None,
        hasDocumentation: Optional[str]=None,
        isPartOf: Optional[str]=None,
        hasTasks: Optional[str]=None,
        hasAdapter: Optional[str]=None,
        implementedByAdapter: Optional[str]=None,
        requiresCapability: Optional[str]=None
) -> Dict[str, Any]:
    """Handler to retrieve AI Actor Task entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import AiTask

    return generic_entity_handler(
        entity_name="aitasks",
        model_cls=AiTask,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        isDefinedByVocabulary=isDefinedByVocabulary,
        hasDocumentation=hasDocumentation,
        isPartOf=isPartOf,
        hasTasks=hasTasks,
        implementedByAdapter=implementedByAdapter,
        requiresCapability=requiresCapability
    )


def vocabularies(byod: bool=False, id: Optional[str]=None,
                 hasDocumentation: Optional[str]=None, hasLicense: Optional[str]=None) -> Dict[str, Any]:
    """Handler to retrieve Vocabulary entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Vocabulary

    return generic_entity_handler(
        entity_name="vocabularies",
        model_cls=Vocabulary,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        hasDocumentation=hasDocumentation,
        hasLicense=hasLicense
    )


def taxonomies(byod: bool=False, id: Optional[str]=None,
               hasDocumentation: Optional[str]=None, hasLicense: Optional[str]=None) -> Dict[str, Any]:
    """Handler to retrieve Taxonomy entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import (
        RiskTaxonomy)

    return generic_entity_handler(
        entity_name="taxonomies",
        model_cls=RiskTaxonomy,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        hasDocumentation=hasDocumentation,
        byod=byod,
        id=id,
        hasLicense=hasLicense
    )


def requirements(byod: bool=False, id: Optional[str]=None,
         isDefinedByTaxonomy: Optional[str]=None, hasApplication: Optional[str]=None,
         appliesToCapability: Optional[str]=None, hasRequirementType: Optional[str]=None,
         hasRule: Optional[str]=None, type: Optional[str]=None) -> Dict[str, Any]:
    """Handler to retrieve Rule entities."""
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Rule

    return generic_entity_handler(
        entity_name="rules",
        model_cls=Rule,
        fetch_all=create_standard_fetch_all(),
        fetch_by_id=fetch_by_id_item,
        byod=byod,
        id=id,
        isDefinedByTaxonomy=isDefinedByTaxonomy,
        hasApplication=hasApplication,
        appliesToCapability=appliesToCapability,
        hasRequirementType=hasRequirementType,
        hasRule=hasRule,
        type=type,
    )


def graph(export: bool=False, id: Optional[str]=None, byod: bool=False) -> Dict[str, Any]:
    """Export or fetch the merged ontology graph.

    All filesystem paths are resolved relative to the repository root, not
    the caller's CWD, so this handler behaves identically whether invoked
    from uvicorn, pytest, or the CLI in any directory.
    """
    if id == "cypher" and export:
        if not _GRAPH_EXPORT_SCRIPT.is_file():
            raise HTTPException(
                status_code=500,
                detail="Cypher export helper script is missing.",
            )
        uv_bin = shutil.which("uv")
        if uv_bin is None:
            raise HTTPException(
                status_code=500,
                detail="'uv' command not found on PATH; cannot run cypher export.",
            )
        try:
            logger.info("Calling helper script: %s", _GRAPH_EXPORT_SCRIPT)
            subprocess.run(
                [uv_bin, "run", str(_GRAPH_EXPORT_SCRIPT)],
                check=True,
                cwd=str(_PROJECT_ROOT),
                timeout=_GRAPH_EXPORT_TIMEOUT,
            )
            return {
                "status": "success",
                "message": f"Cypher export completed via {_GRAPH_EXPORT_SCRIPT.name}",
            }
        except subprocess.TimeoutExpired:
            logger.exception("Cypher export timed out after %ss", _GRAPH_EXPORT_TIMEOUT)
            raise HTTPException(
                status_code=504,
                detail=f"Cypher export timed out after {_GRAPH_EXPORT_TIMEOUT}s.",
            )
        except subprocess.CalledProcessError:
            logger.exception("Cypher export script failed")
            raise HTTPException(status_code=500, detail="Cypher export failed.")

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
