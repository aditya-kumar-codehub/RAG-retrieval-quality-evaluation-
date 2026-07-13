"""Loads real evaluation run data (results.json, eval set, corpus) for the dashboard.

Deliberately decoupled from the ``rag_eval`` package: this module reads the
plain JSON/JSONL/Markdown artifacts the CLI already writes, rather than
importing the CLI's internal dataclasses. That keeps the dashboard portable —
it only needs a `reports/<run>/results.json` directory to point at, not the
library installed in the same environment.

Live retrieval (for the upcoming Query Explorer page) is a different concern
and will import ``rag_eval`` directly, since running a retriever for real
needs the actual retriever classes, not just their saved output.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
REPORTS_DIR = PROJECT_ROOT / "reports"
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"
EVAL_SET_PATH = PROJECT_ROOT / "data" / "eval_set.jsonl"

STRATEGY_ORDER = ["bm25", "dense", "hybrid"]
STRATEGY_LABELS = {"bm25": "BM25", "dense": "Dense", "hybrid": "Hybrid (RRF)"}


@dataclass(frozen=True)
class CorpusStats:
    doc_count: int
    question_count: int
    single_chunk_count: int
    multi_chunk_count: int
    trap_count: int


def list_runs() -> list[Path]:
    """Return run directories under reports/ that contain a results.json, newest first."""
    if not REPORTS_DIR.exists():
        return []
    runs = [p for p in REPORTS_DIR.iterdir() if p.is_dir() and (p / "results.json").exists()]
    return sorted(runs, key=lambda p: p.stat().st_mtime, reverse=True)


def load_results_raw(run_dir: Path) -> list[dict]:
    with open(run_dir / "results.json", encoding="utf-8") as f:
        return json.load(f)


def results_to_dataframe(results: list[dict]) -> pd.DataFrame:
    """Flatten the raw per-question result records into one row per (question, strategy)."""
    rows = []
    for r in results:
        rm = r["retrieval_metrics"]
        rows.append(
            {
                "question_id": r["question_id"],
                "question": r["question"],
                "difficulty": r["difficulty"],
                "is_trap": r["is_trap"],
                "strategy": r["strategy"],
                "reference_answer": r["reference_answer"],
                "relevant_chunk_ids": r["relevant_chunk_ids"],
                "retrieved_chunk_ids": r["retrieved_chunk_ids"],
                "generated_answer": r["generated_answer"],
                "generator_model": r["generator_model"],
                "judge_model": r.get("judge_model", ""),
                "precision_at_3": rm["precision_at_k"].get("3"),
                "precision_at_5": rm["precision_at_k"].get("5"),
                "precision_at_10": rm["precision_at_k"].get("10"),
                "recall_at_3": rm["recall_at_k"].get("3"),
                "recall_at_5": rm["recall_at_k"].get("5"),
                "recall_at_10": rm["recall_at_k"].get("10"),
                "ndcg_at_3": rm["ndcg_at_k"].get("3"),
                "ndcg_at_5": rm["ndcg_at_k"].get("5"),
                "ndcg_at_10": rm["ndcg_at_k"].get("10"),
                "mrr": rm["mrr"],
                "faithfulness_score": r["faithfulness_score"],
                "has_unsupported_claim": r["has_unsupported_claim"],
                "claims": r["claims"],
                "num_claims": len(r["claims"]),
                "answer_relevance_score": r["answer_relevance_score"],
                "answer_relevance_explanation": r["answer_relevance_explanation"],
                "context_utilization": r["context_utilization"],
                "correctly_abstained": r["is_trap"] and len(r["claims"]) == 0,
            }
        )
    return pd.DataFrame(rows)


def summarize_by_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """One row per strategy with mean metrics across all questions — mirrors rag_eval.report."""
    agg = df.groupby("strategy").agg(
        precision_at_5=("precision_at_5", "mean"),
        recall_at_5=("recall_at_5", "mean"),
        ndcg_at_5=("ndcg_at_5", "mean"),
        mrr=("mrr", "mean"),
        faithfulness_score=("faithfulness_score", "mean"),
        pct_answers_fully_faithful=("has_unsupported_claim", lambda s: 1 - s.mean()),
        hallucination_rate=("has_unsupported_claim", "mean"),
        answer_relevance_score=("answer_relevance_score", "mean"),
        context_utilization=("context_utilization", "mean"),
    )
    trap_df = df[df["is_trap"]]
    if not trap_df.empty:
        agg["trap_abstention_rate"] = trap_df.groupby("strategy")["correctly_abstained"].mean()
    else:
        agg["trap_abstention_rate"] = float("nan")
    present = [s for s in STRATEGY_ORDER if s in agg.index]
    return agg.reindex(present)


def pick_winner(summary: pd.DataFrame) -> str | None:
    """Same tie-break rule as the CLI report: NDCG@5, then faithfulness."""
    if summary.empty:
        return None
    ranked = summary.sort_values(by=["ndcg_at_5", "faithfulness_score"], ascending=False)
    return ranked.index[0]


def load_corpus_stats() -> CorpusStats:
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
    return CorpusStats(
        doc_count=doc_count,
        question_count=total,
        single_chunk_count=single,
        multi_chunk_count=multi,
        trap_count=trap,
    )
