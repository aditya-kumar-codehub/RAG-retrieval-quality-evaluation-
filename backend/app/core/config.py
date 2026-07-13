"""Centralized paths and settings, sourced from the environment where relevant.

Kept deliberately simple — this is a small evaluation-results API, not a
multi-tenant service, so a single module of constants is clearer than a
settings-management framework.
"""

from __future__ import annotations

import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CORPUS_DIR = PROJECT_ROOT / "data" / "corpus"
EVAL_SET_PATH = PROJECT_ROOT / "data" / "eval_set.jsonl"
REPORTS_DIR = PROJECT_ROOT / "reports"

# CORS: comma-separated list of allowed origins, e.g.
# "https://your-app.onrender.com,http://localhost:5173"
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("ALLOWED_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

# Which LLM backend live generation uses. "local" needs an Ollama server
# reachable from this process (impractical on most free/cheap hosting tiers —
# see backend/README.md); "api" needs ANTHROPIC_API_KEY set in the
# environment. Defaults to "api" since that's what a public deployment will
# realistically run.
GENERATION_BACKEND = os.environ.get("RAG_EVAL_BACKEND", "api")
GENERATION_MODEL = os.environ.get("RAG_EVAL_MODEL", "")  # "" = backend's own default

# Rate limits for the (costly) live generation endpoint. Retrieval alone is
# cheap (local CPU only) and gets a looser limit.
GENERATE_RATE_LIMIT = os.environ.get("GENERATE_RATE_LIMIT", "5/hour")
RETRIEVE_RATE_LIMIT = os.environ.get("RETRIEVE_RATE_LIMIT", "60/hour")
