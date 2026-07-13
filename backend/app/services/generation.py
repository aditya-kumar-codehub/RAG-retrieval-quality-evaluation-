"""Live answer generation + judging: the costly path, built once and reused per request.

The LLM backend (Ollama or Anthropic) is stateless aside from its client/model
config, so it's built once at startup — same singleton pattern as
retrieval.py's indexed retrievers — rather than reconstructed per request.
"""

from __future__ import annotations

from rag_eval.generation import GeneratedAnswer, generate_answer
from rag_eval.judge import FaithfulnessResult, RelevanceResult, judge_answer_relevance, judge_faithfulness
from rag_eval.llm import DEFAULT_ANTHROPIC_MODEL, DEFAULT_OLLAMA_MODEL, LLMBackend, build_backend

from app.core.config import GENERATION_BACKEND, GENERATION_MODEL

_backend: LLMBackend | None = None


def init_backend() -> None:
    """Construct the configured LLM backend once. Call from the app's startup hook."""
    global _backend
    model = GENERATION_MODEL or (
        DEFAULT_OLLAMA_MODEL if GENERATION_BACKEND == "local" else DEFAULT_ANTHROPIC_MODEL
    )
    _backend = build_backend(GENERATION_BACKEND, model)


def is_ready() -> bool:
    return _backend is not None


def generate(question: str, chunk_texts: list[tuple[str, str]]) -> GeneratedAnswer:
    if _backend is None:
        raise RuntimeError("LLM backend not initialized yet — call init_backend() at startup")
    return generate_answer(_backend, question, chunk_texts)


def judge_faithfulness_of(question: str, answer: str, chunk_texts: list[tuple[str, str]]) -> FaithfulnessResult:
    if _backend is None:
        raise RuntimeError("LLM backend not initialized yet — call init_backend() at startup")
    return judge_faithfulness(_backend, question, answer, chunk_texts)


def judge_relevance_of(question: str, answer: str) -> RelevanceResult:
    if _backend is None:
        raise RuntimeError("LLM backend not initialized yet — call init_backend() at startup")
    return judge_answer_relevance(_backend, question, answer)
