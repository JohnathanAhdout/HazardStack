# Dockerfile for HazardStack data ingestion worker

FROM python:3.10-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    git \
    libgeos-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY pyproject.toml /app/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -e .

# Copy application code
COPY hazard/ /app/hazard/
COPY scripts/ /app/scripts/
COPY configs/ /app/configs/

# Create data directories
RUN mkdir -p /app/data/raw /app/data/interim /app/data/processed

# Run worker (override with specific script)
CMD ["python", "scripts/worker.py"]
