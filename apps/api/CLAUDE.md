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

Frontend polls `GET /api/tutorial/generation/status?repo_url=...` (legacy, URL-keyed) or
`GET /api/tutorial/{instance_id}/status` (preferred).

`POST /generate` returns **202**, normalises the URL through `repo_utils.normalise_repo_url`
before it ever reaches the worker, and **fails with 502 if Redis is unreachable**. It
previously stored the raw URL and skipped the enqueue silently when the pool was missing —
returning a pending instance id for a job that would never run.

`GenerateRequest.difficulty`, `.focus` and `.description` are accepted and validated but
still discarded: `steps/save_tutorial.py` hardcodes `level="intermediate"`. Wiring them
through is Phase 3.

## Directories

| Path | Role | Notes |
|------|------|-------|
| `app/main.py` | App factory | Uses deprecated `@app.on_event`. No lifespan, no request-id middleware, no exception handlers. |
| `app/routers/` | HTTP layer | See `app/routers/CLAUDE.md`. Business logic lives here, not in services. |
| `app/models/` | SQLAlchemy ORM | See `app/models/CLAUDE.md`. |
| `app/schemas/` | Pydantic | Converted slices only (user, settings, notifications, repo, tutorial). Unconverted routers still define response models inline. |
| `app/orchestrator/` | Pipeline engine | See `app/orchestrator/CLAUDE.md`. |
| `app/steps/` | The 5 LLM steps | See `app/steps/CLAUDE.md`. |
| `app/ai/client.py` | OpenRouter HTTP client | Retry + JSON-from-markdown salvage. |
| `app/core/` | config, security, crypto, logging, dependencies | See BYOK section below. |
| `app/services/` | Business logic | New in Phase 2. Routers call services; services own the domain rules. |
| `app/db/session.py` | Both engines + `get_async_db()` / `get_db()` | Async asyncpg engine with `pool_pre_ping`; the sync half exists only for unconverted routers. |
| `app/workers/` | ARQ settings + task | `max_jobs=10`, `job_timeout=3600`. |
| `app/utils/repo_utils.py` | git clone, file tree walk | https+github.com allowlist, `--depth 1`, timeout, size cap, `remove_clone()`. Read its docstring before touching anything handling a URL or path. |
| `alembic/` | Migrations | Baseline `7b1291fb0c9b` captures all 12 tables. |

## Migrations

```bash
make migrate                      # alembic upgrade head
make migration m='add foo'        # autogenerate a revision
```

The URL is **not** in `alembic.ini` — `env.py` injects it from the same
`Settings` object the app uses, so migrations can never target a different
database than the app, and no credentials sit in a tracked file.

Two details in `env.py` that look cosmetic and are not:

- `import app.models` — registers every model on `Base.metadata`. Without it,
  autogenerate sees an empty schema and offers to drop all your tables.
- `.replace("%", "%%")` on the URL — alembic stores it in a configparser, which
  treats `%` as interpolation. A password containing `@` URL-encodes to `%40`
  and otherwise crashes every migration run.

The destructive `drop_all`/`create_all` setup script is gone. Alembic owns the
schema now.

## Async/sync migration — HTTP layer done

The original problem: everything was `async def` over a **synchronous** DB layer, so every
`db.query(...)` blocked the event loop, serialising concurrent requests and worker jobs.

**All routers are now async** (`get_async_db` / `AsyncSession` over asyncpg), converted one
domain at a time in this order — each pass doing async + service-backed + typed schemas +
N+1-fixed + paginated + ownership-checked together:

`user/auth` → `repo` → `tutorial` → `progress` → `author` → `settings` → `dashboard` →
`notification` → `search` ✅

**What remains sync:** the ARQ worker and the orchestrator/steps (`app/orchestrator/`,
`app/steps/`, `app/workers/tutorial_worker.py`) still use `SessionLocal`. `db/session.py`
keeps its sync half alive for them; that is Phase 3's conversion. Delete the sync half and
the `psycopg2` dependency only when the pipeline flips — Alembic keeps `settings.sqlalchemy_url`
but builds its own engine, so it is unaffected.

`settings.async_sqlalchemy_url` is derived from `sqlalchemy_url` by swapping the driver, so
the two can never point at different databases.

## Shared plumbing (Phase 2 foundation)

Use these in every converted router. They exist so nine slices don't each invent their own.

| Module | Use |
|---|---|
| `core/exceptions.py` | Raise `NotFoundError`, `ConflictError`, `ExternalServiceError`… **never** `HTTPException` in new code — services must be callable without FastAPI |
| `core/ownership.py` | `get_owned_tutorial`, `get_readable_tutorial`, `get_owned_module`, `owned_tutorials_stmt` |
| `core/pagination.py` | `page_params` dependency, `Page[T]` envelope, `paginate()` |
| `core/dependencies.py` | `get_current_user_async`, `get_optional_user` |
| `core/middleware.py` | Request IDs (already wired) |
| `core/context.py` | `get_request_id()` anywhere, no argument threading |

### Ownership raises NotFound, never PermissionDenied

"Exists but isn't yours" and "doesn't exist" both return **404**. A 403 confirms the id is
real, turning a guessable id into an enumeration oracle. `PermissionDeniedError` is only for
operations on objects the caller can legitimately see (role/plan checks).

Nothing but `Repository` stores `user_id`, so ownership is derived:
`Repository → Tutorial → Module → Quiz`. Use the helpers rather than re-deriving the join —
that's where a filter gets dropped, and a missing filter looks like correct code in review.

`get_readable_tutorial` is the wider one backing public `/t/{slug}` pages: public and
unlisted are readable by anyone including anonymous callers. Unlisted means "not in
/explore or the sitemap", not access-controlled.

### Error envelope

Every failure — `AppError`, validation, `HTTPException`, unhandled — renders as:

```json
{"error": {"code": "not_found", "message": "…", "request_id": "…"}}
```

Unhandled exceptions never surface their text (connection strings, SQL, upstream payloads);
`request_id` is the bridge to the full trace in the logs.

### Pagination

Offset-based. **`limit` is capped at 100** — without a ceiling `?limit=1000000` is a way to
exhaust memory. `paginate()` runs two queries and strips `ORDER BY` from the count.

### Request IDs

`RequestIDMiddleware` honours an inbound `X-Request-ID` (so a trace survives across
services) or generates one. It appears in every log line, the error body, and the response
header. uvicorn's own access log is raised to WARNING because ours supersedes it.

## BYOK credentials

`app/core/crypto.py` (AES-256-GCM) + `app/services/credentials.py`, exposed at
`/api/settings/credentials` (list / add / delete). **No endpoint returns a key** — there is
deliberately no "reveal" route, since the whole point of encrypting at rest is that a
database dump yields nothing usable.

**`services/credentials.py` is the only decryption path in the application.**
Routers, the orchestrator and steps work with `user_id` and never see key material.

Three properties worth not breaking:

1. **AAD binding.** Every ciphertext is authenticated against `"{user_id}:{provider}"`.
   Copying a `ciphertext`/`nonce` pair from one user's row into another's makes decryption
   *fail* rather than yielding a working key billed to the first user. Verified by test.
2. **Never in step context.** `TutorialStepExecution.input_data` persists the accumulating
   context dict to Postgres verbatim. The credential can't leak there because it's never put
   in the dict — `resolve_credential` is called at the moment of the LLM request.
3. **`ResolvedCredential` has a custom `__repr__`.** The default dataclass repr prints every
   field, which would put the key in any traceback or f-string that touches it.

Decryption failure returns `None`, never a partial result — an unreadable credential is
treated as absent, so callers fall back to "no key configured" rather than sending garbage.

### base_url is an SSRF surface

BYOK lets the user supply the endpoint, and **the server** fetches it — so it is the second
SSRF surface after `git clone`. It was unvalidated: `http://169.254.169.254/`,
`http://127.0.0.1:6379` and any internal address were reachable, and `validate_credential`
returned the HTTP status to the caller, making it a port scanner with a readable oracle.

`core/net.py::validate_outbound_url` enforces https, no embedded credentials, and that
**every** address the host resolves to is public unicast. Enforced at both the schema and
`store_credential`, since the stored value is what later gets fetched.

`allow_redirects=False` on the validation request is load-bearing: without it a public host
just 302s to a private one and the address check never sees it.

Residual: DNS rebinding between the check and the connect. Closing it means pinning the
validated address into the connector.

`app/core/logging.py` installs `RedactingFilter` on the root handlers in both entrypoints.
It scrubs `sk-`/`sk-or-v1-`/`sk-ant-`/`gh*_` tokens, `Authorization` headers, and inline
credentials in Postgres/Redis URLs — from messages, args **and exception text**. It is
defence in depth; the primary control is still not logging secrets.

### Key rotation

`key_version` is stored per row. Set `CREDENTIAL_ENCRYPTION_KEY_PREVIOUS` during a rotation
window so old rows still decrypt while new writes use the current key.

**Losing `CREDENTIAL_ENCRYPTION_KEY` makes every stored credential permanently unreadable.**
Back it up somewhere other than `.env`.

## Health endpoints

- `/api/health` — liveness. Touches nothing external, so a database blip can't cause the
  orchestrator to restart a healthy container.
- `/api/ready` — readiness. Checks Postgres and Redis. This is what a load balancer polls.

## Auth

`app/core/security.py` — python-jose HS256, pbkdf2_sha256 hashing. Access token 30 min,
refresh token 30 days. The key comes from `settings.jwt_secret_key`, which has **no default**
— boot fails without it.

Previously `security.py` read `SECRET_KEY` while `.env` defined `JWT_SECRET_KEY`, so every
token in every deployment was signed with the hardcoded fallback string in the source.

`get_current_user_async` does a DB lookup per request; no caching, no roles, no scopes, no
org/tenant concept. Login burns the KDF even for unknown emails, so response time does not
reveal which addresses are registered.

### Session revocation

`User.sessions_valid_from` is a cutoff: any token whose issue time precedes it is rejected.
Set by a password change and by `POST /api/settings/security/revoke-sessions`.

Checked in **three** places — `get_current_user_async`, `get_optional_user`, and
`auth_service.refresh_tokens`. The refresh path is the one that matters: without it,
revocation would expire the 30-minute access tokens and then happily mint new ones for the
next 30 days.

Tokens carry a custom **`iat_ms`** claim. Standard `iat` is whole seconds, which is wrong in
both directions — comparing at full precision locks a user out of the login they perform
immediately after changing their password, and flooring the cutoff lets tokens issued in the
same second survive revocation. Both were caught by test. Don't "simplify" it back to `iat`.

**Still missing:** refresh token rotation and reuse detection. `sessions_valid_from` can only
revoke *everything* at once, never a single device, and a stolen refresh token is valid until
used-or-revoked. The real fix needs a token store.

## Missing for SaaS

Done: request IDs, liveness/readiness split, log redaction, pagination and a uniform error
envelope on converted slices.

Still missing: rate limiting, metrics/tracing, **idempotency on `POST /generate`** (a
double-click queues two runs), quota enforcement against the dormant credit tables, soft
deletes, and an audit trail. No tests beyond the k6 script — Phase 6.
