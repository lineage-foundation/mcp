# syntax=docker/dockerfile:1
# Distroless runtime (mirrors the explorer service's distroless image).
#
# A venv is ABI-locked to its Python minor version, and distroless
# python3-debian12 is CPython 3.11 — so the build stage MUST use python:3.11
# to produce a compatible venv. The project is installed non-editable so all
# code lives in site-packages, which we copy onto PYTHONPATH in the runtime.
FROM python:3.11-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Dependencies first (cached layer), then the project itself, non-editable.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project --no-editable
COPY . .
RUN uv sync --frozen --no-dev --no-editable

FROM gcr.io/distroless/python3-debian12 AS runtime
WORKDIR /app
# Distroless python3-debian12 is CPython 3.11; the venv's site-packages is
# ABI-compatible. Put it on PYTHONPATH (the venv's bin/ scripts aren't used).
COPY --from=build /app/.venv/lib/python3.11/site-packages /app/site-packages
ENV PYTHONPATH=/app/site-packages
EXPOSE 8000
# No shell in distroless: the image entrypoint is python3, and we read $PORT
# at runtime rather than relying on shell ${PORT} expansion.
CMD ["-c", "import os, uvicorn; uvicorn.run('lineage_mcp.server:app', host='0.0.0.0', port=int(os.environ.get('PORT', '8000')))"]
