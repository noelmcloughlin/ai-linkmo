"""The AI-LinkMO FastAPI application, run as ``uvicorn lib.api.server:app``.

The linkmo project in ``ai-risk-ontology-linkmo/`` builds the app from its exposure file
and the ontology schema: the class listings, the hand-written operations, CORS, caching,
the probes and the API references. This module adds ``/classes``, which ai-linkmo keeps
out of the contract.
"""

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from ai_linkmo.server import app
from lib.api import handlers

__all__ = ["app"]


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
