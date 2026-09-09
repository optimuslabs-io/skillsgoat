# syntax = docker/dockerfile:1.4
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /skillsgoat

# Install Python dependencies
COPY pyproject.toml README.md ./
RUN pip install --no-cache-dir -e ".[dev,scanners]"

# Copy source
COPY . .

# Create non-root user
RUN useradd -m -u 1000 skillsgoat && chown -R skillsgoat:skillsgoat /skillsgoat
USER skillsgoat

ENTRYPOINT ["goat"]
CMD ["--help"]
