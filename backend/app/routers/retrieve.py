"""Live retrieval against the in-memory indexed corpus. CPU-only, no LLM cost."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import RETRIEVE_RATE_LIMIT
from app.core.limiter import limiter
from app.services import retrieval as retrieval_service

router = APIRouter(prefix="/api", tags=["retrieve"])


class RetrieveRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    strategy: str = Field(default="hybrid")
    k: int = Field(default=5, ge=1, le=20)


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_title: str
    score: float
    rank: int
    text: str


class RetrieveResponse(BaseModel):
    question: str
    strategy: str
    results: list[RetrievedChunk]


@router.post("/retrieve", response_model=RetrieveResponse)
@limiter.limit(RETRIEVE_RATE_LIMIT)
def retrieve(request: Request, body: RetrieveRequest) -> RetrieveResponse:
    if not retrieval_service.is_ready():
        raise HTTPException(status_code=503, detail="Corpus index is still warming up — try again shortly")
    try:
        raw = retrieval_service.retrieve(body.question, body.strategy, body.k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    results = [
        RetrievedChunk(
            chunk_id=r.chunk.chunk_id,
            doc_title=r.chunk.doc_title,
            score=r.score,
            rank=r.rank,
            text=r.chunk.text,
        )
        for r in raw
    ]
    return RetrieveResponse(question=body.question, strategy=body.strategy, results=results)
