# Replo — Rewrite Plan

Status: **draft, approved in principle** · Author: Dawood · Date: 2026-07-21

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

**~2 hours. Do this before anything else.**

| # | Task | Why |
|---|------|-----|
| 0.1 | Rotate OpenRouter key, `JWT_SECRET_KEY`, Postgres + Redis passwords | `.env.bak` is committed in `9d19c25` with live values |
| 0.2 | `git rm --cached .env.bak`; `.gitignore` → `.env*` | Stop re-leaking |
| 0.3 | Decide on history scrub (`git filter-repo`) | Rotation makes leaked values useless; scrubbing is optional hygiene |
| 0.4 | MIT → `FSL-1.1-Apache-2.0` | Trivial now (49 commits, one author); hard after contributors |
| 0.5 | Delete `.github/workflows/migrations.yml` | Runs `alembic upgrade head` against prod with no `alembic/` in the repo. Restored properly in 1.4 |

**Milestone:** no live secrets in git, license protects commercial use.

---

## Phase 1 — Foundation

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

| # | Task | Notes |
|---|------|-------|
| 1.1 | Monorepo skeleton; pnpm workspaces + Turborepo | Not Nx — too much machinery for two JS apps |
| 1.2 | `backend/` → `apps/api/`, lift-and-shift | No refactor in this commit |
| 1.3 | `uv` replaces pip/venv | Kills the `.deps_installed` sentinel that silently ignores new packages |
| 1.4 | **Alembic, properly.** `alembic init`, autogenerate baseline from current models | The single biggest missing capability. Nothing else is safe without it |
| 1.5 | **pydantic-settings** for all config | Permanently kills the `SECRET_KEY` / `JWT_SECRET_KEY` class of bug — typed, validated, fails at boot instead of falling back to a hardcoded string |
| 1.6 | Drop `torch`, `transformers`, `tree-sitter` | ~2GB of image for libraries nothing imports |
| 1.7 | CI with path filters (`paths: ['apps/api/**']`) | Independent deploys from one repo |
| 1.8 | Deploy `apps/api` to Railway — old code, new plumbing | Proves deploy + migrations + secrets before betting the rewrite on them |

**Milestone:** deployed API, real migrations, typed config, no secrets in repo.

---

## Phase 2 — Backend core

**~2–3 weeks.** Now the rewrite starts.

| # | Task | Notes |
|---|------|-------|
| 2.1 | **Async SQLAlchemy + asyncpg** | Largest mechanical change. Today every `db.query()` blocks the event loop inside `async def` |
| 2.2 | Extract service layer | Routers stop owning business logic. `tutorial.py` alone is 443 LOC of inline queries |
| 2.3 | Pydantic schemas out of routers → `app/schemas/` | `tutorial.py` declares 8 response models at file top |
| 2.4 | Fix N+1s with `selectinload`/joins | `list_tutorials` fires ~5 queries and stitches dicts in Python |
| 2.5 | Pagination on every list endpoint | There is currently none anywhere |
| 2.6 | Status strings → enums + PG constraints | `Repository.status` is `'PENDING'`, orchestration is `'pending'` |
| 2.7 | Drop global-unique on `Repository.github_url` → unique per `(user_id, github_url)` | Today two users cannot both add `facebook/react` |
| 2.8 | **GitHub OAuth as primary login** | Signup + private-repo access + future paid feature, one system. Deletes most hand-rolled password auth |
| 2.9 | Fix token lifetimes | Refresh (1d) is currently *shorter* than access (7d) — inverted |
| 2.10 | Central ownership enforcement | Today each endpoint re-derives "is this mine?" by joining through `Repository.user_id`. One forgotten check = data leak |
| 2.11 | **`user_llm_credentials`** — AES-256-GCM, per-row nonce, `key_version`, KEK in Railway vars | Plaintext `provider`/`label`/`last_four` for UI. Validate key on save |
| 2.12 | `Tutorial.visibility` enum + slug | Public/private from migration #1, not retrofitted |
| 2.13 | Credit ledger + Stripe customer tables — **schema only, dormant** | Cheap now, expensive to retrofit. Nothing is sold in Phase 1 |

**Milestone:** typed, async, authenticated API whose OpenAPI schema is good enough to
generate a TS client from.

---

## Phase 3 — The pipeline

**~2–3 weeks.** This is the product. Everything else is CRUD.

### 3a. Make it correct

| # | Task | Notes |
|---|------|-------|
| 3.1 | **Typed step contracts** — Pydantic in/out per step | Today steps pass one accumulating dict; step 3 reads whatever step 2 happened to emit. A renamed LLM key silently yields `None` downstream |
| 3.2 | `STEP_REGISTRY: dict[str, type[Step]]` | Replaces the parallel `step_types` list + if/elif ladder in `agent.py` |
| 3.3 | **Idempotent steps + checkpoint after each** | |
| 3.4 | **Resume from `current_step_order`** | The column exists and is written but never read. Finishing this is the durable-execution work |
| 3.5 | Per-step retry with backoff; typed failure reasons | Distinguish "LLM returned bad JSON" (retry) from "user's key revoked" (fail with a clear message) |
| 3.6 | Record error on `TutorialExecution`, not just the step row | |
| 3.7 | `save_tutorial` becomes atomic | Currently commits per module; mid-loop failure leaves a half-written tutorial |
| 3.8 | Pass user's chosen difficulty through to `Tutorial.level` | Currently hardcoded `"INTERMEDIATE"`; the `GenerateRequest` value is discarded |

### 3b. Make it safe

| # | Task | Notes |
|---|------|-------|
| 3.9 | **Credential resolved at call time, never in step context** | Structural guarantee that a user's API key can never land in `TutorialStepExecution.input_data` |
| 3.10 | Log redaction filter; never log request headers | |
| 3.11 | Harden `clone_repo`: `depth=1`, size cap, timeout, SSRF guard, **cleanup** | Currently clones arbitrary user URLs unbounded to `/tmp/reploai/{id}` and never deletes |
| 3.12 | Rate limit generation endpoints | |
| 3.13 | Cap `input_data`/`output_data` retention | This table will otherwise dominate DB size |

### 3c. Make it good

| # | Task | Notes |
|---|------|-------|
| 3.14 | **Replace 5-files × 2000-chars analysis** | This is the actual ceiling on tutorial quality. Everything downstream reasons about a repo it barely read |
| 3.15 | Prompts: one home, not two | Today `TutorialStepConfig.prompt_template` and hardcoded Python strings, switched on the sentinel `"Default prompt"` |
| 3.16 | Replace `str.format()` templating | Any `{` in repo content raises `KeyError`. Repo code full of braces is the normal case |
| 3.17 | Stop defaulting to `:free` models | `kwaipilot/kat-coder-pro:free` hardcoded in 3 places. Free tiers are rate-limited and vanish without notice |
| 3.18 | Model registry + BYOK validation | |

**Milestone:** generation that survives failure, resumes, and produces tutorials worth
publishing. **Generate 25 tutorials for well-known repos here** — Phase 5 needs seed content.

---

## Phase 4 — `apps/web` (MVP)

**~3 weeks.** Deliberately thin. Ship it, then enrich.

| # | Task |
|---|------|
| 4.1 | Rsbuild + React 19 scaffold |
| 4.2 | TanStack Router (typed routes) + TanStack Query |
| 4.3 | **`packages/api-client` generated from OpenAPI** in CI — permanently kills the `as unknown as T` casts |
| 4.4 | `packages/ui` foundation: design tokens, primitives, `MarkdownRenderer`, `DiagramViewer` |
| 4.5 | Auth: GitHub OAuth flow, **one** session module — not three hand-rolled JWT decoders |
| 4.6 | Screens: login → generate → live status → tutorial player → library → settings (BYOK) |
| 4.7 | Error boundaries, loading/error conventions |
| 4.8 | Generation status via **SSE**, not polling |

**Explicitly deferred:** authoring/editor, progress analytics, search, notifications.
Those are ~2,500 LOC of the old frontend and none of them are on the critical path to a
usable product.

**Pick one UI system.** Ant + Radix + a bespoke `ui/` dir is why `Input.tsx` is 596 lines.
**Recommendation: Radix primitives + Tailwind**, no Ant.

**Milestone:** the product works end to end, deployed.

---

## Phase 5 — `apps/site` and the public surface

**~2 weeks.** The growth channel.

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

**Ongoing.**

- Structured JSON logging + request IDs; `/health` vs `/ready` split; Sentry
- **Tests** — pytest + testcontainers on the step contracts and pipeline resume; Vitest +
  Playwright on one critical path. Testing what breaks, not chasing coverage
- LLM cost tracking per generation (feeds the dormant ledger)
- `docs/adr/` — one ADR per irreversible decision

---

## Sequencing rationale

- **Phase 1 deploys before the rewrite starts.** Discovering Railway/migration problems
  while also debugging new code is two unknowns at once.
- **Phase 3 before Phase 4** — the pipeline is testable through OpenAPI docs and needs no UI.
- **Phase 4 is thin on purpose.** The old frontend's 14.3k LOC includes an authoring
  editor, progress analytics, and search — none load-bearing for a first usable product.
- **Phase 5 last but not optional.** It's the only organic growth channel in a plan with
  no ads and no paid tier.

## Risks

| Risk | Mitigation |
|------|-----------|
| **Stalling at 70%** — the classic rewrite death | Every phase ends deployed. No phase is longer than ~3 weeks |
| Async SQLAlchemy conversion sprawls | Phase 2.1 is mechanical and isolated; do it in one pass, not incrementally |
| Tutorial quality stays mediocre | 3.14 is the real fix. If output isn't good after Phase 3, **stop and fix it** — no amount of frontend saves a bad generator |
| Scope creep into Phase 2 monetization | Ledger schema is dormant by design. Do not build Stripe flows in Phase 1 |

## Timeline

**~10–12 weeks** part-time solo. Phases 2 and 3 can overlap; 4 and 5 cannot.
