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

from app.core.config import CORPUS_DIR

STRATEGY_ORDER = ["bm25", "dense", "hybrid"]

_retrievers: dict[str, object] | None = None


def index_corpus() -> None:
    """Build and index all three retrievers once. Call from the app's startup hook."""
    global _retrievers
    chunks = build_chunks(str(CORPUS_DIR))
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    hybrid = HybridRetriever([bm25, dense])
    hybrid.index(chunks)  # also indexes bm25 and dense — they're shared instances
    _retrievers = {"bm25": bm25, "dense": dense, "hybrid": hybrid}


def is_ready() -> bool:
    return _retrievers is not None


def retrieve(question: str, strategy: str, k: int) -> list[RetrievalResult]:
    if _retrievers is None:
        raise RuntimeError("Corpus not indexed yet — call index_corpus() at startup")
    if strategy not in _retrievers:
        raise ValueError(f"Unknown strategy '{strategy}'. Expected one of {STRATEGY_ORDER}")
    return _retrievers[strategy].retrieve(question, k=k)
