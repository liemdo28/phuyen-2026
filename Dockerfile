FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (tzdata for ZoneInfo in slim image)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml /app/pyproject.toml
COPY backend/app /app/app

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY qa /app/qa

RUN chmod +x /app/qa/run_autonomous_qa.sh

# Ensure state dir exists as fallback if disk not mounted
RUN mkdir -p /data /app/.state

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
