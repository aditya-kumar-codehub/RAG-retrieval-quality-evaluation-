"""Build the markdown comparison report (+ charts) from a completed evaluation run.

Aggregation is kept in pandas; charts are static matplotlib PNGs embedded in
the markdown report. Chart styling follows a small fixed categorical palette
(blue / aqua / yellow, in that fixed order) so strategy identity stays
consistent across every chart in the report.
"""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from rag_eval.runner import QuestionResult

# Fixed categorical palette, assigned by strategy identity (never re-cycled).
STRATEGY_COLORS = {
    "bm25": "#2a78d6",  # blue
    "dense": "#1baf7a",  # aqua
    "hybrid": "#eda100",  # yellow
}
STRATEGY_ORDER = ["bm25", "dense", "hybrid"]
STRATEGY_LABELS = {"bm25": "BM25", "dense": "Dense", "hybrid": "Hybrid (RRF)"}

INK = "#0b0b0b"
SECONDARY_INK = "#52514e"
MUTED = "#898781"
GRIDLINE = "#e1e0d9"
SURFACE = "#fcfcfb"


def _ordered_strategies(present: list[str]) -> list[str]:
    return [s for s in STRATEGY_ORDER if s in present] + [
        s for s in present if s not in STRATEGY_ORDER
    ]


def results_to_dataframe(results: list[QuestionResult]) -> pd.DataFrame:
    rows = []
    for r in results:
        rows.append(
            {
                "question_id": r.question_id,
                "question": r.question,
                "difficulty": r.difficulty,
                "is_trap": r.is_trap,
                "strategy": r.strategy,
                "precision_at_3": r.retrieval_metrics.precision_at_k.get(3),
                "precision_at_5": r.retrieval_metrics.precision_at_k.get(5),
                "precision_at_10": r.retrieval_metrics.precision_at_k.get(10),
                "recall_at_3": r.retrieval_metrics.recall_at_k.get(3),
                "recall_at_5": r.retrieval_metrics.recall_at_k.get(5),
                "recall_at_10": r.retrieval_metrics.recall_at_k.get(10),
                "ndcg_at_3": r.retrieval_metrics.ndcg_at_k.get(3),
                "ndcg_at_5": r.retrieval_metrics.ndcg_at_k.get(5),
                "ndcg_at_10": r.retrieval_metrics.ndcg_at_k.get(10),
                "mrr": r.retrieval_metrics.mrr,
                "faithfulness_score": r.faithfulness_score,
                "has_unsupported_claim": r.has_unsupported_claim,
                "num_claims": len(r.claims),
                "answer_relevance_score": r.answer_relevance_score,
                "context_utilization": r.context_utilization,
                "correctly_abstained": r.is_trap and len(r.claims) == 0,
            }
        )
    return pd.DataFrame(rows)


def summarize_by_strategy(df: pd.DataFrame) -> pd.DataFrame:
    """One row per strategy with mean metrics across all questions."""
    agg = df.groupby("strategy").agg(
        precision_at_5=("precision_at_5", "mean"),
        recall_at_5=("recall_at_5", "mean"),
        ndcg_at_5=("ndcg_at_5", "mean"),
        mrr=("mrr", "mean"),
        faithfulness_score=("faithfulness_score", "mean"),
        pct_answers_fully_faithful=("has_unsupported_claim", lambda s: 1 - s.mean()),
        hallucination_rate=("has_unsupported_claim", "mean"),
        answer_relevance_score=("answer_relevance_score", "mean"),
        context_utilization=("context_utilization", "mean"),
    )
    trap_df = df[df["is_trap"]]
    if not trap_df.empty:
        abstention = trap_df.groupby("strategy")["correctly_abstained"].mean()
        agg["trap_abstention_rate"] = abstention
    else:
        agg["trap_abstention_rate"] = float("nan")
    return agg.reindex(_ordered_strategies(list(agg.index)))


def _grouped_bar_chart(
    ax,
    metric_labels: list[str],
    strategy_values: dict[str, list[float]],
    strategies: list[str],
    ylabel: str,
    ylim: tuple[float, float] = (0.0, 1.0),
) -> None:
    n_metrics = len(metric_labels)
    n_strategies = len(strategies)
    bar_width = 0.8 / n_strategies
    x = range(n_metrics)

    for i, strategy in enumerate(strategies):
        offsets = [xi + (i - (n_strategies - 1) / 2) * bar_width for xi in x]
        values = strategy_values[strategy]
        bars = ax.bar(
            offsets,
            values,
            width=bar_width * 0.9,
            color=STRATEGY_COLORS.get(strategy, "#898781"),
            label=STRATEGY_LABELS.get(strategy, strategy),
            zorder=3,
        )
        for bar, val in zip(bars, values):
            ax.annotate(
                f"{val:.2f}",
                xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
                xytext=(0, 3),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=8,
                color=SECONDARY_INK,
            )

    ax.set_xticks(list(x))
    ax.set_xticklabels(metric_labels, color=INK)
    ax.set_ylabel(ylabel, color=INK)
    ax.set_ylim(*ylim)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRIDLINE)
    ax.spines["bottom"].set_color(GRIDLINE)
    ax.tick_params(colors=MUTED)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.legend(frameon=False, labelcolor=SECONDARY_INK, fontsize=9, loc="upper right")
    ax.set_facecolor(SURFACE)


def plot_retrieval_metrics(summary: pd.DataFrame, out_path: Path) -> None:
    strategies = list(summary.index)
    metric_cols = ["precision_at_5", "recall_at_5", "ndcg_at_5", "mrr"]
    metric_labels = ["Precision@5", "Recall@5", "NDCG@5", "MRR"]
    strategy_values = {s: [summary.loc[s, c] for c in metric_cols] for s in strategies}

    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=SURFACE)
    _grouped_bar_chart(ax, metric_labels, strategy_values, strategies, "Score (0-1)")
    ax.set_title("Retrieval quality by strategy", color=INK, fontsize=12, loc="left", pad=12)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_faithfulness(summary: pd.DataFrame, out_path: Path) -> None:
    strategies = list(summary.index)
    metric_cols = ["faithfulness_score", "pct_answers_fully_faithful", "trap_abstention_rate"]
    metric_labels = ["Faithfulness\nscore", "Answers with\nno unsupported claims", "Trap question\nabstention rate"]
    strategy_values = {s: [summary.loc[s, c] for c in metric_cols] for s in strategies}

    fig, ax = plt.subplots(figsize=(7, 4.5), facecolor=SURFACE)
    _grouped_bar_chart(ax, metric_labels, strategy_values, strategies, "Score (0-1)")
    ax.set_title(
        "Faithfulness and hallucination avoidance by strategy (LLM-judged)",
        color=INK,
        fontsize=12,
        loc="left",
        pad=12,
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def plot_answer_relevance(summary: pd.DataFrame, out_path: Path) -> None:
    strategies = list(summary.index)
    values = [summary.loc[s, "answer_relevance_score"] for s in strategies]

    fig, ax = plt.subplots(figsize=(5.5, 4), facecolor=SURFACE)
    bars = ax.bar(
        [STRATEGY_LABELS.get(s, s) for s in strategies],
        values,
        color=[STRATEGY_COLORS.get(s, "#898781") for s in strategies],
        width=0.5,
        zorder=3,
    )
    for bar, val in zip(bars, values):
        ax.annotate(
            f"{val:.2f}",
            xy=(bar.get_x() + bar.get_width() / 2, bar.get_height()),
            xytext=(0, 3),
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=9,
            color=SECONDARY_INK,
        )
    ax.set_ylabel("Mean answer relevance (1-5)", color=INK)
    ax.set_ylim(0, 5)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(GRIDLINE)
    ax.spines["bottom"].set_color(GRIDLINE)
    ax.tick_params(colors=MUTED)
    ax.yaxis.grid(True, color=GRIDLINE, linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    ax.set_title(
        "Answer relevance by strategy (LLM-judged)", color=INK, fontsize=12, loc="left", pad=12
    )
    fig.tight_layout()
    fig.savefig(out_path, dpi=150, facecolor=SURFACE)
    plt.close(fig)


def _pick_failure_examples(df: pd.DataFrame, results: list[QuestionResult], n: int = 3) -> list[QuestionResult]:
    """Pick a few illustrative failure cases: a hallucination, a retrieval miss, a trap failure."""
    by_key = {(r.question_id, r.strategy): r for r in results}
    examples: list[QuestionResult] = []

    hallucinated = df[df["has_unsupported_claim"]].sort_values("faithfulness_score")
    if not hallucinated.empty:
        row = hallucinated.iloc[0]
        examples.append(by_key[(row["question_id"], row["strategy"])])

    # Prefer a complete miss (recall@5 == 0); fall back to the weakest partial
    # miss (lowest NDCG@5 among questions that didn't retrieve every gold chunk)
    # so there's still an illustrative retrieval-quality example even when every
    # strategy finds at least one relevant chunk for every question.
    retrieval_miss = df[(~df["is_trap"]) & (df["recall_at_5"] == 0)]
    if retrieval_miss.empty:
        retrieval_miss = df[(~df["is_trap"]) & (df["recall_at_5"] < 1.0)].sort_values("ndcg_at_5")
    if not retrieval_miss.empty:
        row = retrieval_miss.iloc[0]
        examples.append(by_key[(row["question_id"], row["strategy"])])

    trap_failures = df[df["is_trap"] & (~df["correctly_abstained"])]
    if not trap_failures.empty:
        row = trap_failures.iloc[0]
        examples.append(by_key[(row["question_id"], row["strategy"])])

    seen = set()
    unique_examples = []
    for ex in examples:
        key = (ex.question_id, ex.strategy)
        if key not in seen:
            seen.add(key)
            unique_examples.append(ex)
    return unique_examples[:n]


def _format_example(r: QuestionResult) -> str:
    claims_summary = "\n".join(
        f"  - [{c['verdict']}] {c['text']}" for c in r.claims
    ) or "  (no claims extracted)"
    return f"""**Question** ({r.strategy}, {r.difficulty}): {r.question}

**Retrieved chunks:** {", ".join(r.retrieved_chunk_ids)}
**Gold-relevant chunks:** {", ".join(r.relevant_chunk_ids) or "(none — trap question)"}

**Generated answer:** {r.generated_answer}

**Faithfulness:** {r.faithfulness_score:.2f} (claims:
{claims_summary}
)

**Answer relevance:** {r.answer_relevance_score}/5 — {r.answer_relevance_explanation}
"""


def build_report(
    results: list[QuestionResult],
    out_dir: str | Path,
    generator_model: str = "",
    judge_model: str = "",
) -> Path:
    """Build the markdown report + charts for a completed run. Returns the report path."""
    out_dir = Path(out_dir)
    charts_dir = out_dir / "charts"
    charts_dir.mkdir(parents=True, exist_ok=True)

    df = results_to_dataframe(results)
    summary = summarize_by_strategy(df)

    plot_retrieval_metrics(summary, charts_dir / "retrieval_metrics.png")
    plot_faithfulness(summary, charts_dir / "faithfulness.png")
    plot_answer_relevance(summary, charts_dir / "answer_relevance.png")

    ranked = summary.sort_values(
        by=["ndcg_at_5", "faithfulness_score"], ascending=False
    )
    winner = ranked.index[0] if not ranked.empty else "N/A"

    lines: list[str] = []
    lines.append("# RAG Retrieval Quality Report\n")
    lines.append(
        f"Generator model: `{generator_model}` &nbsp;|&nbsp; Judge model: `{judge_model}` "
        f"&nbsp;|&nbsp; Questions evaluated: {df['question_id'].nunique()} "
        f"&nbsp;|&nbsp; Strategies compared: {', '.join(STRATEGY_LABELS.get(s, s) for s in summary.index)}\n"
    )
    lines.append(
        "> **Methodology note:** Precision@k, Recall@k, NDCG@k, and MRR are computed against "
        "hand-labeled gold-relevant chunk IDs — they are ground truth. Faithfulness, the "
        "hallucination-related metrics, trap abstention rate, and answer relevance are "
        "**LLM-judged** (by the judge model above) and should be read as a consistent, "
        "explainable proxy rather than ground truth.\n"
    )

    lines.append(f"## Summary: {STRATEGY_LABELS.get(winner, winner)} wins\n")
    lines.append(
        f"Ranked by NDCG@5 (retrieval quality) then faithfulness score (answer grounding) "
        f"as a tiebreaker, **{STRATEGY_LABELS.get(winner, winner)}** performed best overall on "
        f"this eval set. See the per-metric tables and charts below for the full picture — "
        f"the best strategy can vary by metric.\n"
    )

    lines.append("## Retrieval Metrics (ground truth)\n")
    lines.append("![Retrieval metrics](charts/retrieval_metrics.png)\n")
    retrieval_table = summary[
        [
            "precision_at_5",
            "recall_at_5",
            "ndcg_at_5",
            "mrr",
        ]
    ].rename(
        columns={
            "precision_at_5": "Precision@5",
            "recall_at_5": "Recall@5",
            "ndcg_at_5": "NDCG@5",
            "mrr": "MRR",
        }
    )
    retrieval_table.index = [STRATEGY_LABELS.get(s, s) for s in retrieval_table.index]
    lines.append(retrieval_table.round(3).to_markdown())
    lines.append("")

    lines.append("\n## Faithfulness and Hallucination (LLM-judged)\n")
    lines.append("![Faithfulness](charts/faithfulness.png)\n")
    faith_table = summary[
        ["faithfulness_score", "hallucination_rate", "trap_abstention_rate", "context_utilization"]
    ].rename(
        columns={
            "faithfulness_score": "Faithfulness score",
            "hallucination_rate": "Hallucination rate (>=1 unsupported claim)",
            "trap_abstention_rate": "Trap question abstention rate",
            "context_utilization": "Context utilization",
        }
    )
    faith_table.index = [STRATEGY_LABELS.get(s, s) for s in faith_table.index]
    lines.append(faith_table.round(3).to_markdown())
    lines.append("")

    lines.append("\n## Answer Relevance (LLM-judged)\n")
    lines.append("![Answer relevance](charts/answer_relevance.png)\n")
    rel_table = summary[["answer_relevance_score"]].rename(
        columns={"answer_relevance_score": "Mean answer relevance (1-5)"}
    )
    rel_table.index = [STRATEGY_LABELS.get(s, s) for s in rel_table.index]
    lines.append(rel_table.round(2).to_markdown())
    lines.append("")

    lines.append("\n## Example Failure Cases\n")
    examples = _pick_failure_examples(df, results)
    if not examples:
        lines.append("No failure cases found in this run — all answers were faithful, all "
                      "non-trap questions retrieved a relevant chunk, and all trap questions "
                      "were correctly declined.\n")
    for i, ex in enumerate(examples, start=1):
        lines.append(f"### Case {i}\n")
        lines.append(_format_example(ex))
        lines.append("")

    lines.append("\n## Per-Question Results\n")
    lines.append(
        "Full per-question, per-strategy results are saved alongside this report in "
        "`results.json` for further inspection.\n"
    )

    report_text = "\n".join(lines)
    report_path = out_dir / "report.md"
    report_path.write_text(report_text, encoding="utf-8")
    return report_path
