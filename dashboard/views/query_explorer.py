"""Query Explorer: run the real BM25 / dense / hybrid retrievers live against the corpus.

Retrieval indexing happens once per session (`st.cache_resource`) — repeat
queries reuse the cached index rather than re-embedding the corpus each time.
Retrieval itself needs no external service. Answer generation + LLM-judge
faithfulness is optional (single-strategy only, since it's slow) and needs a
reachable backend — a local Ollama server, or ANTHROPIC_API_KEY for the API
backend — surfaced as a clear error if unreachable, not a crash.
"""

from __future__ import annotations

import html
import time

import streamlit as st

from rag_eval.corpus import build_chunks
from rag_eval.generation import generate_answer
from rag_eval.judge import judge_answer_relevance, judge_faithfulness
from rag_eval.llm import DEFAULT_ANTHROPIC_MODEL, DEFAULT_OLLAMA_MODEL, build_backend
from rag_eval.retrievers.bm25 import BM25Retriever
from rag_eval.retrievers.dense import DenseRetriever
from rag_eval.retrievers.hybrid import HybridRetriever

from utils.data_loader import CORPUS_DIR

STRATEGY_COLORS = {"bm25": "#5b8cff", "dense": "#2dd4bf", "hybrid": "#a78bfa"}
STRATEGY_LABELS = {"bm25": "BM25", "dense": "Dense", "hybrid": "Hybrid (RRF)"}
STRATEGY_ORDER = ["bm25", "dense", "hybrid"]

EXAMPLE_QUESTIONS = [
    "What is Northwind Cloud's PTO accrual rate?",
    "If I'm on the Pro tier and hit the rate limit, what should I do?",
    "What is Northwind Cloud's policy on bringing pets to the office?",
    "How does the disaster recovery plan define RTO and RPO?",
]


def _esc(s: object) -> str:
    return html.escape(str(s))


@st.cache_resource(show_spinner="Indexing corpus (first run downloads the embedding model)…")
def get_indexed_retrievers():
    chunks = build_chunks(str(CORPUS_DIR))
    bm25 = BM25Retriever()
    dense = DenseRetriever()
    hybrid = HybridRetriever([bm25, dense])
    hybrid.index(chunks)  # also indexes bm25 and dense — they're shared instances
    return {"bm25": bm25, "dense": dense, "hybrid": hybrid}


def render_result_card(rank: int, chunk_id: str, score: float, text: str, color: str) -> str:
    snippet = text[:220] + ("…" if len(text) > 220 else "")
    return f"""
    <div class="result-card">
      <div class="result-card-head">
        <span class="result-rank" style="background:{color}">#{rank}</span>
        <span class="chunk-pill" style="margin:0;">{_esc(chunk_id)}</span>
        <span class="result-score mono">score {score:.3f}</span>
      </div>
      <div class="result-snippet">{_esc(snippet)}</div>
    </div>
    """


def render() -> None:
    retrievers = get_indexed_retrievers()

    st.markdown('<div class="section-title">Query Explorer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-sub">Type any question and watch the real BM25, dense, and '
        "hybrid retrievers run live against the 40-document corpus &mdash; not a replay of "
        "saved results.</div>",
        unsafe_allow_html=True,
    )
    st.write("")

    st.session_state.setdefault("qe_question", "")

    chip_cols = st.columns(len(EXAMPLE_QUESTIONS))
    for col, q in zip(chip_cols, EXAMPLE_QUESTIONS):
        with col:
            if st.button(q if len(q) < 42 else q[:39] + "…", key=f"example_{q}", width="stretch"):
                st.session_state["qe_question"] = q

    with st.container(key="glass_qe_form", border=False):
        question = st.text_area(
            "Question", key="qe_question", height=80,
            placeholder="Ask anything about Northwind Cloud's product, HR, or engineering docs…",
            label_visibility="collapsed",
        )

        f1, f2, f3 = st.columns([1.4, 1, 1])
        with f1:
            mode = st.selectbox(
                "Strategy", ["Compare all", "BM25", "Dense", "Hybrid (RRF)"],
            )
        with f2:
            k = st.slider("Top k", min_value=1, max_value=10, value=5)
        with f3:
            generate = st.toggle(
                "Generate answer", value=False,
                disabled=(mode == "Compare all"),
                help="Also call the LLM backend to generate and faithfulness-judge an answer. "
                     "Single strategy only — this makes 3 backend calls and can take 15-30s locally.",
            )

        if generate:
            g1, g2 = st.columns(2)
            with g1:
                backend_choice = st.selectbox("Backend", ["local", "api"], help="local = Ollama, api = Anthropic")
            with g2:
                default_model = DEFAULT_OLLAMA_MODEL if backend_choice == "local" else DEFAULT_ANTHROPIC_MODEL
                model_name = st.text_input("Model", value=default_model)
        else:
            backend_choice, model_name = "local", DEFAULT_OLLAMA_MODEL

        with st.container(key="cta_primary_run_retrieval", border=False):
            run_clicked = st.button("▶ Run Retrieval", width="stretch")

    if not run_clicked:
        return
    if not question.strip():
        st.warning("Type a question first.")
        return

    strategies = STRATEGY_ORDER if mode == "Compare all" else [
        {"BM25": "bm25", "Dense": "dense", "Hybrid (RRF)": "hybrid"}[mode]
    ]

    st.write("")
    t0 = time.perf_counter()
    retrieval_results = {}
    for s in strategies:
        retrieval_results[s] = retrievers[s].retrieve(question, k=k)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    st.markdown(
        f'<div style="font-size:12px;color:var(--ink-muted);font-family:var(--font-mono);margin-bottom:14px;">'
        f"retrieved in {elapsed_ms:.0f}ms &middot; k={k} &middot; {len(strategies)} "
        f"strateg{'y' if len(strategies)==1 else 'ies'}</div>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(strategies))
    for col, s in zip(cols, strategies):
        with col:
            with st.container(key=f"glass_qe_results_{s}", border=False):
                st.markdown(
                    f'<div class="section-title" style="font-size:14px;">'
                    f'<span class="swatch" style="background:{STRATEGY_COLORS[s]};display:inline-block;'
                    f'width:9px;height:9px;border-radius:3px;margin-right:7px;"></span>'
                    f"{STRATEGY_LABELS[s]}</div>",
                    unsafe_allow_html=True,
                )
                cards = "".join(
                    render_result_card(r.rank, r.chunk.chunk_id, r.score, r.chunk.text, STRATEGY_COLORS[s])
                    for r in retrieval_results[s]
                )
                st.markdown(cards, unsafe_allow_html=True)

    if not generate:
        return

    strategy = strategies[0]
    chunk_texts = [(r.chunk.chunk_id, r.chunk.text) for r in retrieval_results[strategy]]

    st.write("")
    with st.spinner(f"Generating answer with {model_name} and judging faithfulness… (can take up to ~30s locally)"):
        try:
            backend = build_backend(backend_choice, model_name)
            answer = generate_answer(backend, question, chunk_texts)
            faithfulness = judge_faithfulness(backend, question, answer.text, chunk_texts)
            relevance = judge_answer_relevance(backend, question, answer.text)
        except Exception as exc:  # noqa: BLE001 — surface any backend failure as a friendly message
            st.error(
                f"Couldn't reach the **{backend_choice}** backend: {exc}\n\n"
                + (
                    "Make sure Ollama is running (`ollama serve`) and the model is pulled "
                    f"(`ollama pull {model_name}`)."
                    if backend_choice == "local"
                    else "Make sure `ANTHROPIC_API_KEY` is set in this environment."
                )
            )
            return

    render_generation_result(question, answer.text, faithfulness, relevance, strategy)


def render_generation_result(question: str, answer_text: str, faithfulness, relevance, strategy: str) -> None:
    import plotly.graph_objects as go

    score = faithfulness.faithfulness_score
    gauge_color = "#34d399" if score >= 0.8 else "#fbbf24" if score >= 0.5 else "#f87171"

    g1, g2 = st.columns([1, 2])
    with g1:
        with st.container(key="glass_qe_gauge", border=False):
            st.markdown('<div class="section-title" style="font-size:14px;">Faithfulness</div>', unsafe_allow_html=True)
            fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=score * 100,
                    number=dict(suffix="%", font=dict(size=32, color="#f4f4f7", family="Manrope")),
                    gauge=dict(
                        axis=dict(range=[0, 100], tickcolor="#6c6c7c", tickfont=dict(size=9, color="#6c6c7c")),
                        bar=dict(color=gauge_color, thickness=0.28),
                        bgcolor="rgba(0,0,0,0)",
                        borderwidth=0,
                        steps=[
                            dict(range=[0, 50], color="rgba(248,113,113,0.12)"),
                            dict(range=[50, 80], color="rgba(251,191,36,0.12)"),
                            dict(range=[80, 100], color="rgba(52,211,153,0.12)"),
                        ],
                    ),
                )
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=20, r=20, t=10, b=10), height=200,
                font=dict(family="Plus Jakarta Sans, sans-serif", color="#a4a4b3"),
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.markdown(
                f'<div style="text-align:center;font-family:var(--font-mono);font-size:12px;'
                f'color:var(--ink-muted);margin-top:-8px;">relevance {relevance.score}/5</div>',
                unsafe_allow_html=True,
            )

    with g2:
        claims_html = "".join(
            f'<div class="claim-row v-{c.verdict}">'
            f'<span class="claim-icon">{"✓" if c.verdict == "supported" else "✕" if c.verdict == "unsupported" else "±"}</span>'
            f'<span>{_esc(c.text)}</span></div>'
            for c in faithfulness.claims
        ) or '<div style="color:var(--ink-muted);font-size:13px;">No claims extracted (a good sign for an "I don\'t know" answer).</div>'

        st.markdown(
            f"""
            <div class="glass-card fade-in">
              <div class="field-label">Generated answer &middot; {STRATEGY_LABELS[strategy]}</div>
              <div class="answer-box">{_esc(answer_text)}</div>
              <div class="field-label">Claims</div>
              {claims_html}
              <div class="field-label">Relevance judgment</div>
              <div style="font-size:13px;color:var(--ink-secondary);">{_esc(relevance.explanation)}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
