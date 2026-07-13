"""CLI entrypoint: `rag-eval run` and `rag-eval report`."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Optional

import typer

from rag_eval.llm import DEFAULT_ANTHROPIC_MODEL, DEFAULT_OLLAMA_MODEL
from rag_eval.report import build_report
from rag_eval.runner import load_results, run_evaluation, save_results

app = typer.Typer(help="Evaluate RAG retrieval quality: BM25 vs. dense vs. hybrid.")


@app.command()
def run(
    corpus: str = typer.Option("data/corpus", help="Directory of corpus documents."),
    eval_set: str = typer.Option("data/eval_set.jsonl", help="Path to the eval set JSONL file."),
    strategies: str = typer.Option(
        "bm25,dense,hybrid", help="Comma-separated list of retrieval strategies to compare."
    ),
    k: int = typer.Option(5, help="Number of chunks to retrieve and pass to the generator/judge."),
    backend: str = typer.Option(
        "local",
        help="Where to run generation/judging: 'local' (Ollama) or 'api' (Anthropic API).",
    ),
    generator_model: Optional[str] = typer.Option(
        None,
        help=f"Model used to generate answers. Defaults to '{DEFAULT_OLLAMA_MODEL}' (local) "
        f"or '{DEFAULT_ANTHROPIC_MODEL}' (api).",
    ),
    judge_model: Optional[str] = typer.Option(
        None,
        help=f"Model used for LLM-as-judge scoring. Defaults to '{DEFAULT_OLLAMA_MODEL}' (local) "
        f"or '{DEFAULT_ANTHROPIC_MODEL}' (api).",
    ),
    out: Optional[str] = typer.Option(
        None, help="Output directory for this run. Defaults to reports/run_<timestamp>."
    ),
) -> None:
    """Run the full pipeline (retrieve -> generate -> judge -> score) and produce a report."""
    if backend not in ("local", "api"):
        raise typer.BadParameter("--backend must be 'local' or 'api'")

    strategy_list = [s.strip() for s in strategies.split(",") if s.strip()]
    out_dir = Path(out) if out else Path("reports") / f"run_{datetime.now():%Y%m%d_%H%M%S}"
    out_dir.mkdir(parents=True, exist_ok=True)

    resolved_generator = generator_model or (DEFAULT_OLLAMA_MODEL if backend == "local" else DEFAULT_ANTHROPIC_MODEL)
    resolved_judge = judge_model or (DEFAULT_OLLAMA_MODEL if backend == "local" else DEFAULT_ANTHROPIC_MODEL)

    typer.echo(f"Running evaluation: strategies={strategy_list}, k={k}, backend={backend}")
    typer.echo(f"Generator model: {resolved_generator} | Judge model: {resolved_judge}")

    results = run_evaluation(
        corpus_dir=corpus,
        eval_set_path=eval_set,
        strategy_names=strategy_list,
        k=k,
        backend=backend,
        generator_model=resolved_generator,
        judge_model=resolved_judge,
    )

    results_path = out_dir / "results.json"
    save_results(results, results_path)
    typer.echo(f"Saved raw results to {results_path}")

    report_path = build_report(
        results, out_dir, generator_model=resolved_generator, judge_model=resolved_judge
    )
    typer.echo(f"Report written to {report_path}")


@app.command()
def report(
    run_dir: str = typer.Argument(..., help="Path to a run directory containing results.json."),
) -> None:
    """Regenerate the markdown report + charts from a saved run, with no API calls."""
    run_path = Path(run_dir)
    results_path = run_path / "results.json"
    if not results_path.exists():
        raise typer.BadParameter(f"No results.json found in {run_path}")

    results = load_results(results_path)
    generator_model = results[0].generator_model if results else ""
    judge_model = results[0].judge_model if results else ""
    report_path = build_report(results, run_path, generator_model=generator_model, judge_model=judge_model)
    typer.echo(f"Report written to {report_path}")


if __name__ == "__main__":
    app()
