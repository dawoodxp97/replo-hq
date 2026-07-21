FROM python:3.12-slim

# uv from its official distroless image — no curl|sh installer in the build.
COPY --from=ghcr.io/astral-sh/uv:0.11 /uv /uvx /bin/

WORKDIR /app

# git is a genuine runtime dependency: gitpython shells out to it to clone repos.
# curl is for the healthcheck below.
# gcc and libpq-dev are gone — psycopg2-binary ships prebuilt wheels with libpq
# bundled, so nothing is compiled at build time.
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    PYTHONUNBUFFERED=1

# Dependency layer, cached independently of source. --frozen fails the build if
# uv.lock is stale rather than silently resolving something different from dev.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY . .

ENV PATH="/app/.venv/bin:$PATH"

RUN useradd --create-home --uid 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# The worker overrides this with `python run_worker.py` — same image, two entrypoints.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
