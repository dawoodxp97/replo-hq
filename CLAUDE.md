# Replo — Repo Guide

AI tutorial generator. User submits a GitHub repo URL → background pipeline clones it,
runs a 5-step LLM chain → persists a tutorial (modules + quizzes) → user reads it in a player UI.

## Layout

**Mid-rewrite.** See [`docs/REWRITE_PLAN.md`](docs/REWRITE_PLAN.md) for the phased plan and
[`docs/DECISIONS.md`](docs/DECISIONS.md) for why each choice was made. Currently in **Phase 1**
(structure + tooling; no logic changes yet).

| Path | What |
|------|------|
| `apps/api/` | FastAPI API + ARQ worker + SQLAlchemy models. See `apps/api/CLAUDE.md`. |
| `apps/web-legacy/` | Pre-rewrite Next.js client. **Reference only** — outside the pnpm workspace, not built by CI. Deleted after Phase 5 ports the landing components. |
| `apps/web/` | (Phase 4) Rsbuild + React 19 + TanStack Router — the authenticated product. |
| `apps/site/` | (Phase 5) Next.js — marketing, public tutorials, `/explore`, docs. |
| `packages/api-client/` | (Phase 4) TS client **generated** from the API's OpenAPI schema. |
| `packages/ui/` | (Phase 4) Design tokens + primitives shared by `web` and `site`. |
| `infra/` | Compose, Dockerfiles, deploy config. |
| `docs/` | Rewrite plan, decision log, ADRs. |
| `scripts/` | `setup-dev.sh`, `build.sh`, `start.sh` — being retired as `make` absorbs them. |
| `tests/load/` | k6 load script. The **only** test file in the repo. |
| `aws/` | Empty. |
| `AI_LAYER_PLAN.md` | Original design prompt for the orchestrator layer. Aspirational; superseded by `docs/REWRITE_PLAN.md`. |

## Services

Postgres 15, Redis 7, backend (uvicorn :8000), worker (ARQ), frontend (:3000).
All wired in `docker-compose.yml` on `replo-network`.

## Commands

```bash
make setup       # install all deps (uv + pnpm)
make dev         # api + worker + web, parallel
make api         # uvicorn --reload (auto-starts postgres+redis)
make worker      # ARQ worker
make migrate     # alembic upgrade head
make migration m='add foo'
make stop        # docker compose down
```

Python deps via **uv** (`apps/api/pyproject.toml` + `uv.lock`). Node via **pnpm workspaces**
+ Turborepo.

## Config

Single root `.env`, read by **pydantic-settings** in `apps/api`. Typed and validated —
missing or malformed config fails at boot rather than falling back to a default.

## Known landmines

Fixed in Phase 1: `.env.bak` untracked, `.gitignore` broadened to `.env*`, the broken
migrations workflow deleted, license moved MIT → FSL-1.1-ALv2.

**⚠️ Still outstanding: the leaked credentials have not been rotated.** `.env.bak` sat in
git history with a live `OPENROUTER_API_KEY`, `JWT_SECRET_KEY`, and DB/Redis passwords.
Untracking the file does not invalidate them — rotation is the actual fix.

- **No Alembic yet.** Schema today is created by `apps/api/app/scripts/devsetup/setup.py`,
  which **drops all tables** and recreates them. Task 6 replaces this with a real baseline
  migration; until then, do not point that script at anything you care about.
- **No unit or integration tests.** Only a k6 load script.
- **Two token-expiry implementations** (`middleware.ts` and `app/(private)/layout.tsx`) plus a
  third in `hooks/useTokenRefresh.ts`, all hand-rolling JWT base64 decode.
- **JWT secret env name mismatch**: `.env` defines `JWT_SECRET_KEY`, but
  `backend/app/core/security.py` reads `SECRET_KEY` and silently falls back to
  `"a_very_secret_key_fallback"`. Every deployed token is signed with a hardcoded constant.
- Duplicate component trees: `components/core/` vs `components/layout/`,
  `components/author/` vs `components/features/authoring/`.

## Conventions

- Backend: relative imports (`from ..models.user import User`), routers mounted under `/api/*`.
- Frontend: `@/` path alias, services layer wraps `apiClient`, Zustand for auth state,
  TanStack Query provider is mounted but barely used.
