"""Answer generation: given a question and retrieved context, call an LLM to produce an answer.

This module is the RAG "G" — it does not itself judge quality. See ``judge.py``
for the LLM-as-judge faithfulness/relevance scoring, which is a separate
concern from generation. Works against any ``LLMBackend`` (Anthropic API or
local Ollama model) — see ``llm.py``.
"""

from __future__ import annotations

from dataclasses import dataclass

from rag_eval.llm import LLMBackend

SYSTEM_PROMPT = """You are a helpful assistant answering questions using only the provided context excerpts from Northwind Cloud's internal documentation.

Rules:
- Answer using only information present in the provided context. Do not use outside knowledge.
- If the context does not contain enough information to answer the question, say so plainly (e.g. "I don't have information about that in the provided context") rather than guessing or inferring.
- Be concise and direct. Do not pad the answer with unnecessary caveats when the context does answer the question.
- When you state a specific fact (a number, a policy detail, a procedure step), it should be traceable to the context you were given."""

USER_TEMPLATE = """Context excerpts:
{context}

Question: {question}

Answer the question using only the context above."""


@dataclass(frozen=True)
class GeneratedAnswer:
    text: str
    model: str
    input_tokens: int
    output_tokens: int


def format_context(chunk_texts: list[tuple[str, str]]) -> str:
    """Format retrieved chunks as labeled excerpts for the prompt.

    ``chunk_texts`` is a list of (chunk_id, text) pairs, in retrieval rank order.
    """
    parts = []
    for chunk_id, text in chunk_texts:
        parts.append(f"[{chunk_id}]\n{text}")
    return "\n\n".join(parts)


def generate_answer(
    backend: LLMBackend,
    question: str,
    chunk_texts: list[tuple[str, str]],
    max_tokens: int = 1024,
) -> GeneratedAnswer:
    """Generate an answer to ``question`` grounded in the given retrieved chunks."""
    context = format_context(chunk_texts)
    user_message = USER_TEMPLATE.format(context=context, question=question)

    result = backend.complete(SYSTEM_PROMPT, user_message, max_tokens=max_tokens)
    return GeneratedAnswer(
        text=result.text,
        model=result.model,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
    )
