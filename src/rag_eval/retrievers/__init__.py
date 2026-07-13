"""Retriever implementations: BM25, dense embeddings, and hybrid (RRF) fusion."""

from rag_eval.retrievers.base import Retriever, RetrievalResult
from rag_eval.retrievers.bm25 import BM25Retriever
from rag_eval.retrievers.dense import DenseRetriever
from rag_eval.retrievers.hybrid import HybridRetriever

__all__ = [
    "Retriever",
    "RetrievalResult",
    "BM25Retriever",
    "DenseRetriever",
    "HybridRetriever",
]
