# Backend Dockerfile for DeckDex MTG API
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (build context is repo root)
COPY backend/requirements-api.txt .
COPY requirements.txt ./requirements-core.txt

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements-core.txt
RUN pip install --no-cache-dir -r requirements-api.txt

# Copy application code
COPY backend /app/backend
COPY deckdex /app/deckdex
COPY scripts /app/scripts
COPY migrations /app/migrations
COPY config.yaml /app/config.yaml

# Create logs directory
RUN mkdir -p /app/logs

# Expose port
EXPOSE 8000

# Entrypoint: run migrations (when DATABASE_URL is set) then start the API
COPY backend/docker-entrypoint.sh /app/docker-entrypoint.sh
RUN chmod +x /app/docker-entrypoint.sh
ENTRYPOINT ["/app/docker-entrypoint.sh"]
CMD ["uvicorn", "backend.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
