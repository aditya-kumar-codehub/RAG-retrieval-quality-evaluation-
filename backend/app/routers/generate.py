"""Live end-to-end RAG: retrieve -> generate -> judge. The costly endpoint — rate limited."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from app.core.config import GENERATE_RATE_LIMIT
from app.core.limiter import limiter
from app.services import generation as generation_service
from app.services import retrieval as retrieval_service

router = APIRouter(prefix="/api", tags=["generate"])


class GenerateRequest(BaseModel):
    question: str = Field(min_length=1, max_length=500)
    strategy: str = Field(default="hybrid")
    k: int = Field(default=5, ge=1, le=20)


class RetrievedChunkOut(BaseModel):
    chunk_id: str
    doc_title: str
    score: float
    rank: int


class ClaimOut(BaseModel):
    text: str
    verdict: str
    supporting_chunk_ids: list[str]


class GenerateResponse(BaseModel):
    question: str
    strategy: str
    retrieved: list[RetrievedChunkOut]
    answer: str
    model: str
    claims: list[ClaimOut]
    faithfulness_score: float
    has_unsupported_claim: bool
    answer_relevance_score: int
    answer_relevance_explanation: str


@router.post("/generate", response_model=GenerateResponse)
@limiter.limit(GENERATE_RATE_LIMIT)
def generate(request: Request, body: GenerateRequest) -> GenerateResponse:
    if not retrieval_service.is_ready():
        raise HTTPException(status_code=503, detail="Corpus index is still warming up — try again shortly")
    if not generation_service.is_ready():
        raise HTTPException(status_code=503, detail="LLM backend is still warming up — try again shortly")

    try:
        retrieved = retrieval_service.retrieve(body.question, body.strategy, body.k)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    chunk_texts = [(r.chunk.chunk_id, r.chunk.text) for r in retrieved]

    try:
        generated = generation_service.generate(body.question, chunk_texts)
        faithfulness = generation_service.judge_faithfulness_of(body.question, generated.text, chunk_texts)
        relevance = generation_service.judge_relevance_of(body.question, generated.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return GenerateResponse(
        question=body.question,
        strategy=body.strategy,
        retrieved=[
            RetrievedChunkOut(chunk_id=r.chunk.chunk_id, doc_title=r.chunk.doc_title, score=r.score, rank=r.rank)
            for r in retrieved
        ],
        answer=generated.text,
        model=generated.model,
        claims=[
            ClaimOut(text=c.text, verdict=c.verdict, supporting_chunk_ids=c.supporting_chunk_ids)
            for c in faithfulness.claims
        ],
        faithfulness_score=faithfulness.faithfulness_score,
        has_unsupported_claim=faithfulness.has_unsupported_claim,
        answer_relevance_score=relevance.score,
        answer_relevance_explanation=relevance.explanation,
    )
