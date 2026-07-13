"""About: project objectives, workflow, tech stack, and how to reproduce this run.

No GitHub button here — this isn't a git repository, and a dead/fake link is
worse than no link. "Reproduce this run" (the actual CLI commands) serves the
same purpose honestly. Author is a clearly-marked placeholder, not a
fabricated name.
"""

from __future__ import annotations

import streamlit as st

from utils.data_loader import PROJECT_ROOT

WORKFLOW_STEPS = [
    ("🔎", "Retrieve", "BM25 / dense / hybrid RRF fetch the top-k chunks for each question"),
    ("✍️", "Generate", "An LLM answers the question grounded only in the retrieved context"),
    ("⚖️", "Judge", "A second LLM pass extracts claims and checks each against that context"),
    ("📊", "Score", "Ground-truth retrieval metrics + LLM-judged faithfulness & relevance"),
    ("📄", "Report", "Markdown report, charts, and this dashboard — all from one results.json"),
]

TECH_GROUPS = [
    ("Retrieval", ["Python 3.11+", "rank-bm25", "sentence-transformers", "all-MiniLM-L6-v2", "NumPy"]),
    ("Generation & Judging", ["Ollama (local)", "qwen2.5:3b", "Anthropic API (optional)", "claude-sonnet-5"]),
    ("Evaluation Core", ["pandas", "Typer CLI", "pytest"]),
    ("Dashboard", ["Streamlit", "streamlit-option-menu", "Plotly", "custom CSS (glassmorphism)"]),
]


_EXCLUDED_DIRS = {".venv", "__pycache__", ".git", "node_modules"}


def _iter_py_files(root):
    """os.walk with excluded dirs pruned *before* descending into them.

    rglob("*.py") would still recursively stat every file inside .venv
    (thousands of files from torch/transformers/etc.) before any filter on
    the result gets a chance to exclude them — that's an expensive walk on
    every call. Pruning `dirnames` in place during os.walk skips those
    subtrees entirely.
    """
    import os

    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _EXCLUDED_DIRS]
        for name in filenames:
            if name.endswith(".py"):
                yield os.path.join(dirpath, name)


@st.cache_data(show_spinner=False)
def _count_lines_of_code() -> tuple[int, int]:
    """Non-empty lines across the core library and this dashboard. Computed live, not hardcoded.

    Cached — this is static analysis of source files that don't change
    during a dashboard session, so there's no reason to re-walk the
    filesystem on every rerun (every widget interaction on this page).
    """
    def count(root):
        total = 0
        for path in _iter_py_files(root):
            try:
                with open(path, encoding="utf-8") as f:
                    total += sum(1 for line in f if line.strip())
            except OSError:
                pass
        return total

    return count(PROJECT_ROOT / "src"), count(PROJECT_ROOT / "dashboard")


def render(corpus_stats, df) -> None:
    st.markdown('<div class="section-title">About this project</div>', unsafe_allow_html=True)
    st.write("")

    with st.container(key="glass_about_objectives", border=False):
        st.markdown(
            """
            <div class="section-title" style="font-size:16px;">Objective</div>
            <div style="font-size:14px;color:var(--ink-secondary);line-height:1.75;max-width:82ch;">
              Most teams that ship a RAG system eyeball a handful of queries and call it good. This
              project replaces that with a repeatable evaluation: the same labeled question set, run
              against every retrieval strategy, scored the same way every time &mdash; so
              &ldquo;we switched to hybrid retrieval&rdquo; is a claim backed by numbers, not vibes.
              It answers one question: <b>is retrieval actually good, and which strategy should we use?</b>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    with st.container(key="glass_about_workflow", border=False):
        st.markdown('<div class="section-title" style="font-size:16px;">Workflow</div>', unsafe_allow_html=True)
        st.markdown('<div class="section-sub">Every question, every strategy, the same five steps.</div>', unsafe_allow_html=True)
        st.write("")
        cols = st.columns(len(WORKFLOW_STEPS))
        for i, (col, (icon, title, desc)) in enumerate(zip(cols, WORKFLOW_STEPS)):
            with col:
                arrow = '<div class="workflow-arrow">→</div>' if i < len(WORKFLOW_STEPS) - 1 else ""
                st.markdown(
                    f"""
                    <div class="workflow-step">
                      <div class="workflow-icon">{icon}</div>
                      <div class="workflow-title">{title}</div>
                      <div class="workflow-desc">{desc}</div>
                    </div>
                    {arrow}
                    """,
                    unsafe_allow_html=True,
                )

    st.write("")
    c1, c2 = st.columns([1, 1])
    with c1:
        with st.container(key="glass_about_tech", border=False):
            st.markdown('<div class="section-title" style="font-size:16px;">Technologies</div>', unsafe_allow_html=True)
            st.write("")
            for group, items in TECH_GROUPS:
                badges = "".join(f'<span class="tech-badge">{item}</span>' for item in items)
                st.markdown(
                    f'<div class="tech-group-label">{group}</div><div class="tech-badges">{badges}</div>',
                    unsafe_allow_html=True,
                )

    with c2:
        with st.container(key="glass_about_stats", border=False):
            st.markdown('<div class="section-title" style="font-size:16px;">Project stats</div>', unsafe_allow_html=True)
            st.write("")
            src_loc, dash_loc = _count_lines_of_code()
            stats = [
                ("Corpus documents", corpus_stats.doc_count),
                ("Eval questions", corpus_stats.question_count),
                ("&nbsp;&nbsp;&nbsp;single-chunk", corpus_stats.single_chunk_count),
                ("&nbsp;&nbsp;&nbsp;multi-chunk", corpus_stats.multi_chunk_count),
                ("&nbsp;&nbsp;&nbsp;trap questions", corpus_stats.trap_count),
                ("Evaluated (question, strategy) pairs", len(df)),
                ("Core library — lines of code", src_loc),
                ("Dashboard — lines of code", dash_loc),
                ("Unit tests (deterministic)", 33),
            ]
            rows = "".join(
                f'<div class="stat-table-row"><span>{label}</span><span class="mono">{value}</span></div>'
                for label, value in stats
            )
            st.markdown(f'<div class="stat-table">{rows}</div>', unsafe_allow_html=True)

    st.write("")
    with st.container(key="glass_about_methodology", border=False):
        st.markdown('<div class="section-title" style="font-size:16px;">Methodology</div>', unsafe_allow_html=True)
        st.markdown(
            """
            <div style="font-size:13.5px;color:var(--ink-secondary);line-height:1.75;">
              <b style="color:var(--ink-primary);">Ground truth</b> &mdash; Precision@k, Recall@k, NDCG@k,
              and MRR are computed against hand-labeled gold-relevant chunk IDs. Objective, reproducible,
              the same every run.<br/><br/>
              <b style="color:var(--ink-primary);">LLM-judged</b> &mdash; Faithfulness decomposes each
              answer into atomic claims and checks each against the retrieved context (one structured-output
              call, not one call per claim). Hallucination rate is the stricter binary version: did the
              answer contain <i>any</i> unsupported claim. Answer relevance is a separate judge call, scored
              independently of faithfulness &mdash; a faithful-but-off-topic answer should score low here.
              Treat every LLM-judged number as a consistent, explainable proxy, not ground truth &mdash;
              see Insights for where the judge itself gets a call wrong.
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.write("")
    c3, c4 = st.columns([1, 1.3])
    with c3:
        with st.container(key="glass_about_author", border=False):
            st.markdown(
                """
                <div class="section-title" style="font-size:16px;">Author</div>
                <div style="font-size:13.5px;color:var(--ink-secondary);margin-top:8px;">
                  <span style="color:var(--ink-muted);">&mdash; add your name here &mdash;</span><br/>
                  Solo project. No GitHub remote is configured for this repository yet; once one exists,
                  swap this card for a real link instead of a placeholder.
                </div>
                """,
                unsafe_allow_html=True,
            )
    with c4:
        with st.container(key="glass_about_reproduce", border=False):
            st.markdown('<div class="section-title" style="font-size:16px;">Reproduce this run</div>', unsafe_allow_html=True)
            st.code(
                "cd \"RAG retrieval quality evaluator\"\n"
                "uv pip install -e .\n"
                "rag-eval run --backend local --strategies bm25,dense,hybrid\n\n"
                "cd dashboard\n"
                "pip install -r requirements.txt\n"
                "streamlit run app.py",
                language="bash",
            )
