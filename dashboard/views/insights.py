"""Insights: automated, data-derived findings — not an LLM call, not fixed copy.

Every card here is computed live from the loaded results DataFrame and
summary. Re-run the eval with different data and these recompute honestly,
same as the rest of the dashboard — consistent with the project's
ground-truth-vs-LLM-judged transparency principle (see the Methodology
callout on Home): we don't ask an LLM to "generate insights" about its own
judged output, we compute them.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

from utils.data_loader import STRATEGY_LABELS, pick_winner

TAG_CLASS = {"finding": "pill-accent", "strength": "pill-good", "watch": "pill-warning", "risk": "pill-critical"}


def _esc(s: object) -> str:
    return html.escape(str(s))


def _card(icon: str, tag: str, title: str, body_html: str) -> str:
    tag_class = TAG_CLASS.get(tag, "pill-accent")
    return f"""
    <div class="glass-card insight-card fade-in">
      <div class="insight-head">
        <span class="insight-icon">{icon}</span>
        <span class="pill {tag_class}">{tag.upper()}</span>
      </div>
      <div class="insight-title">{_esc(title)}</div>
      <div class="insight-body">{body_html}</div>
    </div>
    """


def _label(strategy: str) -> str:
    return STRATEGY_LABELS.get(strategy, strategy)


# --------------------------------------------------------------------------
# Individual insight generators — each returns one card's (icon, tag, title, body)
# --------------------------------------------------------------------------

def insight_overall_winner(summary: pd.DataFrame) -> str:
    winner = pick_winner(summary)
    d = summary.loc[winner]
    spread = summary["ndcg_at_5"].max() - summary["ndcg_at_5"].min()
    margin_note = (
        "by a clear margin" if spread > 0.03 else
        f"by a razor-thin margin (NDCG@5 spread of only {spread:.3f} across all strategies)"
    )
    body = (
        f"<b>{_esc(_label(winner))}</b> ranks first overall, {margin_note}. It posts an NDCG@5 of "
        f"<b>{d['ndcg_at_5']:.3f}</b> and a faithfulness score of <b>{d['faithfulness_score']:.2f}</b> "
        f"(ranking is NDCG@5 first, faithfulness as tiebreaker)."
    )
    return _card("🏆", "finding", "Overall winner", body)


def insight_retrieval_saturation(summary: pd.DataFrame, n_chunks: int) -> str:
    spread = summary["ndcg_at_5"].max() - summary["ndcg_at_5"].min()
    if spread < 0.02:
        body = (
            f"NDCG@5 varies by only <b>{spread:.3f}</b> across BM25, dense, and hybrid — statistically "
            f"tied. At {n_chunks} chunks, all three retrievers reliably surface the right chunk for this "
            "eval set. The real differentiation between strategies shows up downstream, in generation "
            "and faithfulness, not in raw retrieval — see the Analytics heatmap for where."
        )
        return _card("📏", "finding", "Retrieval is saturated at this corpus size", body)
    leader = summary["ndcg_at_5"].idxmax()
    body = (
        f"<b>{_esc(_label(leader))}</b> leads retrieval quality with an NDCG@5 spread of "
        f"<b>{spread:.3f}</b> over the weakest strategy — retrieval strategy choice meaningfully "
        "affects outcomes on this corpus."
    )
    return _card("📏", "finding", "Retrieval strategies diverge", body)


def insight_relevance_leader(summary: pd.DataFrame) -> str:
    leader = summary["answer_relevance_score"].idxmax()
    laggard = summary["answer_relevance_score"].idxmin()
    gap = summary.loc[leader, "answer_relevance_score"] - summary.loc[laggard, "answer_relevance_score"]
    if gap < 0.15:
        body = "All strategies produce similarly on-topic answers — answer relevance is not a differentiator here."
        return _card("🎯", "finding", "Answer relevance is roughly even", body)
    body = (
        f"<b>{_esc(_label(leader))}</b> produces the most on-topic answers at "
        f"<b>{summary.loc[leader, 'answer_relevance_score']:.2f}/5</b>, "
        f"<b>{gap:.2f} points</b> ahead of {_esc(_label(laggard))}. Better context often means the "
        "generator has less to reconcile and stays closer to what was actually asked."
    )
    return _card("🎯", "strength", f"{_label(leader)} leads on answer relevance", body)


def insight_hallucinations(df: pd.DataFrame) -> str:
    hallucinated = df[df["has_unsupported_claim"]]
    if hallucinated.empty:
        body = f"Zero hallucinations detected across all {len(df)} evaluated answers — every unsupported claim was caught by the faithfulness judge, or none occurred."
        return _card("✅", "strength", "No hallucinations found", body)
    rows = "".join(
        f"<li><code>{_esc(r['question_id'])}</code> &middot; {_esc(_label(r['strategy']))}: "
        f"&ldquo;{_esc(next((c['text'] for c in r['claims'] if c['verdict'] == 'unsupported'), ''))[:110]}&rdquo;</li>"
        for _, r in hallucinated.iterrows()
    )
    body = (
        f"<b>{len(hallucinated)}</b> of {len(df)} evaluated answers ({len(hallucinated)/len(df)*100:.1f}%) "
        f"contain at least one unsupported claim:<ul class='insight-list'>{rows}</ul>"
    )
    return _card("⚠️", "risk", "Hallucinations detected", body)


def insight_judge_reliability(df: pd.DataFrame) -> str:
    trap_df = df[df["is_trap"]]
    judge_artifacts = trap_df[trap_df["claims"].apply(len) > 0]
    if judge_artifacts.empty:
        body = (
            f"All {len(trap_df)} trap-question evaluations correctly produced zero claims on a refusal "
            "answer — the faithfulness judge is behaving consistently on this run."
        )
        return _card("🔍", "strength", "Judge behaved consistently on trap questions", body)
    rows = "".join(
        f"<li><code>{_esc(r['question_id'])}</code> &middot; {_esc(_label(r['strategy']))} &mdash; "
        f"answer was a refusal, but the judge extracted {len(r['claims'])} claim(s) anyway</li>"
        for _, r in judge_artifacts.iterrows()
    )
    body = (
        f"<b>{len(judge_artifacts)}</b> of {len(trap_df)} trap-question evaluations show the judge "
        "extracting claims from an answer that was actually a clean refusal — almost certainly pulling "
        "from retrieved <i>context</i> instead of the <i>answer</i> text. This is a known limitation of "
        f"smaller local judge models (see the README).<ul class='insight-list'>{rows}</ul>"
        "Treat the trap-abstention numbers on Home as directionally useful, not exact, until "
        "cross-checked here."
    )
    return _card("🔍", "watch", "Judge artifact on trap question(s)", body)


def insight_context_utilization(summary: pd.DataFrame) -> str:
    noisiest = summary["context_utilization"].idxmin()
    cleanest = summary["context_utilization"].idxmax()
    body = (
        f"<b>{_esc(_label(cleanest))}</b> has the highest context utilization at "
        f"<b>{summary.loc[cleanest, 'context_utilization']:.1%}</b> — more of what it retrieves actually "
        f"ends up supporting a claim in the answer. {_esc(_label(noisiest))} is lowest at "
        f"<b>{summary.loc[noisiest, 'context_utilization']:.1%}</b>, meaning more of its retrieved chunks "
        "go unused — not necessarily wrong, but noisier context for the generator to sift through."
    )
    return _card("🧹", "finding", "Context utilization varies", body)


def insight_difficulty_breakdown(df: pd.DataFrame) -> str:
    present = [d for d in ["easy", "medium", "trap"] if d in df["difficulty"].unique()]
    by_diff = df.groupby("difficulty")["faithfulness_score"].mean()
    hardest = by_diff.idxmin()
    if by_diff.max() - by_diff.min() < 0.03:
        body = "Faithfulness holds steady across easy, medium, and trap questions alike — difficulty tier isn't driving quality here."
        return _card("📚", "finding", "Difficulty tier doesn't move the needle", body)
    body = (
        f"Mean faithfulness is lowest on <b>{_esc(hardest)}</b> questions "
        f"(<b>{by_diff[hardest]:.2f}</b>) versus <b>{by_diff.max():.2f}</b> on the strongest tier — "
        + (
            "multi-chunk synthesis questions are the harder case for grounding an answer correctly."
            if hardest == "medium"
            else "trap questions (where the correct move is refusal) are the harder case to get right."
            if hardest == "trap"
            else ""
        )
    )
    return _card("📚", "watch", f"{hardest.capitalize()} questions are the weak point", body)


def build_recommendation(summary: pd.DataFrame, df: pd.DataFrame) -> str:
    winner = pick_winner(summary)
    ndcg_spread = summary["ndcg_at_5"].max() - summary["ndcg_at_5"].min()
    hallucination_rate = summary["hallucination_rate"].max()
    relevance_leader = summary["answer_relevance_score"].idxmax()

    lines = [f"<b>{_esc(_label(winner))}</b> is the recommended default for this corpus and eval set."]
    if ndcg_spread < 0.02:
        lines.append(
            "Retrieval quality alone won't tell you which strategy to pick here — they're tied. "
            "The deciding factors are downstream: answer relevance and hallucination rate."
        )
    if relevance_leader != winner:
        lines.append(
            f"If answer relevance matters most for your use case, consider {_esc(_label(relevance_leader))} "
            f"instead — it leads that specific metric."
        )
    if hallucination_rate > 0:
        lines.append(
            f"Before shipping any strategy, review the {int((df['has_unsupported_claim']).sum())} flagged "
            "hallucination case(s) in Data Explorer — a single unsupported claim in a policy or pricing "
            "answer can matter more than an aggregate score."
        )
    lines.append(
        "This recommendation is entirely derived from the current run's numbers — re-run the eval "
        "against a larger or harder corpus before treating it as final."
    )
    return " ".join(lines)


def render(df: pd.DataFrame, summary: pd.DataFrame, corpus_stats) -> None:
    st.markdown('<div class="section-title">Insights</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Automated findings computed live from the real results &mdash; not '
        "an LLM asked to summarize its own output. Re-run the eval and these recompute.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    cards = [
        insight_overall_winner(summary),
        insight_retrieval_saturation(summary, corpus_stats.doc_count),
        insight_relevance_leader(summary),
        insight_hallucinations(df),
        insight_judge_reliability(df),
        insight_context_utilization(summary),
        insight_difficulty_breakdown(df),
    ]

    col_a, col_b = st.columns(2)
    for i, card_html in enumerate(cards):
        with (col_a if i % 2 == 0 else col_b):
            st.markdown(card_html, unsafe_allow_html=True)

    st.write("")
    st.markdown(
        f"""
        <div class="hero fade-in" style="padding:32px 36px;">
          <div class="hero-eyebrow">Recommendation</div>
          <div style="font-size:15px;color:var(--ink-primary);line-height:1.7;max-width:78ch;">
            {build_recommendation(summary, df)}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
