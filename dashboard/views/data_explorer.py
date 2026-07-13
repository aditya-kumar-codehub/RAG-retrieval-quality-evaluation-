"""Data Explorer: search, filter, page through, and inspect every real per-question result.

Reads the already-loaded results DataFrame (see utils/data_loader.py) — no
extra I/O here. Row selection uses st.dataframe's native selection event API
(Streamlit >=1.35) rather than a custom click handler.
"""

from __future__ import annotations

import html

import pandas as pd
import streamlit as st

STRATEGY_COLORS = {"bm25": "#5b8cff", "dense": "#2dd4bf", "hybrid": "#a78bfa"}
STRATEGY_LABELS = {"bm25": "BM25", "dense": "Dense", "hybrid": "Hybrid (RRF)"}
VERDICT_ICON = {"supported": "✓", "unsupported": "✕", "partial": "±"}

PAGE_SIZE = 12


def _esc(s: object) -> str:
    return html.escape(str(s))


def _init_state() -> None:
    st.session_state.setdefault("explorer_page", 1)


def _apply_filters(
    df: pd.DataFrame,
    search: str,
    strategies: list[str],
    difficulties: list[str],
    only_hallucinated: bool,
    only_trap: bool,
) -> pd.DataFrame:
    out = df
    if strategies:
        out = out[out["strategy"].isin(strategies)]
    if difficulties:
        out = out[out["difficulty"].isin(difficulties)]
    if only_hallucinated:
        out = out[out["has_unsupported_claim"]]
    if only_trap:
        out = out[out["is_trap"]]
    if search:
        s = search.lower()
        mask = (
            out["question"].str.lower().str.contains(s, regex=False)
            | out["generated_answer"].str.lower().str.contains(s, regex=False)
        )
        out = out[mask]
    return out


def render(df: pd.DataFrame) -> None:
    _init_state()

    st.markdown('<div class="section-title">Data Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Search, filter, and inspect all real per-question results. '
        "Click a row to see the full answer and claim-level faithfulness breakdown.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    f1, f2, f3, f4, f5 = st.columns([2.2, 1.3, 1.3, 1, 1])
    with f1:
        search = st.text_input(
            "Search", placeholder="Search questions or answers…", label_visibility="collapsed"
        )
    with f2:
        strategies = st.multiselect(
            "Strategy",
            options=list(STRATEGY_LABELS.keys()),
            format_func=lambda s: STRATEGY_LABELS[s],
            label_visibility="collapsed",
            placeholder="All strategies",
        )
    with f3:
        difficulties = st.multiselect(
            "Difficulty",
            options=["easy", "medium", "trap"],
            label_visibility="collapsed",
            placeholder="All difficulties",
        )
    with f4:
        only_hallucinated = st.toggle("⚠ Hallucinated")
    with f5:
        only_trap = st.toggle("Trap only")

    filtered = _apply_filters(df, search, strategies, difficulties, only_hallucinated, only_trap)
    filtered = filtered.sort_values(["question_id", "strategy"]).reset_index(drop=True)

    st.markdown(
        f'<div style="font-size:12.5px;color:var(--ink-muted);margin:4px 0 14px;'
        f'font-family:var(--font-mono);">{len(filtered)} of {len(df)} results</div>',
        unsafe_allow_html=True,
    )

    if filtered.empty:
        st.markdown(
            '<div class="coming-soon"><div class="coming-soon-icon">🔍</div>'
            "<h3>No matches</h3><p>Try clearing a filter or search term.</p></div>",
            unsafe_allow_html=True,
        )
        return

    total_pages = max(1, -(-len(filtered) // PAGE_SIZE))
    st.session_state["explorer_page"] = min(st.session_state["explorer_page"], total_pages)
    page = st.session_state["explorer_page"]
    start, end = (page - 1) * PAGE_SIZE, page * PAGE_SIZE
    page_df = filtered.iloc[start:end]

    display_df = page_df[
        ["question_id", "question", "strategy", "difficulty", "recall_at_5", "faithfulness_score", "answer_relevance_score"]
    ].rename(
        columns={
            "question_id": "ID",
            "question": "Question",
            "strategy": "Strategy",
            "difficulty": "Difficulty",
            "recall_at_5": "Recall@5",
            "faithfulness_score": "Faithfulness",
            "answer_relevance_score": "Relevance",
        }
    )
    display_df["Strategy"] = display_df["Strategy"].map(STRATEGY_LABELS)

    event = st.dataframe(
        display_df,
        width="stretch",
        hide_index=True,
        height=min(460, 46 + 35 * len(page_df)),
        column_config={
            "ID": st.column_config.TextColumn(width="small"),
            "Question": st.column_config.TextColumn(width="large"),
            "Recall@5": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
            "Faithfulness": st.column_config.ProgressColumn(min_value=0, max_value=1, format="%.2f"),
            "Relevance": st.column_config.NumberColumn(format="%d / 5"),
        },
        selection_mode="single-row",
        on_select="rerun",
        key=f"explorer_table_{page}",
    )

    p1, p2, p3 = st.columns([1, 2, 1])
    with p1:
        if st.button("← Previous", disabled=page <= 1, width="stretch"):
            st.session_state["explorer_page"] -= 1
            st.rerun()
    with p2:
        st.markdown(
            f'<div style="text-align:center;font-family:var(--font-mono);font-size:12px;'
            f'color:var(--ink-muted);padding-top:8px;">Page {page} of {total_pages}</div>',
            unsafe_allow_html=True,
        )
    with p3:
        if st.button("Next →", disabled=page >= total_pages, width="stretch"):
            st.session_state["explorer_page"] += 1
            st.rerun()

    st.write("")
    csv_bytes = filtered.drop(columns=["claims"]).to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇ Download filtered results (CSV)",
        data=csv_bytes,
        file_name="rag_eval_results_filtered.csv",
        mime="text/csv",
    )

    selected_rows = event.selection.rows if event and event.selection else []
    if selected_rows:
        row = page_df.iloc[selected_rows[0]]
        st.write("")
        st.markdown(build_detail_html(row), unsafe_allow_html=True)


def build_detail_html(row: pd.Series) -> str:
    """Build the full row-detail panel as a single HTML string.

    Deliberately assembled as one block rather than several st.markdown()
    calls — each st.markdown() call is its own DOM node in Streamlit, so a
    <div> opened in one call and closed in a later call would not actually
    wrap the content in between.
    """
    color = STRATEGY_COLORS.get(row["strategy"], "#888")
    strategy_label = STRATEGY_LABELS.get(row["strategy"], row["strategy"])
    trap_badge = '<span class="pill pill-warning" style="margin-left:6px;">TRAP QUESTION</span>' if row["is_trap"] else ""

    gold = set(row["relevant_chunk_ids"])
    retrieved_html = "".join(
        f'<span class="chunk-pill {"is-gold" if cid in gold else ""}">{_esc(cid)}</span>'
        for cid in row["retrieved_chunk_ids"]
    ) or '<span class="chunk-pill">none</span>'
    gold_html = "".join(
        f'<span class="chunk-pill is-gold">{_esc(cid)}</span>' for cid in row["relevant_chunk_ids"]
    ) or '<span class="chunk-pill">none — trap question</span>'

    claims_html = "".join(
        f'<div class="claim-row v-{c["verdict"]}">'
        f'<span class="claim-icon">{VERDICT_ICON.get(c["verdict"], "?")}</span>'
        f'<span>{_esc(c["text"])}</span></div>'
        for c in row["claims"]
    ) or '<div style="color:var(--ink-muted);font-size:13px;">No claims extracted.</div>'

    return f"""
    <div class="glass-card fade-in">
      <div class="field-label">Question &middot; {_esc(row['question_id'])}</div>
      <div style="font-size:15px;font-weight:600;color:var(--ink-primary);margin-bottom:10px;">
        {_esc(row['question'])}
      </div>
      <span class="strategy-chip" style="background:{color}">{strategy_label}</span>
      <span class="pill pill-accent" style="margin-left:6px;">{_esc(row['difficulty'])}</span>
      {trap_badge}

      <div class="field-label">Retrieved chunks <span style="text-transform:none;">(gold outlined)</span></div>
      {retrieved_html}

      <div class="field-label">Gold-relevant chunks</div>
      {gold_html}

      <div class="field-label">Generated answer</div>
      <div class="answer-box">{_esc(row['generated_answer'])}</div>

      <div class="field-label">Faithfulness &mdash; {row['faithfulness_score']:.2f}</div>
      {claims_html}

      <div class="field-label">Answer relevance &mdash; {row['answer_relevance_score']}/5</div>
      <div style="font-size:13px;color:var(--ink-secondary);">{_esc(row['answer_relevance_explanation'])}</div>
    </div>
    """
