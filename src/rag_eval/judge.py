"""LLM-as-judge: claim extraction + faithfulness, and answer relevance.

Everything in this module is LLM-judged, not ground-truth-based — contrast
with ``metrics.py``, which computes retrieval metrics against hand-labeled
gold chunk IDs. Faithfulness and relevance scores are only as reliable as the
judge model and prompts below; treat them as a consistent, explainable proxy
rather than ground truth.

To keep API usage down, claim extraction and per-claim faithfulness judgment
are combined into a single structured-output call per answer, rather than one
call to extract claims and N further calls to judge each claim individually.

Works against any ``LLMBackend`` (Anthropic API or local Ollama model) — see
``llm.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from rag_eval.llm import LLMBackend

Verdict = Literal["supported", "unsupported", "partial"]

CLAIMS_SCHEMA = {
    "type": "object",
    "properties": {
        "claims": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "claim": {
                        "type": "string",
                        "description": "A single atomic factual claim extracted from the answer.",
                    },
                    # "supporting_chunk_ids" is generated before "verdict" on purpose: the
                    # model should locate evidence first and let the verdict follow from
                    # what it found, rather than committing to a verdict and rationalizing
                    # it afterward. See the note on RELEVANCE_SCHEMA below for the same principle.
                    "supporting_chunk_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Chunk IDs from the context that support this claim, if any. Identify these BEFORE deciding the verdict.",
                    },
                    "verdict": {
                        "type": "string",
                        "enum": ["supported", "unsupported", "partial"],
                        "description": (
                            "'supported' if the claim is fully backed by the context excerpts, "
                            "'unsupported' if the claim is not backed by the context excerpts (whether "
                            "contradicted or simply absent), 'partial' if the context backs part of the "
                            "claim but not all of it."
                        ),
                    },
                },
                "required": ["claim", "supporting_chunk_ids", "verdict"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["claims"],
    "additionalProperties": False,
}

CLAIMS_SYSTEM_PROMPT = """You are a careful fact-checking assistant. You will be given a question, a set of context excerpts (each labeled with a chunk ID), and an answer that was generated using those excerpts.

Extract atomic factual claims ONLY from the literal text under "Answer to fact-check" below — never from the Question, never from the Context. Each claim should be a single, self-contained statement of fact actually asserted by that answer text. If the answer text does not assert any fact of its own (for example, it correctly says the context doesn't contain the answer, or is a refusal/non-answer), you MUST return an empty claims list — do not invent a claim describing what the question asked about.

For each real claim found in the answer text: identify supporting chunk IDs from the context (if any) BEFORE deciding the verdict, then judge it "supported" (fully backed by the context), "unsupported" (not backed by the context — either contradicted or simply not present), or "partial" (the context backs some but not all of the claim).

Be strict: a claim is only "supported" if the specific fact stated actually appears in the context, not merely a related or plausible-sounding fact.

Respond with JSON only, matching the required schema."""

CLAIMS_USER_TEMPLATE = """Context excerpts:
{context}

Question: {question}

Answer to fact-check:
{answer}"""


RELEVANCE_SCHEMA = {
    "type": "object",
    "properties": {
        # "explanation" is listed (and therefore generated) before "relevance_score" on
        # purpose: models reason more accurately about the score when they write the
        # justification first rather than committing to a number and rationalizing it
        # afterward. This matters especially for smaller/local judge models.
        "explanation": {
            "type": "string",
            "description": "One or two sentences explaining the score. Write this BEFORE deciding the score.",
        },
        "relevance_score": {
            "type": "integer",
            "enum": [1, 2, 3, 4, 5],
            "description": (
                "1 = does not address the question at all; 3 = partially addresses it or addresses "
                "a different framing of it; 5 = directly and completely addresses the question asked."
            ),
        },
    },
    "required": ["explanation", "relevance_score"],
    "additionalProperties": False,
}

RELEVANCE_SYSTEM_PROMPT = """You are judging answer relevance: does the answer address the question asked? This is independent of factual correctness — an answer can be accurate but still fail to address what was asked. A correct refusal ("I don't have that information") IS relevant if the question truly cannot be answered from context; score it low only if it evades the question or answers something else instead.

First explain your reasoning, then give a 1-5 score. Respond with JSON only, matching the required schema."""

RELEVANCE_USER_TEMPLATE = """Question: {question}

Answer: {answer}"""


@dataclass(frozen=True)
class Claim:
    text: str
    verdict: Verdict
    supporting_chunk_ids: list[str]


@dataclass(frozen=True)
class FaithfulnessResult:
    claims: list[Claim]

    @property
    def faithfulness_score(self) -> float:
        """Supported claims / total claims. Partial counts as half credit. Vacuously 1.0 if no claims."""
        if not self.claims:
            return 1.0
        weight = {"supported": 1.0, "partial": 0.5, "unsupported": 0.0}
        return sum(weight[c.verdict] for c in self.claims) / len(self.claims)

    @property
    def has_unsupported_claim(self) -> bool:
        """Stricter binary metric: did the answer contain >=1 unsupported claim?"""
        return any(c.verdict == "unsupported" for c in self.claims)


@dataclass(frozen=True)
class RelevanceResult:
    score: int  # 1-5
    explanation: str


def judge_faithfulness(
    backend: LLMBackend,
    question: str,
    answer: str,
    chunk_texts: list[tuple[str, str]],
    max_tokens: int = 2048,
) -> FaithfulnessResult:
    """Extract atomic claims from ``answer`` and judge each against the retrieved context."""
    from rag_eval.generation import format_context

    context = format_context(chunk_texts)
    user_message = CLAIMS_USER_TEMPLATE.format(context=context, question=question, answer=answer)

    data = backend.complete_json(CLAIMS_SYSTEM_PROMPT, user_message, CLAIMS_SCHEMA, max_tokens=max_tokens)
    claims = [
        Claim(
            text=c["claim"],
            verdict=c["verdict"],
            supporting_chunk_ids=c["supporting_chunk_ids"],
        )
        for c in data["claims"]
    ]
    return FaithfulnessResult(claims=claims)


def judge_answer_relevance(
    backend: LLMBackend,
    question: str,
    answer: str,
    max_tokens: int = 512,
) -> RelevanceResult:
    """Score whether ``answer`` addresses ``question`` (independent of faithfulness to context)."""
    user_message = RELEVANCE_USER_TEMPLATE.format(question=question, answer=answer)

    data = backend.complete_json(RELEVANCE_SYSTEM_PROMPT, user_message, RELEVANCE_SCHEMA, max_tokens=max_tokens)
    return RelevanceResult(score=data["relevance_score"], explanation=data["explanation"])
