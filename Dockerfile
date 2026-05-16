FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (tzdata for ZoneInfo in slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata git \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies first (cached layer — only re-runs if pyproject.toml changes)
COPY backend/pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -e ".[all]" 2>/dev/null || pip install --no-cache-dir -e .

# Copy source AFTER deps — invalidates cache on every source change
# Using editable install (-e) so Python imports directly from /app/app,
# NOT from a stale site-packages copy.
COPY backend/app /app/app

# Inject build-time commit hash for /version endpoint
ARG GIT_COMMIT=unknown
ARG BUILD_TIME=unknown
ENV GIT_COMMIT=${GIT_COMMIT} \
    BUILD_TIME=${BUILD_TIME}

COPY qa /app/qa
RUN chmod +x /app/qa/run_autonomous_qa.sh

# Ensure state dir exists as fallback if disk not mounted
RUN mkdir -p /data /app/.state

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
