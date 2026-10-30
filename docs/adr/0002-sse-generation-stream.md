# ADR 0002 — Generation status via SSE, authenticated by a short-lived ticket

Date: 2026-10-29 · Status: Accepted · Decides: Phase 4.8

## Context

Generation status is polled (`GET /{instance_id}/status`). The plan called for
SSE instead. Two constraints shaped everything:

- The pipeline runs in the ARQ **worker**; the API process has no in-process
  view of step transitions. Some cross-process channel is required.
- `EventSource` cannot send an `Authorization` header.

## Decision

**Transport: Redis pub/sub, fan-out per instance.** The worker publishes step
transitions (`step_started`, `step_completed`, `failed`, `completed`) to
`generation:{instance_id}`; the API's SSE endpoint subscribes per connection and
forwards frames. Pub/sub, not a Redis stream: subscribers only care about
transitions happening while connected, and the polling status endpoint remains
the source of truth for anything that happened before they connected.
Fire-and-forget is exactly the right durability — nobody replays step events.

**Auth: a signed ticket from the status payload.** The client first calls the
already-authenticated `GET /{instance_id}/status`, whose response now carries a
`stream_ticket` — a JWT (`type: stream_ticket`) bound to the instance *and*
user, expiring in `stream_ticket_expire_seconds` (120s). The stream endpoint
accepts it as a query parameter.

Why a ticket and not the alternatives:

- *Session token in the query string* — leaks via referrer/logs and lives 30
  minutes; a ticket leaks the same way but is dead in two minutes and only
  ever exposes step transitions.
- *Cookie auth* — would work, but this app's auth is header-token based; adding
  a parallel cookie mechanism for one endpoint is a second auth model, not a fix.
- *One-time tickets* — need a store; a stateless JWT needs none.

The ticket type is disjoint from session tokens in both directions (a stream
ticket is never accepted as an access token and vice versa), enforced by the
`type` claim in `core/security.py`.

**Lifecycle.** Heartbeat comment frames every 15s (proxies close "idle"
connections; the client must distinguish "still generating" from "dead socket").
A terminal event (`completed`/`failed`) closes the stream server-side. A hard
cap (1h) bounds the worst case of a wedged worker. Disconnection is detected
between events and the pub/sub subscription is always released.

**Rate limiting deliberately excludes this endpoint** (see ADR 0003): it
produces no LLM work.

## Consequences

- The client keeps polling as a fallback for reconnects; SSE is an upgrade, not
  a replacement. Nothing breaks if Redis pub/sub is unavailable — the stream
  endpoint returns 502 and the client falls back to polling.
- Publishing is best-effort: a failed publish is logged and never fails a
  generation that already spent real tokens.
