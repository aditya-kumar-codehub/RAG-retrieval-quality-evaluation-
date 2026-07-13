from pathlib import Path

import pytest

from rag_eval.corpus import Chunk
from rag_eval.retrievers.bm25 import BM25Retriever
from rag_eval.retrievers.hybrid import HybridRetriever


def make_chunk(chunk_id: str, text: str) -> Chunk:
    return Chunk(chunk_id=chunk_id, doc_id=chunk_id, doc_title=chunk_id, text=text, position=0)


CHUNKS = [
    make_chunk("cats", "Cats are small domesticated carnivorous mammals often kept as pets."),
    make_chunk("dogs", "Dogs are loyal domesticated canines commonly kept as pets."),
    make_chunk("rockets", "Rockets use propellant combustion to achieve orbital velocity."),
    make_chunk("bread", "Sourdough bread requires a fermented starter culture of flour and water."),
]


class FakeRetriever:
    """A deterministic fake retriever for testing fusion logic in isolation."""

    def __init__(self, name: str, ranking: list[str]) -> None:
        self.name = name
        self._ranking = ranking
        self._chunks_by_id: dict[str, Chunk] = {}

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks_by_id = {c.chunk_id: c for c in chunks}

    def retrieve(self, query: str, k: int):
        from rag_eval.retrievers.base import RetrievalResult

        results = []
        for rank, cid in enumerate(self._ranking[:k], start=1):
            results.append(
                RetrievalResult(chunk=self._chunks_by_id[cid], score=1.0 / rank, rank=rank)
            )
        return results


def test_bm25_retrieves_lexically_relevant_chunk_first():
    retriever = BM25Retriever()
    retriever.index(CHUNKS)
    results = retriever.retrieve("rocket propellant orbital velocity", k=2)
    assert results[0].chunk.chunk_id == "rockets"
    assert results[0].rank == 1
    assert len(results) == 2


def test_bm25_respects_k():
    retriever = BM25Retriever()
    retriever.index(CHUNKS)
    results = retriever.retrieve("pets", k=1)
    assert len(results) == 1


def test_bm25_raises_if_not_indexed():
    retriever = BM25Retriever()
    with pytest.raises(RuntimeError):
        retriever.retrieve("anything", k=3)


def test_bm25_ranks_are_sequential():
    retriever = BM25Retriever()
    retriever.index(CHUNKS)
    results = retriever.retrieve("domesticated pets", k=4)
    assert [r.rank for r in results] == [1, 2, 3, 4]


def test_hybrid_requires_at_least_two_retrievers():
    with pytest.raises(ValueError):
        HybridRetriever([FakeRetriever("solo", ["cats"])])


def test_hybrid_fuses_rankings_via_rrf():
    # retriever A ranks "cats" first; retriever B ranks "dogs" first but agrees "cats" is #2.
    # A chunk both retrievers rank highly should win over one only one retriever likes.
    a = FakeRetriever("a", ["cats", "dogs", "rockets", "bread"])
    b = FakeRetriever("b", ["dogs", "cats", "bread", "rockets"])
    hybrid = HybridRetriever([a, b], rrf_k=60)
    hybrid.index(CHUNKS)
    results = hybrid.retrieve("pets", k=4)
    ranked_ids = [r.chunk.chunk_id for r in results]
    # cats and dogs (agreed upon by both) should outrank rockets and bread.
    assert set(ranked_ids[:2]) == {"cats", "dogs"}
    assert set(ranked_ids[2:]) == {"rockets", "bread"}


def test_hybrid_result_ranks_are_sequential_and_scores_descending():
    a = FakeRetriever("a", ["cats", "dogs", "rockets", "bread"])
    b = FakeRetriever("b", ["dogs", "cats", "bread", "rockets"])
    hybrid = HybridRetriever([a, b])
    hybrid.index(CHUNKS)
    results = hybrid.retrieve("pets", k=4)
    assert [r.rank for r in results] == [1, 2, 3, 4]
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_hybrid_respects_k():
    a = FakeRetriever("a", ["cats", "dogs", "rockets", "bread"])
    b = FakeRetriever("b", ["dogs", "cats", "bread", "rockets"])
    hybrid = HybridRetriever([a, b])
    hybrid.index(CHUNKS)
    results = hybrid.retrieve("pets", k=2)
    assert len(results) == 2
