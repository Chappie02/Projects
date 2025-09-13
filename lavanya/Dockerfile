# Multi-stage Dockerfile for Real-Time Speaker Isolation & Identification System

# Stage 1: Base image with system dependencies
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    wget \
    curl \
    portaudio19-dev \
    libasound2-dev \
    libsndfile1-dev \
    ffmpeg \
    sox \
    && rm -rf /var/lib/apt/lists/*

# Create application directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Development image
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    pytest \
    pytest-asyncio \
    pytest-cov \
    black \
    flake8 \
    mypy

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p data/speaker_embeddings data/audio_cache data/transcripts pretrained_models

# Set permissions
RUN chmod +x run_demo.py

# Expose ports
EXPOSE 8000 8001

# Default command for development
CMD ["python", "run_demo.py", "--info"]

# Stage 3: Production image
FROM base as production

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy source code
COPY . .

# Create necessary directories
RUN mkdir -p data/speaker_embeddings data/audio_cache data/transcripts pretrained_models && \
    chown -R appuser:appuser /app

# Set permissions
RUN chmod +x run_demo.py

# Switch to non-root user
USER appuser

# Expose ports
EXPOSE 8000 8001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Default command for production (web server)
CMD ["python", "run_demo.py", "--server", "--host", "0.0.0.0", "--port", "8000"]
