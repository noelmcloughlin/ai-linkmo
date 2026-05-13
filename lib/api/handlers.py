"""Business logic for AI-LinkMO API handlers.

Usage:
    from lib.api.handlers import actions, evaluations, ...

Bug: python -c "from ai_atlas_nexus import AIAtlasNexus"  # Hangs
"""
from pathlib import Path
from typing import Any, Dict, Optional

import aiofiles
from fastapi import HTTPException, Request
from fastapi.responses import FileResponse

from lib.cli.utils import (
    create_related_fetch_all,
    create_standard_fetch_all,
    create_typed_fetch_all,
    fetch_by_id_item,
    generic_entity_handler,
    initialize_ran,
    clear_ran_cache
)

# Constants
BYOD_PATH = "./byo/data"
BYO_BASE_DIR = Path(__file__).parent.parent.parent / "byo" / "data"


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
    """Handler to retrieve AiEval entities."""
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


def graph(export: bool=False, id: Optional[str]=None, byod: bool=False) -> Dict[str, Any]:

    my_output_dir = 'graph/'
    if id == "cypher" and export:
        import subprocess
        script_path = "./graph/cypher/export.py"
        try:
            print(f"\n# Calling helper script: {script_path}")
            cmd = ["uv", "run", script_path]
            subprocess.run(cmd, check=True)
            return {"status": "success", "message": f"Cypher export completed via {script_path}"}
        except Exception as e:
            error_msg = f"Failed to run {script_path}: {e}"
            print(f"[red]{error_msg}[/red]")
            return {"status": "error", "message": error_msg}

    elif export:
        # Initialize AIAtlasNexus instance
        ran = initialize_ran(byod)

        print("\n# Exporting graph data...")
        ran.export(my_output_dir)
        success_msg = f"Graph exported to: ./{my_output_dir}ai-risk-ontology.yaml"
        print(f"\n# {success_msg}")
        return {"status": "success", "message": success_msg, "path": f"{my_output_dir}ai-risk-ontology.yaml"}

    else:
        my_file = my_output_dir + 'ai-risk-ontology.yaml'
        print(f"\n# No argument passed - printing entire graph: {my_file}")
        import os
        yaml_file = os.path.join(my_file)
        if os.path.exists(yaml_file):
            with open(yaml_file, 'r') as file:
                content = file.read()
                print(content)
                return {"status": "success", "message": "Graph data retrieved", "file": my_file, "content_length": len(content)}
        else:
            error_msg = f"File 'ai-risk-ontology.yaml' not found in '{my_output_dir}'."
            print(f"[red]{error_msg}[/red]")
            return {"status": "error", "message": error_msg}


def schemaview(introspect: bool=True) -> None:
    """View and introspect the schema using the AIAtlasNexus library.
    """
    from rich import print as rprint
    from rich.pretty import pretty_repr
    if not introspect:
        rprint("\n# No argument passed, assume '--introspect'")

    from linkml_runtime.utils.schemaview import SchemaView
    from linkml_runtime.linkml_model.meta import ClassDefinition
    from ai_atlas_nexus.library import AIAtlasNexus

    rprint("The SchemaView class in the linkml-runtime provides a method for dynamically")
    rprint("introspecting and manipulating schemas. This can be used to programatically")
    rprint("explore or edit the AI Atlas Nexus Schema.")
    rprint("See https://linkml.io/linkml/developers/schemaview.html\n")

    # Initialize AIAtlasNexus instance to retrieve SCHEMA
    ran = initialize_ran()

    # Get the schema view
    rprint("\nGET SCHEMA VIEW")
    view = ran.get_schema()  # get the schemaview object

    rprint("\nPrint schema name and description.")
    rprint({"name": view.schema.name})
    rprint({"description": view.schema.description})

    rprint("\nPrint number of classes, slots, and subsets in the schema.")
    rprint({
        "classes": len(view.all_classes()),
        "slots": len(view.all_slots()),
        "subsets": len(view.all_subsets())
    })

    rprint("\nClass ancestors: self and any other classes in its inheritance hierarchy.")
    rprint(pretty_repr(view.class_ancestors("Risk")))

    rprint("\nCURIEs or URIs of a class's ancestors.")
    rprint(pretty_repr([view.get_uri(c)
           for c in view.class_ancestors("Risk")]))

    rprint("\nCURIEs or URIs of a class's ancestors with expanded URIs.")
    rprint(pretty_repr([view.get_uri(c, expand=True)
           for c in view.class_ancestors("Risk")]))

    rprint("\nAncestors of a class without mixins.")
    rprint(pretty_repr(view.class_ancestors("Risk", mixins=False)))

    rprint("\nAncestors of a slot.")
    rprint(pretty_repr(view.slot_ancestors("refersToRisk")))

    rprint("\nChildren of a slot.")
    rprint(pretty_repr(view.slot_children("refersToRisk")))


def crosswalk(byod: bool = False, isDefinedByTaxonomy: Optional[str] = None,
              isDefinedByTaxonomy2: Optional[str] = None, export: bool = False) -> Dict[str, Any]:
    """
    Crosswalk between two taxonomies.
    """
    # Initialize AIAtlasNexus instance
    ran = initialize_ran(byod, isDefinedByTaxonomy)

    # Understand what taxonomies are available to us
    print(
        f"# Taxonomies : {len(ran.query(class_name='taxonomies'))}")
    print(
        f"# Taxonomy IDs : {[x.id for x in ran.query(class_name='taxonomies')]}")

    if not (isDefinedByTaxonomy and isDefinedByTaxonomy2):
        error_msg = "Both isDefinedByTaxonomy and isDefinedByTaxonomy2 must be provided."
        print(f"Error: {error_msg}")
        return {"error": error_msg}

    from numpy import nan
    from collections import defaultdict
    import pandas as pd
    from pydantic import BaseModel
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import Risk

    # Display full column width
    pd.set_option('display.max_colwidth', None)

    print(
        f"\nComparing taxonomy '{isDefinedByTaxonomy}' with taxonomy '{isDefinedByTaxonomy2}'...")

    class RiskSimplified(BaseModel):
        id: str
        name: str
        isPartOf: str | None
        isDefinedByTaxonomy: str | None

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
                ran.get_risk(
                    id=risk_id) for risk_id in list_of_risk_ids if risk_id is not None) if item is not None]
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
            if list_risks is not None:
                return [
                    id for id in list_risks if ran.get_risk(
                        id=id) is not None and ran.get_risk(
                        id=id).isDefinedByTaxonomy == taxonomy_2]
            else:
                return None

        df['close_mappings'] = df['close_mappings'].apply(filter_by_taxonomy)
        df['exact_mappings'] = df['exact_mappings'].apply(filter_by_taxonomy)
        df['broad_mappings'] = df['broad_mappings'].apply(filter_by_taxonomy)
        df['narrow_mappings'] = df['narrow_mappings'].apply(filter_by_taxonomy)
        df['related_mappings'] = df['related_mappings'].apply(filter_by_taxonomy)
        df.rename(columns={"id": "RAN ID"})
        df['expanded_risks'] = df.apply(lambda row: expand_risks((row['close_mappings'] or []) +
                                                                 (row['exact_mappings'] or []) +
                                                                 (row['broad_mappings'] or []) +
                                                                 (row['narrow_mappings'] or []) +
                                                                 (row['related_mappings'] or [])), axis=1)
        return df

    # Use the helper functions in the crosswalk function
    print(
        f"\nConstructing crosswalk between taxonomy '{isDefinedByTaxonomy}' and taxonomy '{isDefinedByTaxonomy2}'...")
    df = construct_crosswalk_df(isDefinedByTaxonomy, isDefinedByTaxonomy2)
    if export:
        my_output_dir = 'graph/'
        print("\n# Exporting crosswalk data...")
        df.to_csv(
            f"{my_output_dir}crosswalk_{isDefinedByTaxonomy}_to_{isDefinedByTaxonomy2}.csv",
            index=False)
        print(
            f"\n# Crosswalk exported to: ./{my_output_dir}crosswalk_{isDefinedByTaxonomy}_to_{isDefinedByTaxonomy2}.csv")
        return {
            "exported": True,
            "path": f"{my_output_dir}crosswalk_{isDefinedByTaxonomy}_to_{isDefinedByTaxonomy2}.csv"}
    else:
        # Return the DataFrame as a list of dicts for API/JSON use
        return {"crosswalk": df.to_dict(orient="records")}


def ares(risks, inference_engine, target):
    """
    Run ARES evaluation.
    """
    from ai_atlas_nexus.ai_risk_ontology.datamodel.ai_risk_ontology import (
        Risk)
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
        engine='vllm',
        parameters='max_tokens=1000, temperature=0.7',
        byod=False,
        taxonomy='ibm-risk-atlas',
        usecase=None,
        id=None,
):

    if engine == 'vllm':
        from ai_atlas_nexus.blocks.inference import VLLMInferenceEngine
        from ai_atlas_nexus.blocks.inference.params import VLLMInferenceEngineParams, InferenceEngineCredentials
    elif engine == 'wml':
        from ai_atlas_nexus.blocks.inference import WMLInferenceEngine
        from ai_atlas_nexus.blocks.inference.params import WMLInferenceEngineParams, InferenceEngineCredentials
    elif engine == 'ollama':
        from ai_atlas_nexus.blocks.inference import OllamaInferenceEngine
        from ai_atlas_nexus.blocks.inference.params import OllamaInferenceEngineParams, InferenceEngineCredentials
    elif engine:
        print(f"[red]Invalid inference engine specified: {engine}[/red]")
        return
    print(f"Using {engine.title()}InferenceEngine for inference.")

    parameters = VLLMInferenceEngineParams(**eval(f"dict({parameters})")),
    inference_engine = VLLMInferenceEngine(
        model_name_or_path=id,
        gpu_memory_utilization="0.8",
        # credentials=InferenceEngineCredentials(
        # api_url="VLLM_API_URL", api_key="VLLM_API_KEY"
        # ),
        parameters=VLLMInferenceEngineParams(**eval(f"dict({parameters})")),
    )

    # Initialize AIAtlasNexus instance
    ran = initialize_ran(byod, taxonomy)
    risks = ran.identify_risks_from_usecases(
        usecases=[usecase],
        inference_engine=inference_engine,
        taxonomy=taxonomy,
    )

    print(f"\n# Inferred risks for usecase '{usecase}':")
    print(f"Number of inferred risks: {len(risks)}")


async def byo_put(filename: str, request: Request) -> Dict[str, str]:
    """Handler to upload a file to 'byo/data/'."""
    BYO_BASE_DIR.mkdir(parents=True, exist_ok=True)
    file_path = BYO_BASE_DIR / filename
    backup_path = file_path.with_suffix(file_path.suffix + '.bak')

    try:
        # Backup existing file before overwriting
        if file_path.exists():
            import shutil
            shutil.copy2(file_path, backup_path)

        # Write uploaded file
        body = await request.body()
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(body)

        # Clear BYOD cache so next request picks up new data
        clear_ran_cache(byod=True)
        
        return {"detail": f"File '{filename}' uploaded successfully."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def byo(filename: str) -> FileResponse:
    """Handler to serve files from 'byo/data/'."""
    file_path = BYO_BASE_DIR / filename

    if not file_path.is_file():
        raise HTTPException(
            status_code=404,
            detail=f"File '{filename}' not found."
        )

    return FileResponse(
        path=str(file_path),
        media_type='application/octet-stream',
        filename=filename
    )
