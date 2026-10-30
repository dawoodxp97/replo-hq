.PHONY: help setup services api worker web dev migrate migration openapi build start stop logs clean

# Root .env is the single source of config. pydantic-settings (apps/api) and
# Next/Rsbuild read it directly — no `export $(grep ...)` shell hack, which
# broke on any value containing a space.

help:
	@echo "Development:"
	@echo "  make setup     - Install all dependencies (uv + pnpm)"
	@echo "  make services  - Start Postgres + Redis only"
	@echo "  make api       - Start API server (auto-starts services)"
	@echo "  make worker    - Start ARQ worker (auto-starts services)"
	@echo "  make web       - Start frontend"
	@echo "  make dev       - Start api + worker + web together"
	@echo ""
	@echo "Database:"
	@echo "  make migrate   - Apply migrations (alembic upgrade head)"
	@echo "  make migration - Generate one: make migration m='add foo'"
	@echo ""
	@echo "Production:"
	@echo "  make build / start / stop / logs / clean"

setup:
	@echo "==> Python deps (uv)"
	@cd apps/api && uv sync
	@echo "==> Node deps (pnpm)"
	@pnpm install
	@echo "Done. Copy .env.example to .env if you haven't."

services:
	@docker compose up -d postgres redis

api: services
	@cd apps/api && uv run uvicorn app.main:app --reload --host 0.0.0.0 --port $${BACKEND_PORT:-8000}

worker: services
	@cd apps/api && uv run python run_worker.py

# web-legacy sits outside the pnpm workspace on purpose, so it uses npm directly.
# Phase 4 replaces this target with `pnpm --filter web dev`.
web:
	@cd apps/web-legacy && npm run dev

dev: services
	@trap 'kill 0' EXIT; $(MAKE) -j3 api worker web

migrate:
	@cd apps/api && uv run alembic upgrade head

migration:
	@test -n "$(m)" || (echo "Usage: make migration m='describe the change'" && exit 1)
	@cd apps/api && uv run alembic revision --autogenerate -m "$(m)"

# Exports the OpenAPI schema and regenerates packages/api-client from it.
# Run after every contract change and COMMIT both outputs — apps/web and
# apps/site are built against the generated types, not hand-written ones.
#
# npx rather than the workspace script: a broken @tanstack/router spec in
# apps/web currently fails any full `pnpm install`, and client generation must
# not depend on every workspace package installing cleanly. The api-client
# package's own `generate` script does the same thing once the workspace
# installs.
openapi:
	@cd apps/api && uv run python -c "import json; from app.main import app; print(json.dumps(app.openapi(), indent=2))" > openapi.json
	@echo "==> apps/api/openapi.json written"
	@npx --yes @hey-api/openapi-ts@0.54.0 -i apps/api/openapi.json -o packages/api-client/src -c @hey-api/client-fetch
	@npx --yes prettier@3.4.2 --write "packages/api-client/src/**/*" >/dev/null
	@echo "==> packages/api-client/src regenerated"

build:
	@docker compose build

start:
	@docker compose up -d

stop:
	@docker compose down

logs:
	@docker compose logs -f

clean:
	@docker compose down -v
	@docker system prune -f
