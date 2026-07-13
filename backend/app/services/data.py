"""Loads real evaluation run data (results.json, eval set, corpus).

Mirrors dashboard/utils/data_loader.py's logic — deliberately decoupled from
both Streamlit and rag_eval's internal dataclasses, reading the plain JSON
artifacts the CLI already writes. Kept as a near-duplicate rather than a
shared import because the two apps (Streamlit dashboard, FastAPI backend)
are independently deployable and shouldn't need to agree on a shared
internal module layout.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.config import CORPUS_DIR, EVAL_SET_PATH, REPORTS_DIR

STRATEGY_ORDER = ["bm25", "dense", "hybrid"]
STRATEGY_LABELS = {"bm25": "BM25", "dense": "Dense", "hybrid": "Hybrid (RRF)"}


def list_runs() -> list[str]:
    """Run directory names under reports/ that contain a results.json, newest first."""
    if not REPORTS_DIR.exists():
        return []
    runs = [p for p in REPORTS_DIR.iterdir() if p.is_dir() and (p / "results.json").exists()]
    runs.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return [p.name for p in runs]


def resolve_run_dir(run: str | None) -> Path:
    runs = list_runs()
    if not runs:
        raise FileNotFoundError("No evaluation runs found under reports/")
    if run is None:
        return REPORTS_DIR / runs[0]
    if run not in runs:
        raise FileNotFoundError(f"Run '{run}' not found. Available: {runs}")
    return REPORTS_DIR / run


def load_results(run: str | None = None) -> list[dict[str, Any]]:
    run_dir = resolve_run_dir(run)
    with open(run_dir / "results.json", encoding="utf-8") as f:
        return json.load(f)


def summarize_by_strategy(results: list[dict[str, Any]]) -> dict[str, dict[str, float]]:
    """One entry per strategy with mean metrics across all questions."""
    by_strategy: dict[str, list[dict[str, Any]]] = {}
    for r in results:
        by_strategy.setdefault(r["strategy"], []).append(r)

    summary: dict[str, dict[str, float]] = {}
    for strategy, rows in by_strategy.items():
        n = len(rows)
        trap_rows = [r for r in rows if r["is_trap"]]
        correctly_abstained = [r for r in trap_rows if len(r["claims"]) == 0]
        summary[strategy] = {
            "precision_at_5": sum(r["retrieval_metrics"]["precision_at_k"].get("5", 0) for r in rows) / n,
            "recall_at_5": sum(r["retrieval_metrics"]["recall_at_k"].get("5", 0) for r in rows) / n,
            "ndcg_at_5": sum(r["retrieval_metrics"]["ndcg_at_k"].get("5", 0) for r in rows) / n,
            "mrr": sum(r["retrieval_metrics"]["mrr"] for r in rows) / n,
            "faithfulness_score": sum(r["faithfulness_score"] for r in rows) / n,
            "hallucination_rate": sum(1 for r in rows if r["has_unsupported_claim"]) / n,
            "answer_relevance_score": sum(r["answer_relevance_score"] for r in rows) / n,
            "context_utilization": sum(r["context_utilization"] for r in rows) / n,
            "trap_abstention_rate": (len(correctly_abstained) / len(trap_rows)) if trap_rows else float("nan"),
        }
    ordered = {s: summary[s] for s in STRATEGY_ORDER if s in summary}
    ordered.update({s: v for s, v in summary.items() if s not in ordered})
    return ordered


def pick_winner(summary: dict[str, dict[str, float]]) -> str | None:
    if not summary:
        return None
    return max(summary, key=lambda s: (summary[s]["ndcg_at_5"], summary[s]["faithfulness_score"]))


def corpus_stats() -> dict[str, int]:
    doc_count = len(list(CORPUS_DIR.glob("*.md"))) if CORPUS_DIR.exists() else 0
    single = multi = trap = total = 0
    if EVAL_SET_PATH.exists():
        with open(EVAL_SET_PATH, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                q = json.loads(line)
                total += 1
                if q["is_trap"]:
                    trap += 1
                elif len(q["relevant_chunk_ids"]) <= 1:
                    single += 1
                else:
                    multi += 1
    return {
        "doc_count": doc_count,
        "question_count": total,
        "single_chunk_count": single,
        "multi_chunk_count": multi,
        "trap_count": trap,
    }
