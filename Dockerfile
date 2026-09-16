# syntax=docker/dockerfile:1
# Multi-stage build mirroring the explorer service: build deps in one stage,
# ship a slim runtime. The virtualenv is created at /app/.venv so the start
# command (also in railpack.json) resolves /app/.venv/bin/uvicorn.
FROM python:3.13-slim AS build
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_PROJECT_ENVIRONMENT=/app/.venv \
    UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

# Install dependencies first for a cached layer, then the project itself.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
RUN uv sync --frozen --no-dev

FROM python:3.13-slim AS runtime
WORKDIR /app
COPY --from=build /app /app
ENV PATH="/app/.venv/bin:$PATH"
EXPOSE 8000
# Railway injects $PORT; bind all interfaces so the proxy can reach the app.
CMD ["/bin/sh", "-c", "/app/.venv/bin/uvicorn lineage_mcp.server:app --host 0.0.0.0 --port ${PORT:-8000}"]
