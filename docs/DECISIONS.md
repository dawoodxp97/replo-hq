# Decision Log

Decisions taken during the 2026-07-21 design interview, with the reasoning that produced
them. Execution sequence lives in [`REWRITE_PLAN.md`](./REWRITE_PLAN.md).

Recorded so future-you (and reviewers) can see *why*, not just *what* — and so a decision
gets reopened deliberately rather than drifted away from.

---

## D1 — Rewrite above the schema, not from scratch

**Decision:** keep the domain model and orchestration tables; replace routers,
orchestrator, steps, and all frontend.

**Why:** the domain decomposition survived contact with a working app and encodes real
understanding. A second design pass, done from memory rather than from usage, is more
likely to make it worse. The orchestration schema in particular
(`TutorialInstance` / `Execution` / `StepExecution` / `StepConfig` with per-step audit rows
and `current_step_order`) is a good design that supports resume and replay — the *code*
never implemented it. That's a good schema wearing bad code, and only the code needs to go.

**Rejected:** full greenfield — 2–4 months before parity, with nothing showable meanwhile,
which directly conflicts with the portfolio goal. Strangler-fig — better practice, but the
frontend is being wholly replaced anyway, so incrementalism buys little.

---

## D2 — MIT → FSL-1.1-Apache-2.0

**Decision:** relicense before the rewrite.

**Why:** the repo is public and on a resume, and that's fine — reading the code isn't the
threat. But MIT *explicitly grants* anyone the right to take it, close it, rebrand it, and
sell it. FSL is source-available and non-compete, auto-converting to Apache-2.0 after two
years. Recruiters read it identically to open source; commercial free-riders cannot use it.

**Timing:** trivial at 49 commits with a sole author. Effectively impossible once there
are outside contributors.

---

## D3 — One monorepo

**Decision:** `apps/{api,web,site}` + `packages/{api-client,ui}` + `infra/` + `docs/`.
Not three repos.

**Why:**
1. The API contract is the highest-traffic seam. Across repos, every shape change becomes
   change → merge → publish client → bump → merge. That friction ends with people giving up
   and typing `any`.
2. Portfolio math: one repo is one README and one architecture story. Three repos means a
   reviewer lands on a backend with no frontend and leaves.
3. Polyrepo solves *organizational* problems — separate teams, cadences, on-call. None
   apply to one person.

Independent deploys come from CI path filters, not separate repos.

`api` and `worker` are **one package, two entrypoints** — they share models, session, and
orchestrator. The existing docker-compose already got this right.

---

## D4 — Rsbuild SPA for the product, Next for the public site

**Decision:** `apps/web` = Rsbuild + React 19 + TanStack Router + TanStack Query.
`apps/site` = Next.

**Why the split is right:** the current frontend is ~100% `'use client'` — already an SPA,
paying Next's full complexity budget for none of its benefits. An authenticated dashboard
with Monaco, Sandpack, and mermaid has no SEO or TTFB requirement and heavy interactivity.
Public tutorials have the exact opposite profile.

**Why Rsbuild, not raw Rspack:** Rspack is a bundler, not an app toolchain. Rsbuild is the
batteries-included layer over it from the same team. Hand-written Rspack config is a file
you maintain forever instead of shipping.

**Honest note:** at 14k LOC, Rspack-vs-Vite build speed is noise. This was a
taste-and-learning choice, chosen knowingly.

**Accepted cost:** leaving Next means server-side auth enforcement disappears. That's
acceptable **only** because the backend is the sole authority — frontend route guards are
UX, never security. Stated explicitly because the old code hand-decoded JWTs in three
places to make access decisions.

---

## D5 — Keep FastAPI and ARQ; fix what's under them

**Decision:** no framework migration. Async SQLAlchemy + asyncpg, pydantic-settings,
Alembic, uv.

**Why:** nothing wrong with FastAPI here, and its OpenAPI output feeds the generated TS
client (D6). The defects were never the framework: sync ORM inside `async def`, config read
from the wrong env var with a silent hardcoded fallback, no migrations at all.

**On the job runner** — considered Temporal and Hatchet. Chose to *finish building* what
the schema already implies, on ARQ.

Reasoning specific to the goals: an LLM pipeline where each step costs money and takes 30+
seconds is the ideal teaching case for durable execution. Building checkpointing,
idempotency, and resume yourself means understanding the problem. Importing Temporal means
understanding its API. For a portfolio piece the first is worth more and interviews better.

**Constraint that makes this reversible:** steps are pure `(typed in) → (typed out)` with
side effects isolated, so swapping to a real engine later is a week's work. That seam
matters more than the runner choice.

---

## D6 — Generated API client

**Decision:** `packages/api-client` generated from FastAPI's OpenAPI schema in CI.

**Why:** frontend types become *derived* from the backend rather than maintained in
parallel. Kills the `as unknown as T` casts caused by `apiClient` unwrapping `response.data`
inside an interceptor, which made every call site's declared type a lie.

Only cheap because of D3.

---

## D7 — BYOK free and unlimited; no paid tier in Phase 1

**Decision:** BYOK unrestricted. 5 lifetime free platform generations as a demo path.
No paid tier, no ads. Credit ledger and Stripe customer schema built but dormant.

**The reframe that produced this:** BYOK looks like lost revenue. It's **avoided cost**.
What kills solo AI products is inference bills arriving before revenue. Under BYOK a user
costs a Postgres row and some CPU — which is what makes thousands of engaged free users
affordable on no budget. That was the stated goal: engagement first, money later.

**On ads:** rejected. At this traffic level they earn single digits monthly and actively
signal "abandoned side project" in a developer tool. Negative on both axes.

**Eventual paywall (Phase 2+):** private repos → private tutorials. GitHub's own model.
Needs no new architecture, because D8 builds the visibility model now.

---

## D8 — Public tutorials, in `apps/site`, read-only

**Decision:** `Tutorial.visibility` from migration #1. Public pages at `/t/[slug]` in Next
with ISR. Progress, quizzes, and runnable Sandpack are the login boundary.

**Why public at all:** it's the only organic growth channel in a plan with no ads and no
paid tier — and it makes the product demoable **without signup**, which is worth more for
the portfolio goal than the rest of the refactor combined.

**Why `apps/site` and not `apps/web`:** an SPA renders an empty div to a crawler. Public
tutorials in the SPA would be invisible to Google, deleting the entire reason for having them.

**Why retrofit is expensive (so: now):** adding public content later means simultaneously
touching the auth model (anonymous reads), the router, the schema (visibility + slugs,
backfilled), and `apps/site`. Now it's a column and a route.

**Never gate the content.** A crawler that sees a wall doesn't index. Low conversion from
public readers is the funnel working — they cost nothing (static CDN) and they're why the
page ranks at all. The conversion hook is *generating your own*, not reading someone else's.

**Sandpack:** static on public pages, runnable behind login. Heavy JS would hurt the Core
Web Vitals the SEO play depends on.

---

## D9 — BYOK credential storage

**Decision:** own table, AES-256-GCM, per-row nonce, versioned KEK from Railway variables.
Credential resolved at call time; **structurally barred from step context**.

**Constraint that killed the easy answer:** "never store it, keep it in the browser" fails
because generation is a background job running minutes after the request returned. The
worker needs the credential. So the question was only *how long* and *how protected*.

**The code-specific trap:** `TutorialStepExecution.input_data` stores the whole accumulating
context dict. If the key ever entered step context it would be written to Postgres in
plaintext, permanently, in a table nobody reads. Hence: steps receive `user_id`; the AI
client resolves the credential and never returns it. A structural guarantee, not a
discipline — the only kind that survives.

**`key_version` from day one** so KMS envelope encryption later is a migration, not a rewrite.

**"Remember my key" opt-out**, Redis + TTL for those who decline. One extra code path, real
credibility with exactly the audience this product targets.

---

## D10 — GitHub OAuth as primary login

**Decision:** OAuth alongside password auth. GitHub only — **not** Google.

**Why:** it is signup, private-repo cloning, and the future paid feature in one system.
The paid feature and the auth work are the same work.

### D10a — GitHub over Google (2026-07-21)

Reconsidered mid-Phase-2. Confirmed GitHub.

Google provides identity and nothing else. The Phase 2 paywall is private repos → private
tutorials (D8), and cloning a private repo needs a GitHub token — so choosing Google means
building **two** OAuth integrations (Google to log in, GitHub for repos) where GitHub alone
is one. Every user is a developer submitting GitHub URLs; the coverage argument for Google
does not apply.

**Incremental authorization** answers the real objection, which is that asking for `repo`
scope at signup reads as "this app wants access to all my code":

| Step | Scope | When |
|---|---|---|
| Sign up | `read:user user:email` | Login |
| Connect repos | `repo` | Only when a private repo is first used |

The alarming consent screen appears only after the user has decided they want the feature.

**Revisit if:** signup analytics show users bouncing off the GitHub consent screen, or the
audience broadens past developers. Note that anonymous readers of public tutorials need no
account at all, so that audience does not by itself justify Google.

### D10b — OAuth deferred (2026-07-21)

Password auth is converted, tested and sufficient. OAuth is purely additive: `hashed_password`
is already nullable and `get_current_user_async` does not care how a session was created, so
it slots in later with no rework. The `repo` slice is on the critical path (unguarded repo
cloning, SSRF) and needs no external setup, so it goes first.

---

## D11 — Railway

**Decision:** Railway for Phase 1. Managed Postgres + Redis, real secrets handling.

**Why not AWS:** two weeks of IAM instead of shipping, at zero users. Move when there's a
reason.

---

## Open

- History scrub of `.env.bak` (`git filter-repo`) — rotation makes the leaked values inert,
  so this is optional hygiene.

## Resolved

- **Deployment status** (2026-07-21): not deployed anywhere, no production data. The rewrite
  has no cutover constraint — no backup, no data migration, no dual-running period. This is
  why the plan can move the schema freely in Phase 2 (D1 keeps the *design*, not the rows).
