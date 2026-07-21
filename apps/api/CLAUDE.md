# apps/api — FastAPI + ARQ

~4.3k LOC Python on **3.12**, managed by **uv** (`pyproject.toml` + `uv.lock`).
Entry points: `uvicorn app.main:app` (API) and `python run_worker.py` (ARQ worker) —
same image, two commands.

```bash
uv sync              # install
uv run <cmd>         # run inside the env
uv add <pkg>         # add a dep (updates lock)
```

Lint/format is **ruff** (replaced black + flake8 + isort + bandit). Config in
`pyproject.toml`; the `ASYNC` ruleset is on deliberately — see the async/sync section below.

## Request flow

```
POST /api/tutorial/generate
  → creates TutorialInstance (status=pending)
  → enqueues generate_tutorial_task on Redis (ARQ)
  → returns instance_id immediately

worker: generate_tutorial_task
  → TutorialOrchestrator.execute()
     → TutorialAgent.get_steps()  (5 hardcoded step types)
     → for each step: validate → record → execute → record
```

Frontend polls `GET /api/tutorial/generation-status?repo_url=...`.

## Directories

| Path | Role | Notes |
|------|------|-------|
| `app/main.py` | App factory | Uses deprecated `@app.on_event`. No lifespan, no request-id middleware, no exception handlers. |
| `app/routers/` | HTTP layer | See `app/routers/CLAUDE.md`. Business logic lives here, not in services. |
| `app/models/` | SQLAlchemy ORM | See `app/models/CLAUDE.md`. |
| `app/schemas/` | Pydantic | Only covers user/settings/notifications. Most routers define response models inline. |
| `app/orchestrator/` | Pipeline engine | See `app/orchestrator/CLAUDE.md`. |
| `app/steps/` | The 5 LLM steps | See `app/steps/CLAUDE.md`. |
| `app/ai/client.py` | OpenRouter HTTP client | Retry + JSON-from-markdown salvage. |
| `app/core/` | security, dependencies, quiz_service, notification_service | Mixed concerns. |
| `app/db/session.py` | Engine + `get_db()` | Sync engine, default pool, no `pool_pre_ping`. |
| `app/workers/` | ARQ settings + task | `max_jobs=10`, `job_timeout=3600`. |
| `app/utils/repo_utils.py` | git clone, file tree walk | Clones to `/tmp/reploai/{id}`, never cleans up. |
| `app/scripts/devsetup/setup.py` | **Destructive** schema reset | `drop_all` + `create_all`. This is the migration story. |

## Async/sync mismatch (important)

Everything is `async def` but the DB layer is **synchronous** SQLAlchemy. Every
`db.query(...)` inside an async route or step blocks the event loop. Under the API this
starves concurrency; inside the worker it serializes jobs. Either move to
`asyncpg` + `AsyncSession`, or make the DB-touching functions sync and let FastAPI
thread-pool them.

## Auth

`app/core/security.py` — python-jose HS256, pbkdf2_sha256 hashing.
Access token 7 days, refresh token 1 day (refresh is *shorter* than access — inverted).
Reads `SECRET_KEY` from env; `.env` sets `JWT_SECRET_KEY`, so the fallback constant is used.

`get_current_user` in `app/core/dependencies.py` does a DB lookup per request; no caching,
no roles, no scopes, no org/tenant concept.

## Missing for SaaS

No rate limiting, no structured logging, no request IDs, no metrics/tracing, no
`/api/health` readiness distinction, no idempotency on generate, no billing/quota,
no soft deletes, no audit trail, no pagination on any list endpoint.
