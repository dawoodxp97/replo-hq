# ADR 0003 — Rate limiting: fixed-window counters in Redis, fail open

Date: 2026-10-29 · Status: Accepted · Decides: Phase 3.12 (deferred)

## Context

Signup/login needed rate limiting (the signup email-existence check is a
documented enumeration oracle; `services/auth.py` mitigates with a message, and
expected the endpoint to be throttled). Generation start/retry needed a cap —
each run costs real LLM tokens, and a loop or a double-click spends money.

## Decision

**Algorithm: fixed window, `INCR` + `EXPIRE`.** Two round trips, one key per
`(scope, identity, window-start)`. Sliding-window/token-bucket smooth the
burst at window edges, but the threat here is a *loop*, not traffic shaping;
the simpler mechanism wins. Limits are config-driven
(`auth_rate_limit_per_minute`, `generation_rate_limit_per_hour`) and each rule
is a `RateLimitRule` value, so a new limit is a new value, not new code.

**Identifier: IP for auth, user id for generation.** Auth callers are not
authenticated; the socket peer is used rather than `X-Forwarded-For`, which a
client controls when there is no trusted proxy. Generation limits are per user
— the account that would burn the tokens.

**Response: 429 + `Retry-After`.** Rendered by the shared `AppError` handler
from `RateLimitError.details["retry_after"]` — every 429 in the product carries
the header through one code path.

**Fail open.** If Redis is unreachable the limiter does nothing and logs a
warning. Deliberately asymmetric with `_enqueue` in `services/tutorial.py`,
which fails *closed*: a generation silently never queued is a correctness bug,
while a skipped counter is only a missed protection. Making the limiter a hard
dependency would let a Redis blip take the whole product down.

**Scope of application.** `POST /api/user/signup`, `POST /api/user/login`,
`POST /api/tutorial/generate`, `POST /api/tutorial/{id}/retry`. The SSE stream
endpoint is excluded — it produces no work, and throttling heartbeats breaks
live updates for exactly the users most worth protecting.

## Consequences

- A burst at a window boundary can admit up to 2× the limit in a short period.
  Accepted; revisit per-rule only if a limit ever matters financially.
- The counters are opaque keys with TTLs; no cleanup job, no persistence.
