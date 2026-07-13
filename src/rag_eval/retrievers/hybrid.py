"""Hybrid retriever: fuses BM25 and dense rankings via Reciprocal Rank Fusion (RRF)."""

from __future__ import annotations

from rag_eval.corpus import Chunk
from rag_eval.retrievers.base import Retriever, RetrievalResult

DEFAULT_RRF_K = 60
FUSION_POOL_SIZE = 50  # how many results to pull from each sub-retriever before fusing


class HybridRetriever:
    name = "hybrid"

    def __init__(self, retrievers: list[Retriever], rrf_k: int = DEFAULT_RRF_K) -> None:
        if len(retrievers) < 2:
            raise ValueError("HybridRetriever needs at least two sub-retrievers to fuse")
        self.retrievers = retrievers
        self.rrf_k = rrf_k
        self._chunks: list[Chunk] = []

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = list(chunks)
        for retriever in self.retrievers:
            retriever.index(chunks)

    def retrieve(self, query: str, k: int) -> list[RetrievalResult]:
        pool_size = max(k, FUSION_POOL_SIZE)
        fused_scores: dict[str, float] = {}
        chunk_by_id: dict[str, Chunk] = {}

        for retriever in self.retrievers:
            results = retriever.retrieve(query, pool_size)
            for result in results:
                chunk_by_id[result.chunk.chunk_id] = result.chunk
                fused_scores[result.chunk.chunk_id] = fused_scores.get(
                    result.chunk.chunk_id, 0.0
                ) + 1.0 / (self.rrf_k + result.rank)

        ranked_ids = sorted(fused_scores, key=lambda cid: fused_scores[cid], reverse=True)[:k]
        return [
            RetrievalResult(chunk=chunk_by_id[cid], score=fused_scores[cid], rank=rank)
            for rank, cid in enumerate(ranked_ids, start=1)
        ]
