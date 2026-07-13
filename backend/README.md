# Backend

FastAPI wrapper around the `rag_eval` core library — see the [project
README](../README.md) for the methodology this API surfaces. Serves the
React frontend in [`../frontend`](../frontend).

## Endpoints

Read-only (serve a saved evaluation run — no LLM calls):
- `GET /api/health`
- `GET /api/runs`
- `GET /api/results?run=<name>`
- `GET /api/summary?run=<name>`
- `GET /api/corpus-stats`

Live (index the real corpus at startup, run in-process):
- `POST /api/retrieve` — `{question, strategy, k}` → ranked chunks. CPU-only, no LLM call.
- `POST /api/generate` — `{question, strategy, k}` → retrieve + generate + judge. Calls the configured LLM backend 3 times per request (generation, faithfulness judging, relevance judging) — the costly, rate-limited endpoint.

## Local setup

```bash
cd backend
uv pip install --python .venv -r requirements.txt   # or: python -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/uvicorn app.main:app --reload --port 8000
```

`requirements.txt` installs `rag_eval` as a regular (non-editable) package
from `../` — run pip from *inside* `backend/` so that relative path resolves.
Non-editable is deliberate: editable installs on this machine's
Desktop-synced path hit a macOS bug where the `.pth` marker file gets
silently flagged hidden, breaking the import.

## Configuration (env vars)

| Var | Default | Purpose |
|---|---|---|
| `ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated CORS allowlist |
| `RAG_EVAL_BACKEND` | `api` | `local` (Ollama) or `api` (Anthropic) for generation/judging |
| `RAG_EVAL_MODEL` | backend's own default | Override the model name |
| `GENERATE_RATE_LIMIT` | `5/hour` | Per-IP limit on `/api/generate` |
| `RETRIEVE_RATE_LIMIT` | `60/hour` | Per-IP limit on `/api/retrieve` |
| `ANTHROPIC_API_KEY` | — | Required when `RAG_EVAL_BACKEND=api` |

`local` needs an Ollama server reachable from this process — fine for local
dev (`ollama serve`), impractical on most hosting tiers, which is why
production defaults to `api`. See [`../DEPLOYMENT.md`](../DEPLOYMENT.md) for
the Render setup.
