# syntax = docker/dockerfile:1.4
FROM python:3.12-slim AS base

RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /skillsgoat

# Copy the tree first so the editable install can see src/goat.
COPY . .
# Default is .[dev] only — same as ./setup. The compose `scan` service
# passes GOAT_EXTRAS=dev,scanners so skillspector is actually on PATH.
ARG GOAT_EXTRAS=dev
RUN pip install --no-cache-dir -e ".[${GOAT_EXTRAS}]"

RUN useradd -m -u 1000 skillsgoat && chown -R skillsgoat:skillsgoat /skillsgoat
USER skillsgoat

ENTRYPOINT ["goat"]
CMD ["--help"]
