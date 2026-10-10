"""
CLI Utility Functions

PERFORMANCE NOTE:
This module uses lazy importing for AIAtlasNexus to optimize startup time.
- API mode (default): ~1-2s execution time - doesn't load ai_atlas_nexus
- Local mode: ~14s execution time - loads ai_atlas_nexus when needed

The ai_atlas_nexus library takes ~10.6s to import (includes PyTorch), so we only
import it when actually needed (local mode). This makes API mode 6-15x faster.
"""

from pathlib import Path
from typing import Any, Callable, List, Tuple, Dict, Optional, TYPE_CHECKING
import json
import logging
from fastapi import HTTPException
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

# Lazy import for AIAtlasNexus - only imported when actually needed (local mode)
# This speeds up API mode by ~10 seconds since it doesn't load ai_atlas_nexus library
if TYPE_CHECKING:
    from ai_atlas_nexus import AIAtlasNexus

# Absolute path to the bundled BYO data directory. Using an absolute path
# avoids the silent "loads wrong data when CWD != repo root" trap of a
# relative "./byo/data" path.
BYOD_PATH = str((Path(__file__).resolve().parent.parent.parent / "byo" / "data"))

# Module-level cache for AIAtlasNexus instances
# Only two instances needed: byod=False (default) and byod=True (custom data)
_ran_cache: Dict[bool, Any] = {}  # Type changed to Any to avoid import at module level

# Initialize module-level logger
logger = logging.getLogger(__name__)

# Single stderr-bound Rich console reused by all error rendering. Writing to
# stderr avoids corrupting JSON output that callers may pipe into ``jq`` or
# similar tools.
_ERR_CONSOLE: Console = Console(stderr=True)


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

    Output is routed to stderr (via a module-level Console) so it never
    corrupts JSON results that may be piped to other tools.

    Args:
        title: Error panel title
        message: Error message text
        style: Text style for message
    """
    _ERR_CONSOLE.print(
        Panel(
            Text(message, style=style),
            title=f"[b red]{title}",
            border_style="red",
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

    Behaviour:

    * When ``AI_ATLAS_API_URL`` is set (test suite, scripted runs, anyone
      who explicitly configured a URL), trust it and skip the ``/health``
      round-trip entirely. This removes the ``GET /health`` noise that
      otherwise prefixes every single API call. If the URL turns out to
      be dead the caller catches ``ConnectionError`` and invokes
      :func:`invalidate_server_url_cache` to force a re-probe on the
      next call.
    * Otherwise, probe ``/health`` on ``base_url`` then the configured
      common ports until something answers. Successful detections are
      cached for :data:`_DETECTION_CACHE_SECONDS` so a burst of CLI
      calls only pays the probe cost once.

    Args:
        base_url: Initial URL to try
        common_ports: List of common ports to try (e.g., [8000, 8080, 5000, 8888])
        force_refresh: If True, bypass cache, env shortcut, and re-detect

    Returns:
        Working server URL, or None if no server found
    """
    global _detected_server_url, _last_detection_time

    import os
    import time
    import requests
    from urllib.parse import urlparse

    current_time = time.time()

    # Trust an explicit env override unless the caller asked for a forced
    # re-detection (typically after a ConnectionError on the previous call).
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


def invalidate_server_url_cache() -> None:
    """Force the next :func:`detect_server_url` call to re-probe.

    Useful after a request raises ``ConnectionError`` so a subsequent
    invocation doesn't keep hitting the same dead URL until the TTL
    expires.
    """
    global _detected_server_url, _last_detection_time
    _detected_server_url = None
    _last_detection_time = 0


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
    # Check module cache first (faster, no imports needed)
    if byod in _ran_cache:
        return _ran_cache[byod]

    # Try FastAPI state if the server module is currently loaded. Re-check
    # ``sys.modules`` on every call so a server import that happens after
    # the first CLI call is still detected (previous code cached the result
    # exactly once per process and could miss it).
    import sys
    if 'lib.api.server' in sys.modules:
        try:
            from lib.api.server import ran_instances
            if byod in ran_instances:
                return ran_instances[byod]
        except (ImportError, KeyError, AttributeError):
            pass

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


def initialize_ran(byod: bool = False, taxonomy: Optional[str] = None) -> Any:  # Returns AIAtlasNexus
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
    if not taxonomy:
        return None
    resolved = ran.get_taxonomy_by_id(taxonomy)
    if resolved:
        return resolved
    # Preserve the originally requested ID in the error so the user can see
    # what they typed (previous implementation reassigned ``taxonomy`` to
    # the lookup result and always reported "None").
    raise HTTPException(
        status_code=400, detail=f"Invalid taxonomy ID: {taxonomy}"
    )


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
