"""FastAPI app entrypoint.

Indexes the corpus and builds the LLM backend once at startup (see
app/services/retrieval.py and app/services/generation.py), then serves
read-only result data plus live retrieval/generation endpoints.
"""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core.config import ALLOWED_ORIGINS
from app.core.limiter import limiter
from app.routers import generate, results, retrieve
from app.services import generation as generation_service
from app.services import retrieval as retrieval_service

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Indexing corpus...")
    retrieval_service.index_corpus()
    logger.info("Corpus indexed.")
    try:
        generation_service.init_backend()
        logger.info("LLM backend ready.")
    except Exception:
        logger.exception("LLM backend failed to initialize — /api/generate will return 503 until fixed")
    yield


app = FastAPI(title="RAG Retrieval Quality Evaluator API", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(results.router)
app.include_router(retrieve.router)
app.include_router(generate.router)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
