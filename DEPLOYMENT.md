# Deploying to Render

This repo has no git history and no GitHub remote yet — Render deploys from a
git repo, so that has to exist first. Everything below is written for a
from-scratch deploy; adjust if you already have a remote.

## 0. What you're deploying

Two independent services, defined in [`render.yaml`](render.yaml):

- **`rag-eval-backend`** — FastAPI, built from [`backend/Dockerfile`](backend/Dockerfile)
  (build context is the *repo root*, not `backend/`, since it needs the
  sibling `rag_eval` package plus `data/` and `reports/`). Serves the
  read-only results/summary endpoints plus live `/api/retrieve` and
  `/api/generate`.
- **`rag-eval-frontend`** — the React/Vite app, deployed as a Render Static
  Site (no Dockerfile needed — `frontend/Dockerfile` exists only if you later
  want to self-host this on a non-Render Docker platform).

## 1. Push to GitHub

```bash
git init
git add .
git commit -m "Initial commit"
gh repo create <your-repo-name> --private --source=. --push
# or: create the repo on github.com, then
#   git remote add origin <url> && git push -u origin main
```

## 2. Get a Groq API key (free)

The backend defaults `RAG_EVAL_BACKEND=groq` in production (local Ollama
isn't reachable from Render, and Groq's free tier avoids per-request
Anthropic API cost on a public endpoint). Get a free key at
[console.groq.com/keys](https://console.groq.com/keys) — no card required
for the free tier. Set it as `GROQ_API_KEY` when Render's blueprint prompts
for it in step 3.

Groq's free tier has its own rate limits that can change over time — check
current numbers at [console.groq.com/docs](https://console.groq.com/docs)
after signing up. This app's own `GENERATE_RATE_LIMIT` (default `5/hour` per
visitor) is deliberately conservative and should stay well under them, but
if you see 429s from Groq itself in the backend logs, either lower
`GENERATE_RATE_LIMIT` further or switch `RAG_EVAL_MODEL` to a smaller/faster
free-tier model.

If you'd rather pay for Claude's answer quality instead, set
`RAG_EVAL_BACKEND=api` and `ANTHROPIC_API_KEY` on the backend service (get a
key at console.anthropic.com and **set a spend limit before deploying** —
rate limits here bound *frequency*, not a hard dollar cap).

## 3. Deploy the Blueprint

In the Render dashboard: **New → Blueprint**, point it at your GitHub repo.
Render will read `render.yaml` and propose both services. Before confirming:

- It will prompt for `GROQ_API_KEY` (marked `sync: false` in the blueprint
  so it's never committed) — paste your free key.
- Both services default to placeholder URLs
  (`rag-eval-backend.onrender.com` / `rag-eval-frontend.onrender.com`) in
  `render.yaml`'s `ALLOWED_ORIGINS` and `VITE_API_BASE_URL`. Render service
  names are globally unique, so if those are taken, Render will assign
  different subdomains — **note the actual URLs it gives you**.

## 4. Fix up the cross-service URLs (one-time, after first deploy)

Because the frontend is a static site, `VITE_API_BASE_URL` is baked in at
**build time**, and the backend's CORS allowlist needs the frontend's real
URL. Blueprint deploys create both services from placeholder values, so
after the first deploy:

1. Copy the actual backend URL (e.g. `https://rag-eval-backend-xyz9.onrender.com`).
2. On `rag-eval-frontend` → Environment: set `VITE_API_BASE_URL` to that URL,
   then trigger a manual redeploy (static sites don't rebuild automatically
   on env var changes).
3. Copy the actual frontend URL (e.g. `https://rag-eval-frontend-abc1.onrender.com`).
4. On `rag-eval-backend` → Environment: set `ALLOWED_ORIGINS` to that URL,
   then redeploy (this one restarts automatically on env var change).

## 5. Verify

- `https://<backend-url>/api/health` → `{"status":"ok"}`
- `https://<backend-url>/api/summary` → real evaluation numbers
- Open the frontend URL, check the Overview page loads charts, and try a
  question in Query Explorer (retrieval should be near-instant; generation
  takes several seconds — it's a real Claude API call).

## Cost and abuse notes

- `/api/generate` (retrieval + LLM answer + LLM-judge — **3 API calls per
  request**) is rate-limited via `GENERATE_RATE_LIMIT` (default `5/hour`,
  per client IP, in-memory — resets on backend restart/redeploy).
- `/api/retrieve` is CPU-only (no LLM call) and rate-limited much looser
  (`RETRIEVE_RATE_LIMIT`, default `60/hour`).
- Both limits are env vars on the backend service — tighten them in the
  Render dashboard if traffic looks abusive, no redeploy needed beyond the
  automatic restart on env var change.
- The in-memory rate limiter resets whenever the backend restarts (deploys,
  crashes, Render's free-tier idle-spindown). For a low-stakes public demo
  this is an acceptable tradeoff; if it becomes a problem, slowapi supports a
  Redis backend as a drop-in swap.

## Local development (unchanged)

```bash
# backend
cd backend && .venv/bin/uvicorn app.main:app --reload --port 8000
# frontend, in another terminal
cd frontend && npm run dev
```

Create `frontend/.env.local` with `VITE_API_BASE_URL=http://localhost:8000`
to point the dev server at your local backend (defaults to
`http://localhost:8000` if unset).
