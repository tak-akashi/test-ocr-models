# Multi-stage Dockerfile for Python document processing project
# Supports both CPU and GPU configurations for Windows/WSL2 and Linux

ARG CUDA_VERSION=12.1.1
ARG UBUNTU_VERSION=22.04

# Base stage with system dependencies
FROM ubuntu:${UBUNTU_VERSION} AS base

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    # Python and build essentials
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    build-essential \
    pkg-config \
    curl \
    git \
    # PDF processing dependencies
    poppler-utils \
    libmupdf-dev \
    # Image processing dependencies
    libopencv-dev \
    python3-opencv \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    # Other dependencies
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Create python symlink for python3.12
RUN ln -sf /usr/bin/python3.12 /usr/bin/python

# Install uv package manager (system-wide for all users)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx 2>/dev/null || true \
    && chmod +x /usr/local/bin/uv

# GPU-enabled base (optional)
FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu${UBUNTU_VERSION} AS base-gpu

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Install system dependencies (same as base)
RUN apt-get update && apt-get install -y \
    software-properties-common \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.12 \
    python3.12-dev \
    python3.12-venv \
    python3-pip \
    build-essential \
    pkg-config \
    curl \
    git \
    poppler-utils \
    libmupdf-dev \
    libopencv-dev \
    python3-opencv \
    libjpeg-dev \
    libpng-dev \
    libtiff-dev \
    libwebp-dev \
    libffi-dev \
    libssl-dev \
    libxml2-dev \
    libxslt1-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

RUN ln -sf /usr/bin/python3.12 /usr/bin/python

# Install uv package manager (system-wide for all users)
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv \
    && mv /root/.local/bin/uvx /usr/local/bin/uvx 2>/dev/null || true \
    && chmod +x /usr/local/bin/uv

# Dependencies stage
FROM base AS dependencies
ARG ENABLE_GPU=false

WORKDIR /app

# Copy dependency files (README.md required for package metadata)
COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md ./

# Install Python dependencies and create virtual environment
RUN if [ -f "uv.lock" ]; then \
        uv sync --frozen; \
    else \
        uv sync; \
    fi

# Set virtual environment PATH
ENV PATH="/app/.venv/bin:$PATH"

# Runtime stage
FROM dependencies AS runtime

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
RUN mkdir -p /app /app/data /app/output /app/notebook && \
    chown -R appuser:appuser /app

# Set up Hugging Face cache directory
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p $HF_HOME && chown -R appuser:appuser $HF_HOME

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser notebook/ /app/notebook/
COPY --chown=appuser:appuser CLAUDE.md README.md /app/

# Copy entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser
WORKDIR /app

# Expose Jupyter port
EXPOSE 8888

# Set default entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["bash"]

# GPU runtime stage
FROM base-gpu AS runtime-gpu
ARG ENABLE_GPU=true

WORKDIR /app

# Copy dependency files (README.md required for package metadata)
COPY pyproject.toml ./
COPY uv.lock* ./
COPY README.md ./

# Install Python dependencies with GPU support
RUN if [ -f "uv.lock" ]; then \
        uv sync --frozen; \
    else \
        uv sync; \
    fi

# Set virtual environment PATH
ENV PATH="/app/.venv/bin:$PATH"

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash appuser
RUN mkdir -p /app /app/data /app/output /app/notebook && \
    chown -R appuser:appuser /app

# Set up Hugging Face cache directory
ENV HF_HOME=/app/.cache/huggingface
RUN mkdir -p $HF_HOME && chown -R appuser:appuser $HF_HOME

# Copy application code
COPY --chown=appuser:appuser src/ /app/src/
COPY --chown=appuser:appuser notebook/ /app/notebook/
COPY --chown=appuser:appuser CLAUDE.md README.md /app/

# Copy entrypoint script
COPY --chown=appuser:appuser entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Switch to non-root user
USER appuser
WORKDIR /app

# Expose Jupyter port
EXPOSE 8888

# Set default entrypoint
ENTRYPOINT ["/app/entrypoint.sh"]

# Default command (can be overridden)
CMD ["bash"]