"""The FastAPI application: the generated endpoints, CORS, caching and the probes.

The class listings and the hand operations are registered from the exposure file when
this module is imported. The records are read once at startup, so ``/ready`` answers 200
only when the data source has loaded. Run it with ``just serve``, or with uvicorn as
``<package>.server:app``.
"""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from starlette.middleware.base import BaseHTTPMiddleware

from . import settings
from .api_kernel import publish_overlay, register_class_endpoints, register_hand_endpoints
from .cli import project_version
from .exposure import load_exposure
from .schema import schema_view
from .sources import load_source

logger = logging.getLogger(__name__)

# Allowed cross-origin callers come from <PREFIX>_CORS_ORIGINS, a comma-separated list, or
# "*". The default is the local development servers only, rather than any origin.
_origins = os.environ.get(f"{settings.ENV_PREFIX}_CORS_ORIGINS", "").strip()
if _origins == "*":
    CORS_ORIGINS = ["*"]
elif _origins:
    CORS_ORIGINS = [o.strip() for o in _origins.split(",") if o.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
# Browsers send Origin: null from file:// pages and sandboxed frames. That is refused
# unless an operator opts in for a local demo.
if os.environ.get(f"{settings.ENV_PREFIX}_CORS_ALLOW_NULL") == "1" and "null" not in CORS_ORIGINS:
    CORS_ORIGINS.append("null")


class CacheControlMiddleware(BaseHTTPMiddleware):
    """Mark GET answers ``no-cache``, so changed data shows at once, and the rest ``no-store``."""

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if "cache-control" not in (h.lower() for h in response.headers.keys()):
            response.headers["Cache-Control"] = "no-cache" if request.method == "GET" else "no-store"
        return response


_state: dict[str, str] = {}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Read the records once at startup, so the first question does not wait for them."""
    try:
        load_source()
        _state["ready"] = "yes"
    except Exception:
        logger.exception("The data source failed to load")
    yield


_info = load_exposure().overlay.get("info") or {}
app = FastAPI(
    title=_info.get("title", f"{settings.COMMAND_NAME} API"),
    description=_info.get(
        "description",
        "One listing per exposed class of the schema, with the class's slots as filters.",
    ),
    version=str(_info.get("version", project_version())),
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

register_class_endpoints(app)
register_hand_endpoints(app)
publish_overlay(app)


@app.get("/", include_in_schema=False)
def redirect_root():
    return RedirectResponse(url="/docs")


@app.get("/health", include_in_schema=False)
def health():
    """Liveness: 200 once the process is up."""
    return {"status": "ok"}


@app.get("/ready", include_in_schema=False)
def ready():
    """Readiness: 200 once the data source has loaded."""
    if _state.get("ready"):
        return {"status": "ready"}
    return JSONResponse(status_code=503, content={"status": "unavailable"})


@app.get("/version", include_in_schema=False)
def version():
    return {
        "api": project_version(),
        "schema": schema_view().schema.version,
        "datamodel": settings.DATAMODEL_MODULE,
    }


# Scalar is a third reference to the contract beside Swagger UI at /docs and ReDoc at
# /redoc. Its script comes from a CDN, so the page needs the network but adds no package.
_SCALAR_PAGE = """<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>API reference</title>
  </head>
  <body>
    <div id="app"></div>
    <script src="https://cdn.jsdelivr.net/npm/@scalar/api-reference"></script>
    <script>Scalar.createApiReference("#app", { url: "/openapi.json" });</script>
  </body>
</html>
"""


@app.get("/scalar", include_in_schema=False)
def scalar_reference():
    return HTMLResponse(_SCALAR_PAGE)
