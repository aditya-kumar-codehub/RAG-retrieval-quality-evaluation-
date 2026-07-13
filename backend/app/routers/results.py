"""Read-only endpoints serving the saved evaluation run data. No LLM calls, no cost."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Query

from app.services import data as data_service

router = APIRouter(prefix="/api", tags=["results"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/runs")
def get_runs() -> dict[str, list[str]]:
    return {"runs": data_service.list_runs()}


@router.get("/results")
def get_results(run: str | None = Query(default=None)) -> list[dict[str, Any]]:
    try:
        return data_service.load_results(run)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/summary")
def get_summary(run: str | None = Query(default=None)) -> dict[str, Any]:
    try:
        results = data_service.load_results(run)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    summary = data_service.summarize_by_strategy(results)
    return {
        "summary": summary,
        "winner": data_service.pick_winner(summary),
    }


@router.get("/corpus-stats")
def get_corpus_stats() -> dict[str, int]:
    return data_service.corpus_stats()
