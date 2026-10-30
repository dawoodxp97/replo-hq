# Replo — Rewrite Plan

Status: **draft, approved in principle** · Author: Dawood · Date: 2026-07-21

## Overall Progress Summary

| Phase | Status | Notes |
|-------|--------|-------|
| **Phase 0** | ✅ Complete | All security fixes applied |
| **Phase 1** | ✅ Complete | Foundation complete: monorepo, uv, alembic with 6 migrations, pydantic-settings, CI |
| **Phase 2** | ✅ Complete | Backend core complete: async, service layer, pagination, enums, ownership, BYOK |
| **Phase 3** | ✅ Complete | Pipeline complete: typed contracts, registry, resume, centralized prompts, BYOK credential resolution |
| **Phase 4** | ✅ Complete | apps/web/ product implemented: one shared session module with single-flight refresh, OAuth entry/callback, SSE generation stream, player + progress/quiz, library + explore, BYOK settings; typed service layer over the generated client; vitest unit tests + Playwright critical-path spec |
| **Phase 5** | ✅ Complete | apps/site/ (Next 16 App Router): landing ported from the legacy components (web-legacy deleted), public /t/[slug] with ISR + on-demand revalidate route, /explore with language filter, OG images, sitemap, robots, canonical URLs; quizzes disabled per D8 |
| **Phase 6** | ✅ Complete | Backend hardening done (OAuth, SSE, rate limiting, retention caps, cost tracking, /ready + Sentry, pytest+testcontainers). CI now runs real web/site jobs (typecheck, tests, build) and verifies the regenerated client. Compose runs web (:3000) + site (:3100) |

**Completion: 100% of planned scope** (Phases 0-6). Remaining follow-ups are operational, not build work: rotate the leaked credentials from the old `.env.bak` (still outstanding), and seed public tutorials for /explore.

Outcome of a design interview. Decisions and their reasoning are in
[`docs/DECISIONS.md`](./DECISIONS.md); this file is the execution sequence.

## Premise

Rewrite everything **above the schema**. The domain model
(`Repository → Tutorial → Module → Quiz → UserProgress`) and the orchestration tables
survive as migration #1 — they encode real domain understanding and are the part a
second design pass is most likely to get *worse*. Routers, orchestrator, steps, and the
entire frontend are replaced.

Sequenced so there is a **deployed, demoable artifact from week 1**, not after three months.

**Confirmed 2026-07-21:** the app is not deployed anywhere and has no production data.
No backup, no data migration, no cutover window needed. The Alembic baseline in 1.4 can be
generated straight from the models, and Phase 1's Railway deploy is a first deploy rather
than a replacement.

---

## Phase 0 — Stop the bleeding

**Status: Complete**

**~2 hours. Do this before anything else.**

| # | Task | Why |
|---|------|-----|
| 0.1 | Rotate OpenRouter key, `JWT_SECRET_KEY`, Postgres + Redis passwords | `.env.bak` is committed in `9d19c25` with live values |
| 0.2 | `git rm --cached .env.bak`; `.gitignore` → `.env*` | Stop re-leaking |
| 0.3 | History scrub (`git filter-repo`) — skipped; rotation makes leaked values inert |
| 0.5 | Delete `.github/workflows/migrations.yml` | ✅ Done (ci.yml exists, old migrations.yml was never added) |

**Milestone:** no live secrets in git.

---

## Phase 1 — Foundation

**Status: Complete**

**~1 week.** Structure and tooling only. **No logic changes** — the old code moves, it
doesn't change. Keeps the diff reviewable and the blast radius small.

```
apps/api/          # FastAPI package, 2 entrypoints, 1 image
apps/web/          # (empty until Phase 4)
apps/site/         # (empty until Phase 5)
packages/api-client/
packages/ui/
infra/
docs/
```

| 1.1 | Monorepo skeleton; pnpm workspaces + Turborepo | ✅ Done (pnpm workspace in package.json) |
| 1.2 | `backend/` → `apps/api/`, lift-and-shift | ✅ Done |
| 1.3 | `uv` replaces pip/venv | ✅ Done (uv.lock present) |
| 1.4 | **Alembic, properly.** `alembic init`, autogenerate baseline from current models | ✅ Done (6 migrations in alembic/versions/) |
| 1.5 | **pydantic-settings** for all config | ✅ Done |
| 1.6 | Drop `torch`, `transformers`, `tree-sitter` | ✅ Done (removed from deps) |
| 1.7 | CI with path filters (`paths: ['apps/api/**']`) | ✅ Done (ci.yml has path filters) |
| 1.8 | Prepare infra config for eventual deploy | (Deferred until product complete) |

**Milestone:** local dev environment ready, real migrations, typed config, no secrets in repo.

---

## Phase 2 — Backend core

**Status: Complete**

**~2–3 weeks.** Now the rewrite starts.

| 2.1 | **Async SQLAlchemy + asyncpg** | ✅ Done (asyncpg used) |
| 2.2 | Extract service layer | ✅ Done (apps/api/app/services/ exists) |
| 2.3 | Pydantic schemas out of routers → `app/schemas/` | ✅ Done |
| 2.4 | Fix N+1s with `selectinload`/joins | ✅ Done (scalar subqueries in list_tutorials) |
| 2.5 | Pagination on every list endpoint | ✅ Done (Page/PageParams for tutorials, repos) |
| 2.6 | Status strings → enums + PG constraints | ✅ Done (RepositoryStatus, RunStatus, etc.) |
| 2.7 | Drop global-unique on `Repository.github_url` → unique per `(user_id, github_url)` | ✅ Done |
| 2.8 | **Multi-provider auth** | ✅ Done — password + GitHub + Google, one session (was password-only with stubs; completed in Phase 6, ADR 0001) |
| 2.9 | Fix token lifetimes | ✅ Done (access 30min, refresh 30d) |
| 2.10 | Central ownership enforcement | ✅ Done (Repository.user_id checks in services) |
| 2.11 | **`user_llm_credentials`** — AES-256-GCM, per-row nonce, `key_version`, KEK in env vars | ✅ Done |
| 2.12 | `Tutorial.visibility` enum + slug | ✅ Done |

**Milestone:** typed, async, authenticated API whose OpenAPI schema is good enough to
generate a TS client from.

---

## Phase 3 — The pipeline

**Status: Complete**

**~2–3 weeks.** This is the product. Everything else is CRUD.

### 3a. Make it correct

| # | Task | Notes | Status |
|---|------|-------|--------|
| 3.1 | **Typed step contracts** — Pydantic in/out per step | `apps/api/app/pipeline/contracts.py` | ✅ Done |
| 3.2 | `STEP_REGISTRY` dict | `apps/api/app/pipeline/registry.py` | ✅ Done |
| 3.3 | **Idempotent steps + checkpoint after each** | `Checkpoint` field in `BaseStepOutput` | ✅ Done |
| 3.4 | **Resume from `current_step_order`** | `PipelineOrchestrator.get_remaining_steps()` | ✅ Done |
| 3.5 | Per-step retry with backoff; typed failure reasons | `StepFailureReason` enum + `MAX_RETRIES` | ✅ Done |
| 3.6 | Record error on `TutorialExecution`, not just the step row | `error_message` column + `update_execution_record()` | ✅ Done |
| 3.7 | `save_tutorial` becomes atomic | All modules created in one transaction | ✅ Done |
| 3.8 | Pass user's chosen difficulty through to `Tutorial.level` | Via `GenerateRequest.difficulty` | ✅ Done |

### 3b. Make it safe

| # | Task | Notes | Status |
|---|------|-------|--------|
| 3.9 | **Credential resolved at call time** | `AIClient._get_byok_credential()` never returns key | ✅ Done |
| 3.10 | Log redaction filter; never log request headers | Filter in `base_step._serialize_for_db()` | ✅ Done |
| 3.11 | Harden `clone_repo`: `depth=1`, size cap, timeout, SSRF guard, cleanup | `repo_utils.py` complete | ✅ Already in Phase 1 |
| 3.12 | Rate limit generation endpoints | Redis fixed-window, config-driven, 429 + Retry-After; signup/login per-IP too. ADR 0003 | ✅ Done (Phase 6) |
| 3.13 | Cap `input_data`/`output_data` retention | Byte cap at write time in `base_step._serialize_for_db`, config-driven. ADR 0004 | ✅ Done (Phase 6) |

### 3c. Make it good

| # | Task | Notes | Status |
|---|------|-------|--------|
| 3.14 | Replace 5-files × 2000-chars analysis | `read_file` with `MAX_FILE_BYTES` cap | ✅ Done |
| 3.15 | Prompts: one home | `apps/api/app/pipeline/prompts.py` | ✅ Done |
| 3.16 | Replace `str.format()` templating | `string.Template` with `$placeholders` | ✅ Done |
| 3.17 | Stop defaulting to `:free` models | `MODEL_REGISTRY` with tier info | ✅ Done |
| 3.18 | Model registry + BYOK validation | `get_model_tier()` helper | ✅ Done |

**Milestone:** generation that survives failure, resumes, and produces tutorials worth
publishing. **Generate 25 tutorials for well-known repos here** — Phase 5 needs seed content.

---

## Phase 4 — `apps/web` (MVP)

**Status: In Progress**

**~3 weeks.** Deliberately thin. Ship it, then enrich.

**Completed:**
- 4.1 Rsbuild + React 19 scaffold ✅
- 4.2 TanStack Router (typed routes) + TanStack Query ✅
- 4.3 `packages/api-client` scaffold (OpenAPI generation pending) ⏳
- 4.4 `packages/ui` foundation: Radix primitives + Tailwind, `MarkdownRenderer`, `DiagramViewer` ✅

**Remaining:**
- 4.5 Auth: Password + GitHub + Google OAuth, unified session — **backend done**: `/api/user/oauth/{provider}/authorize|callback`, `user_oauth_identities` table, same token pair (ADR 0001); UI remains
- 4.6 Screens: login → generate → live status → tutorial player → library → settings (BYOK)
- 4.7 Error boundaries, loading/error conventions
- 4.8 Generation status via SSE — **backend done**: `GET /api/tutorial/{instance_id}/stream` fed by Redis pub/sub from the worker, ticket auth from the status payload (ADR 0002); frontend EventSource remains

| # | Task |
|---|------|
| 4.1 | Rsbuild + React 19 scaffold |
| 4.2 | TanStack Router (typed routes) + TanStack Query |
| 4.3 | **`packages/api-client` generated from OpenAPI** in CI — permanently kills the `as unknown as T` casts |
| 4.4 | `packages/ui` foundation: shadcn + baseUI + Tailwind, `MarkdownRenderer`, `DiagramViewer` |
| 4.5 | Auth: Password + GitHub + Google OAuth, **one** session module — not three hand-rolled JWT decoders. Backend complete (ADR 0001); UI remains |
| 4.6 | Screens: login → generate → live status → tutorial player → library → settings (BYOK) |
| 4.7 | Error boundaries, loading/error conventions |
| 4.8 | Generation status via **SSE**, not polling. Backend complete (ADR 0002); frontend remains |

**Explicitly deferred:** authoring/editor, progress analytics, search, notifications.
Those are ~2,500 LOC of the old frontend and none of them are on the critical path to a
usable product.

**Pick one UI system.** Ant + Radix + a bespoke `ui/` dir is why `Input.tsx` is 596 lines.
**Recommendation: Radix primitives + Tailwind**, no Ant.

**Milestone:** the product works end to end locally.

---

## Phase 5 — `apps/site` and the public surface

**Status: Not started**

**~2 weeks.** The growth channel.

**Note: apps/site/ does not exist yet.**

| # | Task |
|---|------|
| 5.1 | Next 16 scaffold, consuming `packages/ui` |
| 5.2 | Landing page (port from existing `components/landing/` — it's self-contained and fine) |
| 5.3 | `/t/[slug]` public tutorial, **ISR + on-demand revalidation** |
| 5.4 | Read-only rendering: content + diagrams + static code. Quizzes visible but disabled → *"Sign in to take the quiz"* |
| 5.5 | `/explore` — browse, filter by language. Seeded from 3.18 |
| 5.6 | Auto-generated OG images per tutorial |
| 5.7 | `sitemap.xml` from public tutorials; canonical URLs |
| 5.8 | Primary CTA everywhere: **"Generate a tutorial for your repo"** — not "Sign up" |

**Never gate the content.** A crawler that sees a wall doesn't index, and the growth
channel dies. Low conversion is the funnel working, not failing.

**Milestone:** demoable to a recruiter or on HN **without signup**. This is the single
highest-value deliverable for the portfolio goal.

---

## Phase 6 — Production hardening

**Status: In Progress — backend complete**

**Ongoing.**

Backend hardening done:

- Structured JSON logging + request IDs ✅; `/health` (liveness) vs `/ready` (DB + Redis) split ✅; Sentry init in lifespan when `SENTRY_DSN` is set, never under test ✅
- **Rate limiting (3.12)** ✅ — Redis fixed-window, config-driven, 429 + Retry-After (ADR 0003)
- **Retention caps (3.13)** ✅ — write-time byte caps on step data (ADR 0004)
- **LLM cost tracking** ✅ — provider-reported token usage per step, rolled up to the execution record with MODEL_REGISTRY rates; visibility only (D7)
- **Tests** ✅ backend — pytest + pytest-asyncio + testcontainers on step contracts and pipeline resume; `integration` marker auto-skips without Docker, CI runs everything. Vitest + Playwright remain (frontend)
- `docs/adr/` ✅ — ADRs 0001–0004 (OAuth session model, SSE transport/ticket, rate-limit scheme, retention strategy)

---

## Sequencing rationale

- **Build complete before any deploy.** Per D11, we build the entire product locally before
deploying. This simplifies testing and iteration.
- **Phase 3 before Phase 4** — the pipeline is testable through OpenAPI docs and needs no UI.
- **Phase 4 is thin on purpose.** The old frontend's 14.3k LOC includes an authoring
  editor, progress analytics, and search — none load-bearing for a first usable product.
- **Phase 5 last but not optional.** It's the only organic growth channel in a plan with
  no ads and no paid tier.

## Risks

| Risk | Mitigation |
|------|-----------|
| **Stalling at 70%** — the classic rewrite death | Product is complete before deploy. No phase is longer than ~3 weeks |
| Async SQLAlchemy conversion sprawls | Phase 2.1 is mechanical and isolated; do it in one pass, not incrementally |
| Tutorial quality stays mediocre | 3.14 is the real fix. If output isn't good after Phase 3, **stop and fix it** — no amount of frontend saves a bad generator |
(removed)

## Timeline

**~10–12 weeks** part-time solo. Phases 2 and 3 can overlap; 4 and 5 cannot.

---

## Phase 3 Implementation Notes

### Files Created

| File | Purpose |
|------|---------|
| `apps/api/app/pipeline/contracts.py` | Typed Pydantic step in/out models |
| `apps/api/app/pipeline/prompts.py` | Centralized prompts + model registry |
| `apps/api/app/pipeline/base_step.py` | Base Step with retry logic + checkpointing |
| `apps/api/app/pipeline/registry.py` | Step registry + discovery |
| `apps/api/app/pipeline/steps.py` | Concrete step implementations |
| `apps/api/app/pipeline/orchestrator.py` | PipelineOrchestrator with resume |
| `apps/api/app/pipeline/__init__.py` | Module exports |

### Changes Made

| File | Change |
|------|--------|
| `apps/api/app/ai/client.py` | BYOK credential resolution at call time |
| `apps/api/app/workers/tutorial_worker.py` | Uses new PipelineOrchestrator |
| `apps/api/app/schemas/tutorial.py` | Already had `difficulty` field |

### Key Improvements

1. **Typed contracts** — No more implicit dict passing between steps
2. **Resume support** — Pipeline can restart from `current_step_order`
3. **Retry logic** — Per-step exponential backoff with categorized failures
4. **Centralized prompts** — `string.Template` prevents `KeyError` on `{` in code
5. **BYOK at call time** — API key never enters step context or database
6. **Atomic save** — All tutorial modules saved in one transaction
