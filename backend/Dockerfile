# backend/Dockerfile (multi-stage)
FROM python:3.11-slim AS build
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev build-essential && \
    rm -rf /var/lib/apt/lists/*

COPY backend/pyproject.toml backend/requirements.txt /app/
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY backend /app

FROM python:3.11-slim AS runtime
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN useradd -m -u 1000 appuser
COPY --from=build /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=build /usr/local/bin /usr/local/bin
COPY --chown=appuser:appuser backend /app

USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
