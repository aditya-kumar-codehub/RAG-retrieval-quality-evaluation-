"""Dense embedding retriever using a local sentence-transformers model + numpy cosine similarity."""

from __future__ import annotations

import numpy as np

from rag_eval.corpus import Chunk
from rag_eval.retrievers.base import RetrievalResult

DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"


class DenseRetriever:
    name = "dense"

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME) -> None:
        self.model_name = model_name
        self._model = None  # lazy-loaded; sentence-transformers import is slow
        self._chunks: list[Chunk] = []
        self._embeddings: np.ndarray | None = None

    def _get_model(self):
        if self._model is None:
            from sentence_transformers import SentenceTransformer

            self._model = SentenceTransformer(self.model_name)
        return self._model

    def index(self, chunks: list[Chunk]) -> None:
        self._chunks = list(chunks)
        model = self._get_model()
        embeddings = model.encode(
            [c.text for c in self._chunks],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        self._embeddings = embeddings.astype(np.float32)

    def retrieve(self, query: str, k: int) -> list[RetrievalResult]:
        if self._embeddings is None:
            raise RuntimeError("DenseRetriever.index() must be called before retrieve()")
        model = self._get_model()
        query_vec = model.encode(
            [query], convert_to_numpy=True, normalize_embeddings=True, show_progress_bar=False
        )[0].astype(np.float32)
        # Embeddings and query are L2-normalized, so dot product == cosine similarity.
        scores = self._embeddings @ query_vec
        ranked = np.argsort(-scores)[:k]
        return [
            RetrievalResult(chunk=self._chunks[i], score=float(scores[i]), rank=rank)
            for rank, i in enumerate(ranked, start=1)
        ]
