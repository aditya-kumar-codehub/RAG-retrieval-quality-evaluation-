"""Live retrieval: indexes the corpus once at process startup, serves from memory after.

Unlike the Streamlit dashboard (which uses st.cache_resource, itself
per-process), a FastAPI server has one obvious place to do this exactly
once: the app's lifespan startup hook (see app/main.py). This module just
holds the indexed retrievers as module-level state once startup has run.
"""

from __future__ import annotations

from rag_eval.corpus import build_chunks
from rag_eval.retrievers.base import RetrievalResult
from rag_eval.retrievers.bm25 import BM25Retriever
from rag_eval.retrievers.dense import DenseRetriever
from rag_eval.retrievers.hybrid import HybridRetriever

from app.core.config import CORPUS_DIR, LIVE_STRATEGIES

STRATEGY_ORDER = ["bm25", "dense", "hybrid"]

_retrievers: dict[str, object] | None = None


def index_corpus() -> None:
    """Build and index the configured subset of retrievers. Call from the app's startup hook.

    "dense" and "hybrid" load a real embedding model (torch); skip them via
    LIVE_STRATEGIES on memory-constrained deployments — see config.py.
    """
    global _retrievers
    chunks = build_chunks(str(CORPUS_DIR))
    retrievers: dict[str, object] = {}

    need_bm25 = "bm25" in LIVE_STRATEGIES or "hybrid" in LIVE_STRATEGIES
    need_dense = "dense" in LIVE_STRATEGIES or "hybrid" in LIVE_STRATEGIES

    bm25 = BM25Retriever() if need_bm25 else None
    dense = DenseRetriever() if need_dense else None

    if "hybrid" in LIVE_STRATEGIES and bm25 is not None and dense is not None:
        hybrid = HybridRetriever([bm25, dense])
        hybrid.index(chunks)  # indexes bm25 and dense as a side effect — shared instances
        retrievers["hybrid"] = hybrid
    else:
        if bm25 is not None:
            bm25.index(chunks)
        if dense is not None:
            dense.index(chunks)

    if "bm25" in LIVE_STRATEGIES and bm25 is not None:
        retrievers["bm25"] = bm25
    if "dense" in LIVE_STRATEGIES and dense is not None:
        retrievers["dense"] = dense

    _retrievers = retrievers


def is_ready() -> bool:
    return _retrievers is not None


def available_strategies() -> list[str]:
    if _retrievers is None:
        return []
    return [s for s in STRATEGY_ORDER if s in _retrievers]


def retrieve(question: str, strategy: str, k: int) -> list[RetrievalResult]:
    if _retrievers is None:
        raise RuntimeError("Corpus not indexed yet — call index_corpus() at startup")
    if strategy not in _retrievers:
        raise ValueError(f"Strategy '{strategy}' isn't available in this deployment. Available: {available_strategies()}")
    return _retrievers[strategy].retrieve(question, k=k)
