"""
AI-LinkMO FastAPI Server (Dynamic Generation)

Server to automatically generate all endpoints.
Uses the OpenAPI spec as single source of truth.
"""

import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Dict

from ai_atlas_nexus import AIAtlasNexus
from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from lib.api import handlers
from lib.api.server_dynamic import register_endpoints_from_openapi

logger = logging.getLogger(__name__)

# Global cache for AIAtlasNexus instances (shared across all requests)
# Two instances: byod=False (default data) and byod=True (custom BYOD data)
ran_instances: Dict[bool, AIAtlasNexus] = {}

# Absolute path used for the BYOD instance.
BYOD_PATH = str(handlers.BYO_BASE_DIR)

# Project root (same anchor handlers.py uses).
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# CORS configuration via env. Default to localhost dev origins instead of "*",
# which together with a credentials policy avoids accidentally exposing the
# demo API to arbitrary cross-origin callers.
_CORS_ORIGINS_ENV = os.getenv("AI_LINKMO_CORS_ORIGINS", "")
if _CORS_ORIGINS_ENV.strip() == "*":
    CORS_ORIGINS: list[str] = ["*"]
elif _CORS_ORIGINS_ENV:
    CORS_ORIGINS = [o.strip() for o in _CORS_ORIGINS_ENV.split(",") if o.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]

# Browsers send Origin: null for file:// pages and some sandboxed iframes. We
# never want that by default - it's a known CSRF/XS-leak vector - but allow
# operators to opt in for local file-based demos.
if os.getenv("AI_LINKMO_CORS_ALLOW_NULL") == "1" and "null" not in CORS_ORIGINS:
    CORS_ORIGINS.append("null")


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Set a sensible default ``Cache-Control`` on responses.

    GET responses are marked ``no-cache`` so a refreshed BYOD upload is
    immediately visible (the data behind the API is mutable). Non-GET
    responses are marked ``no-store`` to keep mutating responses off any
    intermediate caches.
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if "cache-control" not in (h.lower() for h in response.headers.keys()):
            if request.method == "GET":
                response.headers["Cache-Control"] = "no-cache"
            else:
                response.headers["Cache-Control"] = "no-store"
        return response


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle: initialize shared resources on startup.

    Creates and caches AIAtlasNexus instances that are reused across all requests
    for optimal performance. Instances are stateless for read operations.
    Also registers dynamic endpoints from OpenAPI spec.
    """
    # Register dynamic endpoints from OpenAPI spec (only at server startup, not on import)
    logger.info("Generating endpoints from OpenAPI specification...")
    register_endpoints_from_openapi(app, verbose=True)
    logger.info("Initializing AIAtlasNexus instances...")
    # The default instance is required - if it fails to build the API can't
    # serve any real traffic. Surface that as a startup failure rather than
    # silently returning empty results.
    try:
        ran_instances[False] = AIAtlasNexus()  # Default data
        logger.info("Default instance ready")
    except Exception:
        logger.exception("Failed to initialize default AIAtlasNexus instance")
        raise

    # The BYOD instance is optional - if there's no BYOD data yet we still
    # want the server up.
    try:
        ran_instances[True] = AIAtlasNexus(base_dir=BYOD_PATH)  # BYOD data
        logger.info("BYOD instance ready")
    except Exception:
        logger.exception("Failed to initialize BYOD AIAtlasNexus instance")

    logger.info("Server ready with %d cached instance(s)", len(ran_instances))
    yield

    # Cleanup on shutdown
    logger.info("Shutting down AIAtlasNexus instances...")
    ran_instances.clear()


app = FastAPI(
    title="AI-LinkMO API Demo",
    description="REST API for AI-LinkMO Demo operations (dynamically generated from OpenAPI spec)",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST", "PUT", "OPTIONS"],
    allow_headers=["*"],
)
app.add_middleware(CacheControlMiddleware)


@app.get("/", include_in_schema=False)
def redirect_root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
def health():
    """Liveness probe. Always 200 once the process is up."""
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
def ready():
    """Readiness probe - 200 only when the default AIAtlasNexus is loaded."""
    if False in ran_instances:
        return {"status": "ready", "instances": sorted(map(str, ran_instances.keys()))}
    return JSONResponse(
        status_code=503,
        content={"status": "unavailable", "reason": "default instance not initialised"},
    )


def _read_pyproject_version() -> str:
    """Fallback to pyproject.toml when the package isn't installed (dev runs)."""
    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python < 3.11
        return "unknown"
    pyproject = _PROJECT_ROOT / "pyproject.toml"
    if not pyproject.is_file():
        return "unknown"
    try:
        with pyproject.open("rb") as f:
            data = tomllib.load(f)
        return str(data.get("project", {}).get("version", "unknown"))
    except Exception:
        return "unknown"


def _read_git_sha() -> str | None:
    """Best-effort lookup of the current git commit SHA without forking git.

    Returns ``None`` when no usable info can be read so the caller can omit
    the field cleanly.
    """
    git_dir = _PROJECT_ROOT / ".git"
    if not git_dir.is_dir():
        return None
    head_file = git_dir / "HEAD"
    try:
        head = head_file.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if head.startswith("ref: "):
        ref_path = git_dir / head[5:].strip()
        try:
            return ref_path.read_text(encoding="utf-8").strip()[:12] or None
        except OSError:
            return None
    # Detached HEAD
    return head[:12] or None


@app.get("/version", include_in_schema=False)
def version():
    """Report API, ai-atlas-nexus and git versions."""
    api_version = "unknown"
    try:
        from importlib.metadata import version as _v

        api_version = _v("acme-ai-atlas-nexus-demo")
    except Exception:
        api_version = _read_pyproject_version()

    nexus_version = "unknown"
    try:
        from importlib.metadata import version as _v

        nexus_version = _v("ai-atlas-nexus")
    except Exception:
        pass

    payload = {"api": api_version, "ai_atlas_nexus": nexus_version}
    git_sha = _read_git_sha()
    if git_sha:
        payload["git_sha"] = git_sha
    return payload


@app.get("/classes", include_in_schema=False)
def get_classes(
    class_name: str | None = None,
    taxonomy: str | None = None,
    vocabulary: str | None = None,
):
    """List schema classes (and accept optional filters)."""
    result = handlers.all_classes_endpoint(
        class_name=class_name, taxonomy=taxonomy, vocabulary=vocabulary
    )
    return JSONResponse(content=jsonable_encoder(result))


# === DYNAMIC ENDPOINT GENERATION ===
# All 27+ API endpoints are automatically registered from OpenAPI spec in the lifespan function
# This happens at server startup, not at module import time (for faster CLI performance)
