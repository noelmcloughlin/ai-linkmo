"""
AI-LinkMO FastAPI Server (Dynamic Generation)

Server to automatically generate all endpoints.
Uses the OpenAPI spec as single source of truth.
"""

from contextlib import asynccontextmanager
from typing import Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.encoders import jsonable_encoder
from ai_atlas_nexus import AIAtlasNexus
from lib.api import handlers
from lib.api.server_dynamic import register_endpoints_from_openapi

# Global cache for AIAtlasNexus instances (shared across all requests)
# Two instances: byod=False (default data) and byod=True (custom BYOD data)
ran_instances: Dict[bool, AIAtlasNexus] = {}

BYOD_PATH = "./byo/data"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage application lifecycle: initialize shared resources on startup.
    
    Creates and caches AIAtlasNexus instances that are reused across all requests
    for optimal performance. Instances are stateless for read operations.
    Also registers dynamic endpoints from OpenAPI spec.
    """
    # Register dynamic endpoints from OpenAPI spec (only at server startup, not on import)
    print("\n🚀 Generating endpoints from OpenAPI specification...")
    register_endpoints_from_openapi(app, verbose=True)
    print("\n🚀 Initializing AIAtlasNexus instances...")
    try:
        ran_instances[False] = AIAtlasNexus()  # Default data
        print("   ✅ Default instance ready")
    except Exception as e:
        print(f"   ⚠️  Warning: Failed to initialize default instance: {e}")
    
    try:
        ran_instances[True] = AIAtlasNexus(base_dir=BYOD_PATH)  # BYOD data
        print("   ✅ BYOD instance ready")
    except Exception as e:
        print(f"   ⚠️  Warning: Failed to initialize BYOD instance: {e}")
    
    print(f"✅ Server ready with {len(ran_instances)} cached instance(s)")
    yield
    
    # Cleanup on shutdown
    print("🛑 Shutting down AIAtlasNexus instances...")
    ran_instances.clear()


app = FastAPI(
    title="AI-LinkMO API Demo",
    description="REST API for AI-LinkMO Demo operations (dynamically generated from OpenAPI spec)",
    lifespan=lifespan
)

# Allow CORS for local frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", include_in_schema=False)
def redirect_root():
    """Redirect root to API documentation."""
    return RedirectResponse(url="/docs")

@app.get("/health", include_in_schema=False)
def health():
    """Health check endpoint."""
    return {"status": "ok"}

# Special endpoint not in OpenAPI spec
@app.get("/classes")
def get_classes(class_name: str = None, taxonomy: str = None, vocabulary: str = None):
    """Get all classes with optional filters."""
    result = handlers.all_classes_endpoint(class_name=class_name, taxonomy=taxonomy, vocabulary=vocabulary)
    return JSONResponse(content=jsonable_encoder(result))

# === DYNAMIC ENDPOINT GENERATION ===
# All 27+ API endpoints are automatically registered from OpenAPI spec in the lifespan function
# This happens at server startup, not at module import time (for faster CLI performance)
