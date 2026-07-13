"""BM25 lexical retriever backed by rank-bm25."""

from __future__ import annotations

import re

from rank_bm25 import BM25Okapi

from rag_eval.corpus import Chunk
from rag_eval.retrievers.base import RetrievalResult

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _TOKEN_RE.findall(text.lower())


class BM25Retriever:
    name = "bm25"

    def __init__(self) -> None:
        self._bm25: BM25Okapi | None = None
        self._chunks: list[Chunk] = []

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = list(chunks)
        tokenized = [_tokenize(c.text) for c in self._chunks]
        self._bm25 = BM25Okapi(tokenized)

    def retrieve(self, query: str, k: int) -> list[RetrievalResult]:
        if self._bm25 is None:
            raise RuntimeError("BM25Retriever.index() must be called before retrieve()")
        scores = self._bm25.get_scores(_tokenize(query))
        ranked = sorted(
            range(len(self._chunks)), key=lambda i: scores[i], reverse=True
        )[:k]
        return [
            RetrievalResult(chunk=self._chunks[i], score=float(scores[i]), rank=rank)
            for rank, i in enumerate(ranked, start=1)
        ]
