FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/backend/src \
    API_PORT=8000

WORKDIR /app/backend

RUN addgroup --system chiron && \
    adduser --system --ingroup chiron chiron

COPY backend/requirements.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=chiron:chiron backend ./

USER chiron

FROM base AS api
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os, urllib.request; urllib.request.urlopen(f'http://127.0.0.1:{os.getenv(\"API_PORT\", \"8000\")}/healthz', timeout=3)"
CMD ["sh", "-c", "exec python -m uvicorn --app-dir src chiron_backend.api.main:app --host 0.0.0.0 --port ${API_PORT:-8000}"]

FROM base AS worker
CMD ["python", "-m", "chiron_backend.agents.worker"]

