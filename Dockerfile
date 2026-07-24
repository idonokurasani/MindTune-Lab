# MindTune MPE Phase 4B.1 — development and test environment
# Build from repository root: docker build -t mpe:phase4b1 .

FROM python:3.11-slim

# Prevent Python from writing pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install build dependencies and a non-root user
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libc6-dev \
    && rm -rf /var/lib/apt/lists/* \
    && useradd -m -u 1000 mpe \
    && mkdir -p /tmp/ruff_cache /tmp/mypy_cache \
    && chown -R mpe:mpe /tmp/ruff_cache /tmp/mypy_cache

ENV RUFF_CACHE_DIR=/tmp/ruff_cache \
    MYPY_CACHE_DIR=/tmp/mypy_cache

# Copy dependency lock and install deterministically
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy package source and install in editable mode for development/tests
COPY packages/mpe /app/packages/mpe
RUN pip install --no-cache-dir -e ./packages/mpe

# Switch to non-root user for runtime
RUN mkdir -p /data/mpe && chown -R mpe:mpe /data

USER mpe

# Default command demonstrates the deterministic mock session
CMD ["python", "-m", "mpe.demo"]
