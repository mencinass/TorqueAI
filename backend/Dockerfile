# ==============================================================================
# Automotive AI Agent - Backend Dockerfile
# Python 3.11 Slim with async PostgreSQL and Qdrant client dependencies
# ==============================================================================
FROM python:3.11-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install system runtime dependencies:
# - curl: healthchecks
# - poppler-utils: pdfinfo/pdftotext, used as isolated subprocesses for robust
#   PDF extraction (a stuck/pathological page can be killed outright, unlike
#   an in-process Python library)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt requirements-dev.txt /app/
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . /app/

# Expose FastAPI default port
EXPOSE 8000

# Health check within container
HEALTHCHECK --interval=10s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start FastAPI server without reload so long-running ingestion jobs survive file changes
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

