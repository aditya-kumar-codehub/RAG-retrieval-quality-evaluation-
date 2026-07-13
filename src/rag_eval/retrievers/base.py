"""Retriever interface shared by BM25, dense, and hybrid implementations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from rag_eval.corpus import Chunk


@dataclass(frozen=True)
class RetrievalResult:
    chunk: Chunk
    score: float
    rank: int  # 1-indexed


class Retriever(Protocol):
    """A retriever indexes a fixed set of chunks and ranks them for a query."""

    name: str

    def index(self, chunks: list[Chunk]) -> None:
        """Build the retriever's index over ``chunks``. Call once before retrieve()."""
        ...

    def retrieve(self, query: str, k: int) -> list[RetrievalResult]:
        """Return the top-``k`` chunks for ``query``, best first."""
        ...
