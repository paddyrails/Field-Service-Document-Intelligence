FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files first for layer caching
COPY pyproject.toml ./

# Install dependencies (no lock file yet — generates one at build time)
RUN uv sync --no-dev

# Copy application source
COPY config.py channel_router.py handlers.py main.py ./

CMD ["uv", "run", "python", "main.py"]
