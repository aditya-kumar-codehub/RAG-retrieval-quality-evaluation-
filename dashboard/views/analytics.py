"""Analytics: deeper cross-cutting views over the real per-question results.

Line trends, faithfulness-by-difficulty bars, a per-question x strategy
faithfulness heatmap, and score distributions — all computed live from the
loaded results DataFrame, filterable by strategy.
"""

from __future__ import annotations

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

STRATEGY_COLORS = {"bm25": "#5b8cff", "dense": "#2dd4bf", "hybrid": "#a78bfa"}
STRATEGY_LABELS = {"bm25": "BM25", "dense": "Dense", "hybrid": "Hybrid (RRF)"}
STRATEGY_ORDER = ["bm25", "dense", "hybrid"]

PLOTLY_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Plus Jakarta Sans, sans-serif", color="#a4a4b3", size=12),
    margin=dict(l=10, r=10, t=10, b=10),
)
GRID_COLOR = "rgba(255,255,255,0.07)"
LEGEND = dict(orientation="h", y=1.18, x=0, font=dict(size=11), bgcolor="rgba(0,0,0,0)")


def _card_header(title: str, sub: str) -> None:
    st.markdown(f'<div class="section-title" style="font-size:15px;">{title}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="section-sub">{sub}</div>', unsafe_allow_html=True)


def _line_ndcg_vs_k(df: pd.DataFrame, strategies: list[str]) -> go.Figure:
    ks = [3, 5, 10]
    fig = go.Figure()
    for s in strategies:
        sub = df[df["strategy"] == s]
        y = [sub[f"ndcg_at_{k}"].mean() for k in ks]
        fig.add_trace(
            go.Scatter(
                x=ks, y=y, mode="lines+markers", name=STRATEGY_LABELS[s],
                line=dict(color=STRATEGY_COLORS[s], width=2.5, shape="spline"),
                marker=dict(size=8, line=dict(width=2, color="#08080c")),
                hovertemplate="k=%{x}<br>NDCG=%{y:.3f}<extra>" + STRATEGY_LABELS[s] + "</extra>",
            )
        )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=300, legend=LEGEND, hovermode="x unified",
        xaxis=dict(title="k", tickvals=ks, gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(title="Mean NDCG@k", range=[0, 1.05], gridcolor=GRID_COLOR),
    )
    return fig


def _bar_by_difficulty(df: pd.DataFrame, strategies: list[str]) -> go.Figure:
    present = [d for d in ["easy", "medium", "trap"] if d in df["difficulty"].unique()]
    fig = go.Figure()
    for s in strategies:
        sub = df[df["strategy"] == s]
        y = [sub[sub["difficulty"] == d]["faithfulness_score"].mean() for d in present]
        fig.add_trace(
            go.Bar(
                name=STRATEGY_LABELS[s], x=[d.capitalize() for d in present], y=y,
                marker_color=STRATEGY_COLORS[s], marker_line_width=0,
                hovertemplate="%{x}<br>Faithfulness=%{y:.2f}<extra>" + STRATEGY_LABELS[s] + "</extra>",
            )
        )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=300, barmode="group", bargap=0.32, bargroupgap=0.14, legend=LEGEND,
        yaxis=dict(title="Mean faithfulness", range=[0, 1.05], gridcolor=GRID_COLOR),
        xaxis=dict(gridcolor="rgba(0,0,0,0)"),
    )
    return fig


def _heatmap_faithfulness(df: pd.DataFrame, strategies: list[str]) -> go.Figure:
    pivot = df.pivot_table(index="question_id", columns="strategy", values="faithfulness_score")
    cols = [s for s in strategies if s in pivot.columns]
    pivot = pivot[cols].sort_index()
    fig = go.Figure(
        data=go.Heatmap(
            z=pivot.values,
            x=[STRATEGY_LABELS[s] for s in cols],
            y=list(pivot.index),
            colorscale=[[0, "#f87171"], [0.5, "#fbbf24"], [1, "#34d399"]],
            zmin=0, zmax=1,
            colorbar=dict(tickfont=dict(size=10, color="#a4a4b3"), thickness=12, outlinewidth=0),
            hovertemplate="%{y} · %{x}<br>Faithfulness: %{z:.2f}<extra></extra>",
            xgap=3, ygap=3,
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=min(700, 34 * len(pivot) + 60),
        yaxis=dict(autorange="reversed", tickfont=dict(size=10.5, family="JetBrains Mono, monospace")),
        xaxis=dict(side="top", tickfont=dict(size=11.5)),
    )
    return fig


def _distribution_hist(df: pd.DataFrame) -> go.Figure:
    fig = go.Figure(
        data=go.Histogram(
            x=df["context_utilization"], nbinsx=20,
            marker_color="#5b8cff", marker_line_width=0, opacity=0.85,
            hovertemplate="%{x:.2f}<br>Count: %{y}<extra></extra>",
        )
    )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=300, bargap=0.08,
        xaxis=dict(title="Context utilization", gridcolor="rgba(0,0,0,0)"),
        yaxis=dict(title="Count", gridcolor=GRID_COLOR),
    )
    return fig


def _pie_relevance(df: pd.DataFrame) -> go.Figure:
    counts = df["answer_relevance_score"].value_counts().sort_index()
    palette = {1: "#f87171", 2: "#fb923c", 3: "#fbbf24", 4: "#a3e635", 5: "#34d399"}
    fig = go.Figure(
        data=[
            go.Pie(
                labels=[f"{i}/5" for i in counts.index],
                values=counts.values,
                hole=0.58,
                marker=dict(colors=[palette[i] for i in counts.index], line=dict(color="#08080c", width=2)),
                textfont=dict(size=11, color="#f4f4f7"),
                sort=False,
            )
        ]
    )
    fig.update_layout(
        **PLOTLY_LAYOUT, height=300, showlegend=True,
        legend=dict(orientation="h", y=-0.08, font=dict(size=10.5), bgcolor="rgba(0,0,0,0)"),
    )
    return fig


def render(df: pd.DataFrame) -> None:
    st.markdown('<div class="section-title">Analytics</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Deeper cross-cutting views over the full result set &mdash; '
        "retrieval trends, quality by question difficulty, and exactly where each strategy struggles.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    strategies = st.multiselect(
        "Strategies", options=STRATEGY_ORDER, default=STRATEGY_ORDER,
        format_func=lambda s: STRATEGY_LABELS[s], label_visibility="collapsed",
    )
    if not strategies:
        st.info("Select at least one strategy to see charts.")
        return
    sdf = df[df["strategy"].isin(strategies)]

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        with st.container(key="glass_an_ndcg_line", border=False):
            _card_header("Retrieval quality vs. k", "Mean NDCG at k = 3, 5, 10")
            st.plotly_chart(_line_ndcg_vs_k(sdf, strategies), width="stretch", config={"displayModeBar": False})
    with c2:
        with st.container(key="glass_an_difficulty_bar", border=False):
            _card_header("Faithfulness by difficulty", "Mean faithfulness score per question difficulty tier")
            st.plotly_chart(_bar_by_difficulty(sdf, strategies), width="stretch", config={"displayModeBar": False})

    st.write("")
    with st.container(key="glass_an_heatmap", border=False):
        _card_header(
            "Faithfulness heatmap &mdash; question &times; strategy",
            "Red = low faithfulness, green = high. Spot exactly which questions each strategy struggles with.",
        )
        st.plotly_chart(_heatmap_faithfulness(sdf, strategies), width="stretch", config={"displayModeBar": False})

    st.write("")
    c3, c4 = st.columns(2)
    with c3:
        with st.container(key="glass_an_context_hist", border=False):
            _card_header(
                "Context utilization distribution",
                "Fraction of retrieved chunks the judge cited as supporting a claim",
            )
            st.plotly_chart(_distribution_hist(sdf), width="stretch", config={"displayModeBar": False})
    with c4:
        with st.container(key="glass_an_relevance_pie", border=False):
            _card_header("Answer relevance distribution", "LLM-judged 1&ndash;5 relevance score across evaluated answers")
            st.plotly_chart(_pie_relevance(sdf), width="stretch", config={"displayModeBar": False})
