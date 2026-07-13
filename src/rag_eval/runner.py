"""Orchestrates the full pipeline: retrieve -> generate -> judge -> score.

Results are accumulated per (strategy, question) as ``QuestionResult`` records
and can be serialized to/from JSON so a report can be regenerated later
without re-calling the Anthropic API (see ``report.py`` and the ``rag-eval
report`` CLI command).
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from tqdm import tqdm

from rag_eval.corpus import build_chunks
from rag_eval.generation import GeneratedAnswer, generate_answer
from rag_eval.judge import (
    FaithfulnessResult,
    RelevanceResult,
    judge_answer_relevance,
    judge_faithfulness,
)
from rag_eval.llm import LLMBackend, build_backend
from rag_eval.metrics import RetrievalMetrics, compute_retrieval_metrics
from rag_eval.retrievers.base import Retriever
from rag_eval.retrievers.bm25 import BM25Retriever
from rag_eval.retrievers.dense import DenseRetriever
from rag_eval.retrievers.hybrid import HybridRetriever

DEFAULT_KS: tuple[int, ...] = (3, 5, 10)


@dataclass(frozen=True)
class EvalQuestion:
    id: str
    question: str
    difficulty: str
    relevant_chunk_ids: list[str]
    reference_answer: str
    is_trap: bool


def load_eval_set(path: str | Path) -> list[EvalQuestion]:
    questions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            data = json.loads(line)
            questions.append(EvalQuestion(**data))
    return questions


@dataclass
class QuestionResult:
    question_id: str
    question: str
    difficulty: str
    is_trap: bool
    strategy: str
    reference_answer: str
    relevant_chunk_ids: list[str]
    retrieved_chunk_ids: list[str]
    retrieval_metrics: RetrievalMetrics
    generated_answer: str
    generator_model: str
    judge_model: str
    faithfulness_score: float
    has_unsupported_claim: bool
    claims: list[dict[str, Any]]
    answer_relevance_score: int
    answer_relevance_explanation: str
    context_utilization: float  # fraction of retrieved chunks the judge cited as supporting >=1 claim

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        # RetrievalMetrics has int-keyed dicts; JSON needs string keys.
        d["retrieval_metrics"] = {
            "precision_at_k": {str(k): v for k, v in self.retrieval_metrics.precision_at_k.items()},
            "recall_at_k": {str(k): v for k, v in self.retrieval_metrics.recall_at_k.items()},
            "ndcg_at_k": {str(k): v for k, v in self.retrieval_metrics.ndcg_at_k.items()},
            "mrr": self.retrieval_metrics.mrr,
        }
        return d

    @staticmethod
    def from_dict(d: dict[str, Any]) -> "QuestionResult":
        rm = d["retrieval_metrics"]
        retrieval_metrics = RetrievalMetrics(
            precision_at_k={int(k): v for k, v in rm["precision_at_k"].items()},
            recall_at_k={int(k): v for k, v in rm["recall_at_k"].items()},
            ndcg_at_k={int(k): v for k, v in rm["ndcg_at_k"].items()},
            mrr=rm["mrr"],
        )
        d = {**d, "retrieval_metrics": retrieval_metrics}
        return QuestionResult(**d)


def build_strategies(strategy_names: list[str]) -> dict[str, Retriever]:
    """Build the requested named retrieval strategies.

    Recognized names: "bm25", "dense", "hybrid". The dense and BM25 retriever
    instances are shared between standalone use and use inside "hybrid" so the
    dense embedding model is only loaded once.
    """
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    available = {
        "bm25": bm25,
        "dense": dense,
        "hybrid": HybridRetriever([bm25, dense]),
    }
    unknown = set(strategy_names) - set(available)
    if unknown:
        raise ValueError(f"Unknown strategies: {sorted(unknown)}. Available: {sorted(available)}")
    return {name: available[name] for name in strategy_names}


def run_evaluation(
    corpus_dir: str | Path,
    eval_set_path: str | Path,
    strategy_names: list[str],
    k: int = 5,
    ks_for_metrics: tuple[int, ...] = DEFAULT_KS,
    backend: str = "local",
    generator_model: str | None = None,
    judge_model: str | None = None,
    generator_backend: LLMBackend | None = None,
    judge_backend: LLMBackend | None = None,
    progress: bool = True,
) -> list[QuestionResult]:
    """Run retrieve -> generate -> judge -> score for every strategy x question.

    ``k`` is the number of chunks retrieved and passed to the generator/judge.
    ``ks_for_metrics`` are the additional k values at which retrieval metrics
    (precision/recall/NDCG) are computed; ``k`` is always included.

    ``backend`` selects "local" (Ollama) or "api" (Anthropic) when
    ``generator_backend``/``judge_backend`` aren't passed explicitly; model
    names default per-backend if not given (see ``llm.py``).
    """
    from rag_eval.llm import DEFAULT_ANTHROPIC_MODEL, DEFAULT_OLLAMA_MODEL

    if generator_backend is None:
        default_model = DEFAULT_OLLAMA_MODEL if backend == "local" else DEFAULT_ANTHROPIC_MODEL
        generator_backend = build_backend(backend, generator_model or default_model)
    if judge_backend is None:
        default_model = DEFAULT_OLLAMA_MODEL if backend == "local" else DEFAULT_ANTHROPIC_MODEL
        judge_backend = build_backend(backend, judge_model or default_model)

    chunks = build_chunks(corpus_dir)
    questions = load_eval_set(eval_set_path)
    strategies = build_strategies(strategy_names)

    metric_ks = tuple(sorted(set(ks_for_metrics) | {k}))

    results: list[QuestionResult] = []
    for strategy_name, retriever in strategies.items():
        retriever.index(chunks)
        iterator = tqdm(questions, desc=f"[{strategy_name}]") if progress else questions
        for q in iterator:
            retrieval = retriever.retrieve(q.question, k=k)
            retrieved_ids = [r.chunk.chunk_id for r in retrieval]
            retrieval_metrics = compute_retrieval_metrics(
                retrieved_ids, set(q.relevant_chunk_ids), ks=metric_ks
            )

            chunk_texts = [(r.chunk.chunk_id, r.chunk.text) for r in retrieval]
            generated: GeneratedAnswer = generate_answer(generator_backend, q.question, chunk_texts)

            faithfulness: FaithfulnessResult = judge_faithfulness(
                judge_backend, q.question, generated.text, chunk_texts
            )
            relevance: RelevanceResult = judge_answer_relevance(
                judge_backend, q.question, generated.text
            )

            cited_chunk_ids = {
                cid for c in faithfulness.claims for cid in c.supporting_chunk_ids
            }
            context_utilization = (
                len(cited_chunk_ids & set(retrieved_ids)) / len(retrieved_ids)
                if retrieved_ids
                else 0.0
            )

            results.append(
                QuestionResult(
                    question_id=q.id,
                    question=q.question,
                    difficulty=q.difficulty,
                    is_trap=q.is_trap,
                    strategy=strategy_name,
                    reference_answer=q.reference_answer,
                    relevant_chunk_ids=q.relevant_chunk_ids,
                    retrieved_chunk_ids=retrieved_ids,
                    retrieval_metrics=retrieval_metrics,
                    generated_answer=generated.text,
                    generator_model=generated.model,
                    judge_model=judge_backend.model,
                    faithfulness_score=faithfulness.faithfulness_score,
                    has_unsupported_claim=faithfulness.has_unsupported_claim,
                    claims=[asdict(c) for c in faithfulness.claims],
                    answer_relevance_score=relevance.score,
                    answer_relevance_explanation=relevance.explanation,
                    context_utilization=context_utilization,
                )
            )
    return results


def save_results(results: list[QuestionResult], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump([r.to_dict() for r in results], f, indent=2)


def load_results(path: str | Path) -> list[QuestionResult]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return [QuestionResult.from_dict(d) for d in data]
