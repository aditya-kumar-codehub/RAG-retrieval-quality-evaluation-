# Build context is the PROJECT ROOT (not backend/) — see render.yaml's
# dockerContext. This lets us install the sibling rag_eval package and ship
# the corpus/reports data the read-only endpoints serve.
FROM python:3.12-slim

WORKDIR /app

# rag_eval package (hatchling needs pyproject.toml + README.md + src/rag_eval)
COPY pyproject.toml README.md ./
COPY src ./src

# Data the API serves: corpus for live retrieval, eval set for corpus-stats,
# reports/ for the read-only results/summary endpoints.
COPY data ./data
COPY reports ./reports

COPY backend/requirements.txt ./backend/requirements.txt

# pip resolves a relative local-path requirement (the "../" line in
# requirements.txt) against the CWD at invocation time, NOT against the
# requirements file's own location — so this must run from /app/backend for
# "../" to land on /app (the rag_eval project root), not "/".
WORKDIR /app/backend
RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

ENV PYTHONUNBUFFERED=1

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
