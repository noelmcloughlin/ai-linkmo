"""
CLI Utility Functions

PERFORMANCE NOTE:
This module uses lazy importing for AIAtlasNexus to optimize startup time.
- API mode (default): ~1-2s execution time - doesn't load ai_atlas_nexus
- Local mode: ~14s execution time - loads ai_atlas_nexus when needed

The ai_atlas_nexus library takes ~10.6s to import (includes PyTorch), so we only
import it when actually needed (local mode). This makes API mode 6-15x faster.
"""

from typing import Any, Callable, List, Tuple, Dict, Optional, TYPE_CHECKING
import json
import logging
from fastapi import HTTPException

# Lazy import for AIAtlasNexus - only imported when actually needed (local mode)
# This speeds up API mode by ~10 seconds since it doesn't load ai_atlas_nexus library
if TYPE_CHECKING:
    from ai_atlas_nexus import AIAtlasNexus

BYOD_PATH = "./byo/data"

# Module-level cache for AIAtlasNexus instances
# Only two instances needed: byod=False (default) and byod=True (custom data)
_ran_cache: Dict[bool, Any] = {}  # Type changed to Any to avoid import at module level

# Cache for server module import check
_has_server_module: bool = False
_server_module_checked: bool = False

# Initialize module-level logger
logger = logging.getLogger(__name__)


# ============================================================================
# JSON ENCODING UTILITIES
# ============================================================================

class EnhancedJSONEncoder(json.JSONEncoder):
    """JSON encoder that handles date/datetime objects."""
    
    def default(self, obj: Any) -> Any:
        """Encode special types to JSON-serializable format.
        
        Args:
            obj: Object to encode
            
        Returns:
            JSON-serializable representation
        """
        import datetime
        if isinstance(obj, (datetime.date, datetime.datetime)):
            return obj.isoformat()
        return super().default(obj)


# ============================================================================
# DISPLAY UTILITIES
# ============================================================================

def display_error(title: str, message: str, style: str = "bold red") -> None:
    """Display formatted error message using Rich.
    
    Args:
        title: Error panel title
        message: Error message text
        style: Text style for message
    """
    from rich.console import Console
    from rich.panel import Panel
    from rich.text import Text
    
    console = Console()
    console.print(
        Panel(
            Text(message, style=style),
            title=f"[b red]{title}",
            border_style="red"
        )
    )


def display_result(result: Any, count_only: bool = False, pretty: bool = False) -> None:
    """Display handler result with rich formatting.
    
    Args:
        result: Result from handler function
        count_only: If True, only display the count value
        pretty: If True, format JSON with indentation
    """
    # Handle count-only mode
    if count_only:
        if isinstance(result, dict) and 'count' in result:
            print(result['count'])
        elif isinstance(result, dict) and 'item' in result:
            count = 1 if result['item'] is not None else 0
            print(count)
        elif isinstance(result, list):
            print(len(result))
        else:
            print(result)
        return
    
    # Format output as JSON with proper encoding
    json_str = json.dumps(
        result,
        indent=2 if pretty else None,
        ensure_ascii=False,
        cls=EnhancedJSONEncoder
    )
    if pretty:
        from rich.console import Console as _Console
        from rich.json import JSON as _RichJSON
        _Console().print(_RichJSON(json_str))
    else:
        # Use print() instead of console.print() to avoid Rich's line wrapping
        print(json_str)


# ============================================================================
# SERVER DETECTION UTILITIES
# ============================================================================

# Server URL detection cache
_detected_server_url: Optional[str] = None
_last_detection_time: float = 0
_DETECTION_CACHE_SECONDS = 60  # Cache for 1 minute


def detect_server_url(base_url: str, common_ports: List[int], force_refresh: bool = False) -> Optional[str]:
    """Detect which URL/port the API server is running on.
    
    If AI_ATLAS_API_URL is explicitly set in the environment, trust it directly
    without probing /health (the caller already knows where the server is).
    Otherwise, caches successful detection for 60 seconds to avoid repeated checks.
    Tries the provided base_url first, then common alternative ports.
    
    Args:
        base_url: Initial URL to try
        common_ports: List of common ports to try (e.g., [8000, 8080, 5000, 8888])
        force_refresh: If True, bypass cache and re-detect
        
    Returns:
        Working server URL, or None if no server found
    """
    global _detected_server_url, _last_detection_time

    import os
    import time
    import requests
    from urllib.parse import urlparse

    current_time = time.time()

    # If the URL was explicitly configured via env var, trust it without probing.
    # This avoids a /health round-trip on every subprocess invocation (e.g. in tests).
    if not force_refresh and os.environ.get("AI_ATLAS_API_URL"):
        return base_url

    # Return cached URL if recent and not forcing refresh
    if not force_refresh and _detected_server_url and (current_time - _last_detection_time) < _DETECTION_CACHE_SECONDS:
        return _detected_server_url

    # Extract scheme and host from base_url
    parsed = urlparse(base_url)
    scheme = parsed.scheme or 'http'
    host = parsed.hostname or 'localhost'

    # Build list of URLs to try (deduplicated)
    urls_to_try = [base_url]
    seen = {base_url}

    # Add common alternative ports if not already tried
    for port in common_ports:
        alt_url = f"{scheme}://{host}:{port}"
        if alt_url not in seen:
            urls_to_try.append(alt_url)
            seen.add(alt_url)
    
    # Try each URL with a quick health check
    for url in urls_to_try:
        try:
            response = requests.get(f"{url}/health", timeout=1)
            if response.status_code == 200:
                # Cache successful detection
                _detected_server_url = url
                _last_detection_time = current_time
                return url
        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
            continue
    
    return None


# ============================================================================
# AIATLLASNEXUS INSTANCE MANAGEMENT
# ============================================================================

def get_ran_instance(byod: bool = False) -> Any:  # Returns AIAtlasNexus
    """
    Get cached AIAtlasNexus instance - from FastAPI state or module cache.
    
    Instances are stateless and safe to reuse across requests.
    Uses FastAPI lifespan-managed instances when available (server context),
    otherwise falls back to module-level cache (CLI context).
    
    Lazy imports AIAtlasNexus only when actually needed for local mode.
    
    Args:
        byod: If True, use custom data from BYOD_PATH, else use default data
        
    Returns:
        Cached AIAtlasNexus instance
        
    Raises:
        HTTPException: If instance creation fails
    """
    global _has_server_module, _server_module_checked
    
    # Check module cache first (faster, no imports needed)
    if byod in _ran_cache:
        return _ran_cache[byod]
    
    # Try FastAPI state (only check once per process)
    if not _server_module_checked:
        import sys
        _has_server_module = 'lib.api.server' in sys.modules
        _server_module_checked = True
    
    if _has_server_module:
        try:
            from lib.api.server import ran_instances
            if byod in ran_instances:
                return ran_instances[byod]
        except (ImportError, KeyError, AttributeError):
            _has_server_module = False
    
    # Create new instance and cache it - lazy import here
    try:
        from ai_atlas_nexus import AIAtlasNexus
        ran = AIAtlasNexus(base_dir=BYOD_PATH) if byod else AIAtlasNexus()
        _ran_cache[byod] = ran
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to initialize AIAtlasNexus: {e}")
    
    return _ran_cache[byod]


def clear_ran_cache(byod: bool = True) -> None:
    """
    Clear cached AIAtlasNexus instance to force reload on next access.
    
    Should be called after byo_put operations that modify data files,
    so the byod instance picks up new data.
    
    Args:
        byod: Which cache to clear (typically True for BYOD instance)
    """
    # Clear module cache
    if byod in _ran_cache:
        del _ran_cache[byod]
    
    # Clear FastAPI state cache if available
    try:
        from lib.api.server import ran_instances
        if byod in ran_instances:
            # Reinitialize the instance - lazy import
            from ai_atlas_nexus import AIAtlasNexus
            ran_instances[byod] = AIAtlasNexus(base_dir=BYOD_PATH) if byod else AIAtlasNexus()
    except (ImportError, KeyError, AttributeError):
        pass


def initialize_ran(byod: bool = False, taxonomy: str = None) -> Any:  # Returns AIAtlasNexus
    """
    Initialize AIAtlasNexus instance with optional taxonomy validation.
    
    Lazy imports AIAtlasNexus only when called.
    
    Wrapper around get_ran_instance() that adds taxonomy validation.
    Use get_ran_instance() directly if taxonomy validation isn't needed.
    
    Returns the instance or raises an error if initialization fails.
    """
    ran = get_ran_instance(byod)
    if taxonomy:
        validate_taxonomy(ran, taxonomy)
    return ran


def validate_taxonomy(ran, taxonomy):
    """
    Validate taxonomy ID. Raises HTTPException if invalid.
    Returns taxonomy details if valid.
    """
    if taxonomy:
        taxonomy = ran.get_taxonomy_by_id(taxonomy)
        if taxonomy:
            return taxonomy
        raise HTTPException(
            status_code=400, detail=f"Invalid taxonomy ID: {taxonomy}")
    return None


def validate_and_serialize_entities(
        entities: List[Any], model_cls: Callable[..., Any]
) -> Tuple[List[Dict], List[str], List[Any]]:
    """
    Validate and serialize a list of entities using a Pydantic model.

    Args:
            entities: List of dicts or model instances to validate/serialize.
            model_cls: The Pydantic model class to use for validation.

    Returns:
            serialized: List of model_dump dicts for valid entities.
            errors: List of error messages for failed validations.
            objs: List of successfully validated model instances.
    """
    objs = []
    errors = []
    serialized = []
    if model_cls is None:
        errors.append(
            "Model class is not available (import failed). Check your dependencies and installation.")
        return [], errors, []
    # If entities is a list of strings (ids), just return as-is for related_ids
    if entities and all(isinstance(e, str) for e in entities):
        return entities, [], entities
    for e in entities:
        try:
            obj = model_cls(**dict(e)) if not isinstance(e, model_cls) else e
            objs.append(obj)
            serialized.append(obj.model_dump())
        except Exception as ex:
            errors.append(str(ex))
    return serialized, errors, objs

def fetch_by_id_item(ran, entity_name, id, **kw):
    """Fetch a single item by ID with optional taxonomy and document filtering.
    
    Args:
        ran: AIAtlasNexus instance
        entity_name: Name of the entity class
        id: Entity ID to fetch
        **kw: Additional filters (isDefinedByTaxonomy, document, etc.)
    
    Returns:
        Single entity instance or None if not found
    """
    taxonomy = kw.get("isDefinedByTaxonomy")  # Match parameter name used by callers
    document = kw.get("document")
    if taxonomy and entity_name != "taxonomies":
        results = ran.query(class_name=entity_name, id=id, isDefinedByTaxonomy=taxonomy, hasDocumentation=document)
    else:
        results = ran.query(class_name=entity_name, id=id, hasDocumentation=document)
    return next(iter(results), None)

def preprocess_fetch_kwargs(kw):
    """Pass through all kwargs without transformation.
    
    Note: Now that CLI uses API parameter names directly, no mapping is needed.
    This function is kept for potential future preprocessing needs.
    """
    return kw


def create_standard_fetch_all():
    """Factory function to create standard fetch_all_items functions.
    
    Returns:
        A fetch_all_items function that can be used with generic_entity_handler.
    """
    def fetch_all_items(ran, entity_name, **kw):
        kw = preprocess_fetch_kwargs(kw)
        query_args = {'class_name': entity_name}
        
        # Pass all kwargs as query parameters (API names are used directly)
        for param_key, value in kw.items():
            if value is not None and param_key not in ('related', 'related_ids'):
                query_args[param_key] = value
        
        return ran.query(**query_args)
    
    return fetch_all_items


def create_related_fetch_all(related_method_name: str,
                             related_method_params: Optional[List[str]] = None,
                             related_param_mappings: Optional[Dict[str, str]] = None):
    """Factory function to create fetch_all_items functions with related/related_ids support.
    
    Args:
        related_method_name: Name of the method on AIAtlasNexus (e.g., 'get_related_actions')
        related_method_params: List of API parameter names to pass to related method (e.g., ['isDefinedByTaxonomy'])
        related_param_mappings: Optional dict to rename parameters for upstream method calls
                               (e.g., {'requiredByTask': 'aitask_id'} maps API param to upstream param)
        
    Returns:
        A fetch_all_items function with related/related_ids support.
    """
    def fetch_all_items(ran, entity_name, **kw):
        kw = preprocess_fetch_kwargs(kw)
        risk_id = kw.get('hasRelatedRisk')
        related = kw.get('related')
        related_ids = kw.get('related_ids')
        
        results = []
        
        # Prepare method params for related calls
        method_params = {}
        if related_method_params:
            for param_name in related_method_params:
                value = kw.get(param_name)
                if value is not None:
                    # Apply parameter name mapping if provided
                    target_param = related_param_mappings.get(param_name, param_name) if related_param_mappings else param_name
                    method_params[target_param] = value
        
        # Handle related queries
        if (related or related_ids) and risk_id:
            try:
                related_risks = ran.get_related_risks(id=risk_id)
                if not related_risks:
                    return [] if not related_ids else []
                    
                related_method = getattr(ran, related_method_name)
                for a_risk in related_risks:
                    if a_risk is None:
                        continue
                    if entity_name in ('evaluations', 'llmintrinsics', 'riskincidents', 'benchmarkmetadatacards'):
                        # These upstream methods use 'risk_id' parameter
                        related_items = related_method(risk_id=a_risk.id, **method_params) or []
                    else:
                        # These upstream methods use 'id' parameter (actions, controls)
                        related_items = related_method(id=a_risk.id, **method_params) or []
                    results.extend(related_items)
                
                if related_ids:
                    return [getattr(item, "id", None) for item in results if hasattr(item, "id")]
            except (AttributeError, TypeError) as e:
                # Handle cases where risk_id is invalid and upstream methods fail
                logger.debug(f"Failed to fetch related items for entity '{entity_name}' with risk_id={risk_id}: {e}")
                return []
        elif risk_id:
            try:
                related_method = getattr(ran, related_method_name)
                if entity_name in ('evaluations', 'llmintrinsics', 'riskincidents', 'benchmarkmetadatacards'):
                    # These upstream methods use 'risk_id' parameter
                    results = related_method(risk_id=risk_id, **method_params) or []
                else:
                    # These upstream methods use 'id' parameter (actions, controls)
                    results = related_method(id=risk_id, **method_params) or []
            except (AttributeError, TypeError) as e:
                # Handle cases where risk_id is invalid and upstream methods fail
                logger.debug(f"Failed to fetch items for entity '{entity_name}' with risk_id={risk_id}: {e}")
                results = []
        else:
            # Standard query
            query_args = {'class_name': entity_name}
            # Pass all kwargs as query parameters (API names are used directly)
            for param_key, value in kw.items():
                if value is not None and param_key not in ('related', 'related_ids'):
                    query_args[param_key] = value
            results = ran.query(**query_args)
        
        return results
    
    return fetch_all_items


def create_typed_fetch_all(type_value: str):
    """Factory function to create fetch_all_items with type filtering.
    
    For entity subclasses that need type filtering to avoid mixing with
    sibling classes (e.g., ControlActivityObligation vs Requirement under Rule).

    Bug/enhancement suggestion: The ran.query() function applies all filters at once
    causing AttributeErrors on sibling classes that don't have the same attributes.

    Workaround: Use two-phase filtering: First filters by type to get the correct
    subclass, then apply python filtering.

    Args:
        type_value: The type value to filter by (e.g., 'ControlActivityObligation')
        
    Returns:
        A fetch_all_items function with type filtering.
    """
    def fetch_all_items(ran, entity_name, **kw):
        kw = preprocess_fetch_kwargs(kw)
        
        # Phase 1: Filter by type only to get correct subclass
        results = ran.query(class_name=entity_name, type=type_value)
        
        # Phase 2: Apply Python-level filtering for API parameters
        for param_key, value in kw.items():
            if value is not None and param_key not in ('related', 'related_ids'):
                # Filter results based on the parameter
                results = [
                    r for r in results
                    if hasattr(r, param_key) and matches_filter(getattr(r, param_key), value)
                ]
        
        return results
    return fetch_all_items


def matches_filter(field_value, filter_value):
    """Helper to check if a field matches a filter value.
    
    Handles both single values and lists (for multi-valued fields).
    """
    if isinstance(field_value, list):
        return filter_value in field_value
    return field_value == filter_value

def generic_entity_handler(
    *,
    entity_name: str,
    model_cls: Callable[..., Any],
    fetch_all: Callable[..., List[Any]],
    fetch_by_id: Optional[Callable[..., Any]] = None,
    byod: bool = False,
    id: Optional[str] = None,
    preprocess_fetch_kwargs: Optional[Callable[[dict], dict]] = None,
    **fetch_kwargs
) -> Dict:
    """
    Generic handler for entity endpoints, with optional preprocessing for fetch kwargs.
    Uses cached AIAtlasNexus instances for optimal performance.
    
    This handler receives API field names (e.g., isDefinedByTaxonomy, hasDocumentation)
    from the handler functions and passes them through directly.
    """
    ran = get_ran_instance(byod)
    
    # Validate taxonomy if provided
    taxonomy_value = fetch_kwargs.get('isDefinedByTaxonomy')
    if taxonomy_value:
        validate_taxonomy(ran, taxonomy_value)
    
    # Preprocess fetch_kwargs if needed
    if preprocess_fetch_kwargs:
        fetch_kwargs = preprocess_fetch_kwargs(fetch_kwargs)
    
    # Fetch by ID if provided and fetch_by_id is available
    if id and fetch_by_id:
        entity = fetch_by_id(ran, entity_name, id, **fetch_kwargs)
        # If fetch_by_id returns a list (for related/related_ids), treat as multiple entities
        if isinstance(entity, list):
            serialized, errors, objs = validate_and_serialize_entities(entity, model_cls)
            return {
                "items": serialized,
                "count": len(serialized),
                "validation_errors": errors
            }
        elif entity:
            try:
                item_dict = entity.model_dump() if hasattr(
                    entity, "model_dump") else entity.__dict__
                return {"item": item_dict}
            except Exception as e:
                return {"item": None, "validation_errors": [str(e)]}
        else:
            return {"item": None}
    
    # Fetch all entities
    # Pass all kwargs including 'related' and 'related_ids' for handlers that need them
    try:
        entities = fetch_all(ran, entity_name, **fetch_kwargs)
        serialized, errors, objs = validate_and_serialize_entities(
            entities, model_cls)
        return {
            "items": serialized,
            "count": len(serialized),
            "validation_errors": errors
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch {entity_name}: {e}")
