# RAG Retrieval Quality Evaluator

A small, well-engineered Python framework for answering one question: **is our
retrieval actually good, and which retrieval strategy should we use?**

This is not another RAG chatbot. It's an evaluation harness: point it at a
corpus and a labeled eval set, and it runs multiple retrieval strategies
(BM25, dense embeddings, hybrid RRF fusion), generates answers grounded in
each strategy's retrieved context, scores everything on both ground-truth
retrieval metrics and LLM-judged answer quality, and produces a markdown
comparison report with charts and concrete failure-case examples.

## Why this exists

Teams that ship RAG systems usually eyeball a handful of queries and call it
good. This framework replaces that with a repeatable eval: the same 28
questions, the same gold labels, run against every retrieval strategy, scored
the same way every time — so "we switched to hybrid retrieval" is a claim you
can actually back up with numbers.

## Methodology — what's ground truth vs. LLM-judged

This distinction matters for interpreting results, so it's explicit
everywhere in the code and the generated report:

| Metric | Basis | Computed in |
|---|---|---|
| Precision@k, Recall@k, MRR, NDCG@k | **Ground truth** — hand-labeled gold-relevant chunk IDs | `metrics.py` |
| Faithfulness score | **LLM-judged** — claim extraction + per-claim support check | `judge.py` |
| Hallucination rate (≥1 unsupported claim) | **LLM-judged**, derived from the same claim check | `judge.py` |
| Trap-question abstention rate | **LLM-judged proxy** — did the answer assert zero claims on a question with no correct answer in the corpus | `report.py` |
| Answer relevance (1-5) | **LLM-judged** — separate call, independent of faithfulness | `judge.py` |
| Context utilization | **LLM-judged proxy** — fraction of retrieved chunks the judge actually cited as supporting a claim | `runner.py` |

Retrieval metrics are objective and reproducible — the same run always
produces the same numbers. Everything LLM-judged is a *consistent, explainable
proxy*, not ground truth: it's only as reliable as the judge model and
prompts in `judge.py`. Treat the LLM-judged numbers as directionally useful
for comparing strategies against each other within one run, not as an
absolute quality certification.

### Faithfulness methodology (RAGAS-style)

1. **Claim extraction**: the generated answer is decomposed into atomic
   factual claims via a structured-output LLM call (one call, not N — see
   "keeping API/compute usage down" below).
2. **Per-claim verdict**: each claim is judged `supported` / `partial` /
   `unsupported` against the retrieved context, in the same call.
3. **Faithfulness score** = (supported claims + 0.5 × partial claims) / total
   claims, vacuously `1.0` if the answer asserted zero claims (e.g. a correct
   "I don't know").
4. **Hallucination rate** (the stricter binary metric) = fraction of answers
   with **at least one** unsupported claim — this is the number to watch if
   you care about worst-case behavior rather than average faithfulness.

### Trap questions and hallucination-under-RAG

6 of the 28 eval questions ask about things that are **not in the corpus at
all** (an office pet policy, a referral bonus, an uptime SLA percentage,
etc.). A good system should retrieve weak/irrelevant context for these and
have the generator say "I don't know" — asserting zero claims, which scores a
faithfulness of `1.0` and a high abstention rate. A system that instead
confabulates a plausible-sounding answer is hallucinating, and this shows up
as a low trap-abstention rate even if its faithfulness score elsewhere looks
fine. This is the main signal to check before trusting a retrieval strategy
in production.

## Architecture

```
rag-eval/
  pyproject.toml
  src/rag_eval/
    corpus.py          # load & chunk documents into stable-ID chunks
    retrievers/
      base.py           # Retriever protocol
      bm25.py            # rank-bm25 lexical retrieval
      dense.py            # sentence-transformers + numpy cosine similarity
      hybrid.py            # reciprocal rank fusion (RRF) over bm25 + dense
    llm.py              # LLMBackend abstraction: Anthropic API or local Ollama
    generation.py        # calls the backend to answer a question from context
    judge.py              # LLM-as-judge: claim extraction, faithfulness, relevance
    metrics.py             # precision/recall/MRR/NDCG (ground truth)
    runner.py                # orchestrates: retrieve -> generate -> judge -> score
    report.py                 # builds the markdown report + matplotlib charts
    cli.py                     # typer entrypoint (`rag-eval run` / `rag-eval report`)
  data/
    corpus/               # 40 synthetic "Northwind Cloud" internal docs
    eval_set.jsonl          # 28 labeled questions
  tests/                     # deterministic unit tests (no API/model calls)
  reports/                     # generated output lands here
```

Adding a new retriever means implementing the `Retriever` protocol in
`retrievers/base.py` (an `index(chunks)` and a `retrieve(query, k)` method)
and registering it in `runner.build_strategies()` — nothing else in the
pipeline needs to change. Swapping in a different corpus means pointing
`--corpus` at a new directory of `.md` files and writing a matching
`eval_set.jsonl`; `metrics.py`, `judge.py`, and `report.py` are corpus-agnostic.

## The corpus and eval set

The corpus is 40 short synthetic Markdown documents about a fictional B2B
SaaS company, **Northwind Cloud**, split across three domains chosen so
retrieval strategies would meaningfully diverge:

- **Product/API docs** (19) — auth, rate limits, pricing tiers, webhooks,
  SSO, audit logs, data retention, etc. — heavily cross-referenced (rate
  limits differ by pricing tier, SSO auto-enables audit logging, and so on).
- **HR/policy docs** (11) — PTO, remote work, benefits, security policy,
  onboarding, etc.
- **Engineering runbooks** (10) — incident response, on-call, deployment
  process, disaster recovery, etc.

Documents chunk to one chunk each at this length (the chunker in `corpus.py`
packs paragraphs up to ~300-450 words per chunk and is unit-tested on longer
synthetic text to confirm it does split when a document is long enough — see
`tests/test_corpus.py`). Chunk IDs are stable: `"{doc_id}-{index}"`.

The eval set (`data/eval_set.jsonl`) has 28 hand-written questions:

- **12 single-chunk** questions, answerable from exactly one document.
- **10 multi-chunk** questions that require synthesizing 2 documents (e.g.
  "If I'm on the Pro tier and hit the rate limit, what's my retry strategy?"
  needs both the pricing-tiers doc and the rate-limits doc).
- **6 trap** questions about things genuinely absent from the corpus, used to
  measure hallucination-under-RAG (see above).

Gold-relevant chunk IDs were assigned by actually running the chunker against
the corpus and reading off the real resulting chunk IDs, not guessed from the
source Markdown — every `relevant_chunk_ids` entry in `eval_set.jsonl` is
verified to exist in the corpus's actual chunk set.

## Installation

Requires Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv venv --python 3.12
uv pip install -e .
```

### Choosing a backend

The generator and judge both run through a swappable `LLMBackend`
(`llm.py`), so you can run the whole pipeline for free against a local model,
or against Claude for higher-quality judging:

| Backend | Flag | Default model | Setup |
|---|---|---|---|
| Local (Ollama) | `--backend local` (default) | `qwen2.5:3b` | Install [Ollama](https://ollama.com), run `ollama serve`, then `ollama pull qwen2.5:3b` |
| Anthropic API | `--backend api` | `claude-sonnet-5` | `export ANTHROPIC_API_KEY=...` |

The local backend is what this repo's included run used (see Results below)
— it's free and requires no API key, at the cost of a smaller, noisier judge
model. Point `--generator-model` / `--judge-model` at a larger local model
(e.g. `llama3.1:8b`) or at the API backend for higher-fidelity judging; the
prompts and structured-output schemas in `judge.py` work against either.

## Usage

```bash
# Run the full pipeline: retrieve -> generate -> judge -> score -> report
rag-eval run --corpus data/corpus --eval-set data/eval_set.jsonl \
  --strategies bm25,dense,hybrid --k 5 --backend local \
  --out reports/run_YYYYMMDD

# Regenerate the report from a saved run, with zero API/model calls
rag-eval report reports/run_YYYYMMDD
```

Every run saves per-question raw results to `results.json` in the output
directory — retrieved chunk IDs, the full generated answer, every extracted
claim and its verdict, and the relevance judgment — so you can inspect
individual failure cases or regenerate the report without re-running
generation or judging.

### Keeping API/compute usage down

- Claim extraction and per-claim faithfulness judgment are combined into
  **one** structured-output call per answer, not one call to extract claims
  plus N further calls to judge each claim.
- `rag-eval report` never calls the backend — it works entirely from the
  saved `results.json`.
- A full run against the included eval set is 28 questions × 3 strategies =
  84 (question, strategy) pairs, each needing 1 generation call + 1
  faithfulness call + 1 relevance call = 252 total backend calls. On the
  Anthropic API at Sonnet pricing this is on the order of $1-3; on the local
  backend it's free but slower (well under an hour on modest hardware — see
  Results for actual timing on an 8GB M1).

## Swapping in a real corpus

1. Drop `.md` files into a new directory (or point `--corpus` elsewhere).
   Keep documents in the ~150-450 word range for the default chunker
   settings, or tune `target_words`/`max_words` in `corpus.py::chunk_document`.
2. Run the corpus through `rag_eval.corpus.build_chunks()` once and print the
   resulting chunk IDs — you need these to write gold labels.
3. Write a new `eval_set.jsonl` with the same shape as `data/eval_set.jsonl`:
   `id`, `question`, `difficulty`, `relevant_chunk_ids`, `reference_answer`,
   `is_trap`. Include some trap questions if you care about measuring
   hallucination, not just retrieval accuracy.
4. `rag-eval run --corpus <your dir> --eval-set <your file>`.

## Testing

```bash
pytest
```

All 33 tests are deterministic and require no API key or model download —
they cover chunking edge cases, all four retrieval metrics (including the
edge cases: no relevant chunks for trap questions, order sensitivity, k
truncation), BM25 ranking, and RRF fusion behavior with a fake deterministic
sub-retriever.

## Results

Full report with charts and failure-case examples:
[`reports/run_local_full/report.md`](reports/run_local_full/report.md).
Backend: local (`qwen2.5:3b` for both generation and judging). Summary below.

### Retrieval quality (ground truth)

| | Precision@5 | Recall@5 | NDCG@5 | MRR |
|---|---|---|---|---|
| BM25 | 0.214 | 0.750 | 0.747 | 0.786 |
| Dense | 0.214 | 0.750 | 0.750 | 0.786 |
| Hybrid (RRF) | 0.214 | 0.750 | 0.749 | 0.786 |

All three strategies retrieve near-identically well on this corpus — **zero
non-trap questions had a complete retrieval miss** (recall@5 = 0) for any
strategy. That's not a bug, it's a property of a 40-chunk corpus with
lexically distinct topics: at k=5 against 40 total chunks, all three
strategies have an easy time finding *a* relevant chunk. Precision@5 is low
(~0.21) simply because most questions have only 1-2 gold-relevant chunks
among the 5 retrieved — see the Methodology section above for why Precision@k
and Recall@k move in opposite directions here. The one genuine (partial) miss
across the whole run: **all three strategies** fail to retrieve
`pricing-tiers-0` for the Pro-tier rate-limit question (q13), consistently
returning only `rate-limits-0`. The answer was still correct in that case
because the tier-specific numbers happen to be duplicated in `rate-limits.md`
— a quirk of this synthetic corpus, not the retrieval strategies.

**Takeaway:** at this corpus size, retrieval strategy choice barely matters
for raw retrieval quality — the differentiation shows up downstream, in
generation and faithfulness.

### Faithfulness, hallucination, and answer relevance (LLM-judged)

| | Faithfulness | Hallucination rate | Trap abstention rate | Answer relevance (1-5) |
|---|---|---|---|---|
| BM25 | 1.00 | 0% | 100% | 3.68 |
| Dense | 1.00 | 0% | 83.3% | 4.14 |
| Hybrid (RRF) | 0.97 | 7.1% | 100% | 4.36 |

**Hybrid wins on answer relevance** (4.36/5) despite a slightly non-zero
hallucination rate. **Dense's 83.3% trap-abstention rate is not a genuine
dense-retrieval failure** — see Case 3 below; it's an artifact of the judge
model occasionally extracting claims from retrieved *context* instead of the
generated *answer* on refusal questions, a known limitation of the 3B local
judge (see "Known limitations"). This happened in exactly 1 of 84
(question, strategy) pairs in this run (1 of 18 trap-question pairs) — rare,
but worth knowing about before trusting an aggregate hallucination number
from a small local judge at face value.

### Overall

Ranked by NDCG@5 then faithfulness as a tiebreaker, the generated report
calls **Dense** the winner — but by a razor-thin margin over BM25 and Hybrid
on retrieval, and **Hybrid actually leads on answer relevance**. On a corpus
this size, the honest conclusion is: *all three strategies are roughly
equivalent on this eval set*, and the choice would come down to Hybrid's
slightly better answer relevance versus its slightly higher hallucination
rate. This kind of near-tie is itself a useful finding — it tells you
retrieval strategy isn't the bottleneck here, and that a larger or harder
corpus (more documents, more lexical/semantic divergence between them) would
be needed to meaningfully differentiate BM25 from dense embeddings.

### Example failure cases

**1. A real hallucination, caught.** For "What is the minimum password length
... does the company force periodic password rotation?" (hybrid), the model
answered "14 characters" (correct) but then asserted Northwind Cloud *does*
enforce periodic rotation — the exact opposite of the source policy. The
faithfulness judge correctly flagged this claim as `unsupported` and scored
the answer 0.50, and separately scored answer relevance only 2/5 since the
answer didn't actually resolve the yes/no rotation question the user asked.

**2. A retrieval miss with a lucky save.** For the Pro-tier 429/rate-limit
question (bm25), retrieval never surfaces the `pricing-tiers-0` chunk (only
`rate-limits-0`) — a genuine partial miss. The answer came out correct anyway
because `rate-limits.md` happens to restate each tier's numeric limit
directly. In a corpus without that redundancy, this exact retrieval gap
would have produced an unanswerable or hallucinated response — a good
illustration of why Recall@k matters even when the generated answer looks
fine on the surface.

**3. A judge failure, not a system failure.** For the uptime-SLA trap
question (dense), the model correctly answered "I don't have information
about that in the provided context" — genuinely the right behavior. But the
faithfulness judge extracted four claims about support-tier SLAs that appear
nowhere in that answer text (they're from the retrieved context instead),
and marked them all "supported." This is exactly the small-local-judge
failure mode flagged in "Known limitations": the judge occasionally conflates
context with the answer it's supposed to be checking. It's rare (1/84 in
this run) but it's the reason the trap-abstention numbers above should be
spot-checked against `results.json`, not taken as ground truth.

## Known limitations

- **Local judge model noise.** `qwen2.5:3b` is a 3B-parameter model chosen to
  fit an 8GB-RAM machine. Two concrete, reproducible failure modes were found
  and mitigated during development (see the field-ordering and prompt notes
  in `judge.py`): (1) the model scored answer relevance more reliably once
  the schema was reordered to generate the explanation *before* the numeric
  score — committing to a number first and rationalizing afterward produced
  visibly wrong scores; (2) on refusal answers, claim extraction would
  occasionally pull claims from the retrieved *context* rather than the
  *answer* text, despite explicit instructions not to — observed in 1 of 84
  (question, strategy) pairs in the included run (see Results, Case 3).
  Both were reduced by tightening the system prompts but not eliminated
  entirely; this is an inherent characteristic of a 3B model on a
  reasoning-heavy judging task. For a rigorous production eval, run with
  `--backend api` and a full-size judge model.
- **One chunk per document in this corpus.** Given the corpus's document
  lengths, the chunker produces exactly one chunk per document, so
  "multi-chunk" questions in the eval set are effectively multi-document. The
  chunker itself does split longer documents (see `tests/test_corpus.py`);
  this is a property of this specific synthetic corpus, not a limitation of
  the chunking code.
- **Small corpus.** 40 documents / 28 questions is enough to see retrieval
  strategies diverge and to validate the framework, not enough for tight
  statistical confidence intervals. The framework scales to larger corpora
  without code changes; only wall-clock time and (for the API backend) cost
  change.
