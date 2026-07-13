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

# Install CPU-only torch FIRST, from PyTorch's own CPU index. The default
# PyPI torch wheel on Linux drags in several NVIDIA CUDA packages
# (nvidia-cublas-cu12, nvidia-cudnn-cu12, etc.) as dependencies even though
# we never touch a GPU — those libraries alone were enough to blow past
# Render free tier's 512MB RAM cap. Once this satisfies sentence-transformers'
# torch requirement, the next install step won't replace it with the GPU
# build.
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/app ./app

ENV PYTHONUNBUFFERED=1
# Cut down on thread-pool memory overhead from torch's CPU intra-op
# parallelism and HF tokenizers' parallel-fork warning/overhead — this is a
# single low-traffic instance, not a batch-inference server.
ENV OMP_NUM_THREADS=1
ENV TOKENIZERS_PARALLELISM=false

EXPOSE 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
