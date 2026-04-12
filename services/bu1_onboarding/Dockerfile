FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first — Docker caches this layer
# Only re-runs pip install if pyproject.toml or uv.lock changes
COPY pyproject.toml uv.lock ./

# Install dependencies (no dev extras, frozen lockfile)
RUN uv sync --frozen --no-dev

# Copy application source
COPY api/       ./api/
COPY service/   ./service/
COPY dao/       ./dao/
COPY common/    ./common/
COPY ingestion/    ./ingestion/

EXPOSE 8001

CMD ["uv", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8001"]
