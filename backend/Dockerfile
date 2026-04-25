FROM python:3.12-slim AS base
WORKDIR /app/backend
ENV PYTHONUNBUFFERED=1
COPY backend/requirements.txt backend/requirements-dev.txt ./
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt
COPY backend ./
ENV PYTHONPATH=/app/backend/src

FROM base AS api
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "--app-dir", "src", "chiron_backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]

FROM base AS worker
CMD ["python", "-m", "chiron_backend.agents.worker"]

