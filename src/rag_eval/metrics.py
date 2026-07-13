"""Ground-truth retrieval metrics: Precision@k, Recall@k, MRR, NDCG@k.

These are all computed against the gold-labeled relevant chunk IDs in the eval
set — they do not involve an LLM judge. Contrast with ``judge.py``, which
computes faithfulness and answer relevance via LLM-as-judge and is therefore
not ground-truth-based.

Binary relevance is used throughout (a chunk is either relevant or not; there
is no graded relevance score in the eval set).
"""

from __future__ import annotations

import math
from dataclasses import dataclass


def precision_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of the top-k retrieved chunks that are relevant."""
    if k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    return hits / len(top_k)


def recall_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Fraction of all relevant chunks captured within the top-k retrieved."""
    if not relevant_ids:
        return 0.0
    top_k = retrieved_ids[:k]
    hits = sum(1 for cid in top_k if cid in relevant_ids)
    return hits / len(relevant_ids)


def mrr(retrieved_ids: list[str], relevant_ids: set[str]) -> float:
    """Reciprocal rank of the first relevant chunk (0 if none found)."""
    for rank, cid in enumerate(retrieved_ids, start=1):
        if cid in relevant_ids:
            return 1.0 / rank
    return 0.0


def ndcg_at_k(retrieved_ids: list[str], relevant_ids: set[str], k: int) -> float:
    """Binary-relevance NDCG@k."""
    if not relevant_ids or k <= 0:
        return 0.0
    top_k = retrieved_ids[:k]
    dcg = sum(
        1.0 / math.log2(i + 2) for i, cid in enumerate(top_k) if cid in relevant_ids
    )
    ideal_hits = min(len(relevant_ids), k)
    idcg = sum(1.0 / math.log2(i + 2) for i in range(ideal_hits))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


@dataclass(frozen=True)
class RetrievalMetrics:
    """Retrieval metrics for a single question, at every configured k."""

    precision_at_k: dict[int, float]
    recall_at_k: dict[int, float]
    ndcg_at_k: dict[int, float]
    mrr: float


def compute_retrieval_metrics(
    retrieved_ids: list[str], relevant_ids: set[str], ks: tuple[int, ...] = (3, 5, 10)
) -> RetrievalMetrics:
    """Compute all retrieval metrics for one question at the given k values."""
    return RetrievalMetrics(
        precision_at_k={k: precision_at_k(retrieved_ids, relevant_ids, k) for k in ks},
        recall_at_k={k: recall_at_k(retrieved_ids, relevant_ids, k) for k in ks},
        ndcg_at_k={k: ndcg_at_k(retrieved_ids, relevant_ids, k) for k in ks},
        mrr=mrr(retrieved_ids, relevant_ids),
    )
