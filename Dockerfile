# Multi-stage production Dockerfile for ALVERIS GeoAI Engine
FROM python:3.12-slim AS base

# Install system geospatial libraries (GDAL, GEOS, PROJ) and build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgdal-dev \
    libgeos-dev \
    libproj-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy dependency manifests
COPY pyproject.toml ./

# Install python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Copy source code, configurations, data, and tests
COPY src/ ./src/
COPY configs/ ./configs/
COPY data/ ./data/
COPY tests/ ./tests/
COPY README.md ./

# Re-install package in editable mode with entrypoints
RUN pip install --no-cache-dir -e .

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck for container orchestration
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Default entrypoint: launch Streamlit Decision Cockpit
CMD ["streamlit", "run", "src/alveris/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
