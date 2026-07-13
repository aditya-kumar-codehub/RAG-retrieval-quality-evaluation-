"""RAG Retrieval Quality — premium Streamlit dashboard.

Entry point. Renders the app shell (theme, sidebar nav) and the Home page
(hero, KPI cards, headline charts) from a real completed evaluation run.
Every nav destination is implemented — see views/ for Analytics, Query
Explorer, Data Explorer, Insights, and About.

Run from the `dashboard/` directory:

    streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from streamlit_option_menu import option_menu

from utils.html import flatten as _flatten_html

# Patch st.markdown so every unsafe_allow_html=True call across the app is
# automatically protected from CommonMark's "4+ leading spaces = literal
# code block" rule (see utils/html.py for the full explanation — this is a
# real bug that was silently breaking most of the app's custom-HTML cards,
# turning them into visible raw markup instead of rendering). Applied once,
# here, at the entry point, before any view module runs — every
# st.markdown(..., unsafe_allow_html=True) call in app.py and views/*.py
# benefits automatically, without 50+ individual call-site edits that would
# have meant reconstructing every file and losing every comment in it.
_original_markdown = st.markdown


def _patched_markdown(body="", *args, **kwargs):
    if kwargs.get("unsafe_allow_html") and isinstance(body, str):
        body = _flatten_html(body)
    return _original_markdown(body, *args, **kwargs)


st.markdown = _patched_markdown

from views import about, analytics, data_explorer, insights, query_explorer
from utils.data_loader import (
    STRATEGY_LABELS,
    STRATEGY_ORDER,
    list_runs,
    load_corpus_stats,
    load_results_raw,
    pick_winner,
    results_to_dataframe,
    summarize_by_strategy,
)

APP_DIR = Path(__file__).resolve().parent

NAV_OPTIONS = ["Home", "Analytics", "Query Explorer", "Data Explorer", "Insights", "About"]

PLOTLY_DARK_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#a4a4b3", size=12),
    margin=dict(l=0, r=10, t=10, b=0),
    legend=dict(
        orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0,
        font=dict(size=11.5, color="#a4a4b3"), bgcolor="rgba(0,0,0,0)",
    ),
)
GRID_COLOR = "rgba(255,255,255,0.07)"


# --------------------------------------------------------------------------
# Page config + theme injection (must run before any other st.* call)
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def _load_css() -> str:
    return (APP_DIR / "css" / "theme.css").read_text(encoding="utf-8")


def configure_page() -> None:
    st.set_page_config(
        page_title="RAG Retrieval Quality",
        page_icon="◆",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown(f"<style>{_load_css()}</style>", unsafe_allow_html=True)


# --------------------------------------------------------------------------
# Data loading (cached — re-reads only when the underlying file changes)
# --------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_active_run(run_dir_str: str) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    run_dir = Path(run_dir_str)
    raw = load_results_raw(run_dir)
    df = results_to_dataframe(raw)
    summary = summarize_by_strategy(df)
    return df, summary, raw


# --------------------------------------------------------------------------
# Small reusable components
# --------------------------------------------------------------------------

def render_sidebar(run_dirs: list[Path], active_run_dir: Path) -> str:
    with st.sidebar:
        st.markdown(
            """
            <div class="sidebar-logo">
              <div class="sidebar-logo-mark">R</div>
              <div>
                <div class="sidebar-logo-text">RAG Quality</div>
                <div class="sidebar-logo-sub">EVALUATOR</div>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # streamlit-option-menu is a third-party bidirectional component; its
        # cross-rerun persistence (remembering the last click when some *other*
        # unrelated widget on the destination page triggers a rerun) isn't
        # reliable to depend on. So `current_page` in session_state — plain
        # Python state — is the single source of truth, and option_menu is
        # driven as a fully *controlled* component via `manual_select` on
        # every render, not just for one-shot programmatic overrides (e.g.
        # the Home page's CTA buttons). Its own return value is only used to
        # detect a fresh user click and update that source of truth.
        st.session_state.setdefault("current_page", NAV_OPTIONS[0])
        if "nav_override" in st.session_state:
            st.session_state["current_page"] = st.session_state.pop("nav_override")
        current_index = NAV_OPTIONS.index(st.session_state["current_page"])

        selected = option_menu(
            menu_title=None,
            options=NAV_OPTIONS,
            icons=["house", "bar-chart-line", "search", "table", "lightbulb", "info-circle"],
            default_index=current_index,
            manual_select=current_index,
            key="main_nav_menu",
            # streamlit-option-menu renders inside its own component iframe — CSS
            # in theme.css cannot cross that boundary at all, so every style this
            # nav needs has to be specified here, not left to theme.css to patch
            # in. Any state not explicitly set below falls back to the library's
            # own default (a reddish accent), not this app's palette.
            styles={
                "container": {"padding": "0", "background-color": "transparent"},
                "icon": {"font-size": "15px", "color": "#a4a4b3"},
                "nav-link": {
                    "font-size": "13.5px",
                    "padding": "10px 14px",
                    "color": "#a4a4b3",
                    "background-color": "transparent",
                    "--hover-color": "#232323",
                },
                "nav-link-selected": {
                    "background-color": "#5b6ef5",
                    "color": "#f4f4f7",
                    "font-weight": "600",
                },
            },
        )
        st.session_state["current_page"] = selected

        if len(run_dirs) > 1:
            with st.expander("⚙ Settings", expanded=False):
                names = [p.name for p in run_dirs]
                idx = names.index(active_run_dir.name) if active_run_dir.name in names else 0
                choice = st.selectbox("Active run", names, index=idx)
                active_run_dir = run_dirs[names.index(choice)]

        df, _, raw = load_active_run(str(active_run_dir))
        generator_model = raw[0]["generator_model"] if raw else "—"
        st.markdown(
            f"""
            <div class="run-info-card">
              <div class="run-info-row"><span><span class="status-dot"></span>status</span><b>ready</b></div>
              <div class="run-info-row"><span>run</span><b>{active_run_dir.name}</b></div>
              <div class="run-info-row"><span>backend</span><b>{generator_model}</b></div>
              <div class="run-info-row"><span>questions</span><b>{df['question_id'].nunique()}</b></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    return selected, active_run_dir


def render_animated_stats(items: list[tuple[str, float, str]]) -> None:
    """items: list of (label, value, suffix). Staggered CSS fade-in-up, no JS/iframe.

    A previous version used a JS requestAnimationFrame count-up rendered via
    st.iframe. Iframes are one of the heaviest DOM primitives available — a
    separate browsing context, rebuilt from scratch on every single visit to
    Home (every navigation *to* Home reruns this) — and were a real
    contributor to felt navigation lag. A staggered opacity/transform-only
    CSS animation (reusing the .fade-in.d1-d4 delay classes already in
    theme.css) gives nearly the same "alive" feel at negligible cost: no
    separate browsing context, no JS loop, no layout/backdrop recomposition.
    """
    delay_classes = ["d1", "d2", "d3", "d4"]
    cells = "".join(
        f"""
        <div class="stat-item fade-in {delay_classes[i % len(delay_classes)]}">
          <div class="stat-value">{value}{suffix}</div>
          <div class="stat-label">{label}</div>
        </div>
        """
        for i, (label, value, suffix) in enumerate(items)
    )
    st.markdown(f'<div class="stat-row">{cells}</div>', unsafe_allow_html=True)


def render_kpi_card(label: str, value: str, sub: str, pill_text: str, pill_class: str) -> str:
    return f"""
    <div class="glass-card kpi-card fade-in">
      <div class="kpi-label">{label} <span class="pill {pill_class}">{pill_text}</span></div>
      <div class="kpi-value">{value}</div>
      <div class="kpi-sub">{sub}</div>
    </div>
    """


def render_progress_bars(summary: pd.DataFrame, column: str, title: str) -> None:
    st.markdown(f'<div class="section-title" style="font-size:14px;">{title}</div>', unsafe_allow_html=True)
    for strategy in summary.index:
        val = summary.loc[strategy, column]
        pct = 0 if pd.isna(val) else val * 100
        st.markdown(
            f"""
            <div class="progress-row">
              <div class="progress-row-head">
                <span>{STRATEGY_LABELS.get(strategy, strategy)}</span>
                <b>{pct:.1f}%</b>
              </div>
              <div class="progress-track"><div class="progress-fill" style="width:{pct}%;"></div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def strategy_bar_chart(summary: pd.DataFrame) -> go.Figure:
    colors = {"bm25": "#5b8cff", "dense": "#2dd4bf", "hybrid": "#a78bfa"}
    metrics = [("precision_at_5", "Precision@5"), ("recall_at_5", "Recall@5"),
               ("ndcg_at_5", "NDCG@5"), ("mrr", "MRR")]
    fig = go.Figure()
    for strategy in summary.index:
        fig.add_trace(
            go.Bar(
                name=STRATEGY_LABELS.get(strategy, strategy),
                x=[label for _, label in metrics],
                y=[summary.loc[strategy, key] for key, _ in metrics],
                marker_color=colors.get(strategy, "#888"),
                marker_line_width=0,
                text=[f"{summary.loc[strategy, key]:.2f}" for key, _ in metrics],
                textposition="outside",
                textfont=dict(size=10.5, color="#a4a4b3"),
            )
        )
    fig.update_layout(
        **PLOTLY_DARK_LAYOUT,
        barmode="group",
        bargap=0.28,
        bargroupgap=0.12,
        height=320,
        yaxis=dict(range=[0, 1.08], gridcolor=GRID_COLOR, zeroline=False),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def claim_verdict_pie(df: pd.DataFrame) -> go.Figure:
    verdict_counts: dict[str, int] = {"supported": 0, "partial": 0, "unsupported": 0}
    for claims in df["claims"]:
        for c in claims:
            verdict_counts[c["verdict"]] = verdict_counts.get(c["verdict"], 0) + 1
    colors = {"supported": "#34d399", "partial": "#fbbf24", "unsupported": "#f87171"}
    labels = list(verdict_counts.keys())
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[l.capitalize() for l in labels],
                values=[verdict_counts[l] for l in labels],
                hole=0.62,
                marker=dict(colors=[colors[l] for l in labels], line=dict(color="#08080c", width=2)),
                textfont=dict(size=11.5, color="#f4f4f7"),
                sort=False,
            )
        ]
    )
    total_claims = sum(verdict_counts.values())
    fig.update_layout(
        **PLOTLY_DARK_LAYOUT,
        height=320,
        showlegend=True,
        annotations=[
            dict(
                text=f"<b>{total_claims}</b><br><span style='font-size:10.5px'>claims</span>",
                x=0.5, y=0.5, showarrow=False,
                font=dict(size=20, color="#f4f4f7", family="Manrope"),
            )
        ],
    )
    return fig


# --------------------------------------------------------------------------
# Pages
# --------------------------------------------------------------------------

def page_home(df: pd.DataFrame, summary: pd.DataFrame, corpus_stats) -> None:
    winner = pick_winner(summary)

    st.markdown(
        f"""
        <div class="hero fade-in">
          <div class="hero-eyebrow">Retrieval Evaluation &middot; Live Report</div>
          <h1>Is your retrieval <span class="gradient-text">actually good</span>?</h1>
          <div class="hero-desc">
            A side-by-side evaluation of BM25, dense embeddings, and hybrid RRF fusion
            retrieval on the Northwind Cloud synthetic corpus — scored on ground-truth
            retrieval metrics and LLM-judged faithfulness, hallucination, and answer relevance.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_animated_stats(
        [
            ("Documents", corpus_stats.doc_count, ""),
            ("Questions", corpus_stats.question_count, ""),
            ("Trap Qs", corpus_stats.trap_count, ""),
            ("Strategies", len(summary.index), ""),
            ("Best NDCG@5", round(float(summary["ndcg_at_5"].max()), 2) if not summary.empty else 0, ""),
        ]
    )

    st.write("")
    # All three wrapped in st.container(key="cta_primary_...") for the same
    # gradient treatment — a <div> opened in one st.markdown() call and closed
    # in another, with an st.button() call in between, never actually wraps
    # that button (each st.markdown() is its own isolated DOM fragment in
    # Streamlit), so st.container(key=...) is required whenever custom
    # styling needs to span multiple Streamlit calls like this.
    col_a, col_b, col_c = st.columns(3)
    with col_a:
        with st.container(key="cta_primary_analytics", border=False):
            if st.button("→ Explore Analytics", width='stretch'):
                st.session_state["nav_override"] = "Analytics"
                st.rerun()
    with col_b:
        with st.container(key="cta_primary_query", border=False):
            if st.button("→ Try a Live Query", width='stretch'):
                st.session_state["nav_override"] = "Query Explorer"
                st.rerun()
    with col_c:
        with st.container(key="cta_primary_explorer", border=False):
            if st.button("→ Browse Raw Results", width='stretch'):
                st.session_state["nav_override"] = "Data Explorer"
                st.rerun()

    st.markdown("<div style='height:36px'></div>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">Strategy scorecard</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Ground-truth retrieval metrics + LLM-judged faithfulness, '
        'ranked by NDCG@5 then faithfulness.</div>',
        unsafe_allow_html=True,
    )
    st.write("")

    cols = st.columns(len(summary.index)) if len(summary.index) else [st]
    for col, strategy in zip(cols, summary.index):
        d = summary.loc[strategy]
        is_winner = strategy == winner
        pill_text = "TOP PICK" if is_winner else STRATEGY_LABELS.get(strategy, strategy).upper()
        pill_class = "pill-accent" if is_winner else "pill-good"
        with col:
            st.markdown(
                render_kpi_card(
                    label=STRATEGY_LABELS.get(strategy, strategy),
                    value=f"{d['ndcg_at_5']:.2f}",
                    sub=f"NDCG@5 &nbsp;·&nbsp; Faithfulness {d['faithfulness_score']:.2f} "
                        f"&nbsp;·&nbsp; Relevance {d['answer_relevance_score']:.1f}/5",
                    pill_text=pill_text,
                    pill_class=pill_class,
                ),
                unsafe_allow_html=True,
            )

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    chart_col, side_col = st.columns([1.4, 1])
    with chart_col:
        with st.container(key="glass_home_retrieval_chart", border=False):
            st.markdown('<div class="section-title" style="font-size:15px;">Retrieval metrics by strategy</div>', unsafe_allow_html=True)
            st.plotly_chart(strategy_bar_chart(summary), width='stretch', config={"displayModeBar": False})
    with side_col:
        with st.container(key="glass_home_verdicts_chart", border=False):
            st.markdown('<div class="section-title" style="font-size:15px;">Claim verdicts (all strategies)</div>', unsafe_allow_html=True)
            st.plotly_chart(claim_verdict_pie(df), width='stretch', config={"displayModeBar": False})

    st.markdown("<div style='height:32px'></div>", unsafe_allow_html=True)
    with st.container(key="glass_home_progress", border=False):
        render_progress_bars(summary, "trap_abstention_rate", "Trap-question abstention rate")


def render_footer(active_run_dir: Path) -> None:
    st.markdown(
        f"""
        <div class="app-footer">
          <span>RAG Retrieval Quality Evaluator &middot; reading <code>{active_run_dir.name}/results.json</code></span>
          <span>streamlit run app.py</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main() -> None:
    configure_page()

    run_dirs = list_runs()
    if not run_dirs:
        st.error(
            "No evaluation runs found under `../reports/`. Run `rag-eval run` from the "
            "project root first, then reload this dashboard."
        )
        st.stop()
    active_run_dir = run_dirs[0]

    nav_choice, active_run_dir = render_sidebar(run_dirs, active_run_dir)

    df, summary, _raw = load_active_run(str(active_run_dir))
    corpus_stats = load_corpus_stats()

    if nav_choice == "Home":
        page_home(df, summary, corpus_stats)
    elif nav_choice == "Analytics":
        analytics.render(df)
    elif nav_choice == "Query Explorer":
        query_explorer.render()
    elif nav_choice == "Data Explorer":
        data_explorer.render(df)
    elif nav_choice == "Insights":
        insights.render(df, summary, corpus_stats)
    elif nav_choice == "About":
        about.render(corpus_stats, df)

    render_footer(active_run_dir)


if __name__ == "__main__":
    main()
