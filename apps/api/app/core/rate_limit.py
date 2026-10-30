"""Redis-backed fixed-window rate limiting (Phase 3.12).

Scope: `POST /api/user/signup`, `POST /api/user/login` (per client IP) and
`POST /api/tutorial/generate` + `POST /api/tutorial/{id}/retry` (per user).
The SSE stream endpoint is deliberately **not** rate limited — a heartbeat
connection is not a work-producing request, and throttling it would break
live updates for exactly the users most worth protecting.

## Why fixed window

`INCR` + `EXPIRE` is two Redis round trips and one key per (scope, identity,
window). Sliding-window or token-bucket gives smoother edges at the cost of
sorted sets and Lua scripts. For limits of "tens per hour" the burst at a
window boundary is acceptable; the point is to stop a loop, not to shape traffic.

## Fail open

When Redis is unreachable the limiter does nothing rather than rejecting every
request. Rate limiting protects the LLM budget and the auth endpoints; turning
it into a hard dependency means a Redis blip takes the whole product down, which
is a strictly worse failure. Logged at WARNING so an operator can see it.

Note the asymmetry with `_enqueue` in services/tutorial.py, which fails *closed*
on a missing Redis pool: a job silently not queued is a correctness bug, a
skipped counter is not.
"""

import logging
import time
from dataclasses import dataclass

from fastapi import Depends, Request

from .config import settings
from .dependencies import get_current_user_async
from .exceptions import RateLimitError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RateLimitRule:
    """One limit. `scope` namespaces the Redis keys so auth and generation
    counters can never collide."""

    scope: str
    limit: int
    window_seconds: int


def auth_rule() -> RateLimitRule:
    """Signup/login. Per client IP — the caller is not authenticated yet."""
    return RateLimitRule("auth", settings.auth_rate_limit_per_minute, 60)


def generation_rule() -> RateLimitRule:
    """Generation starts and retries. Per user — that is the account that would
    burn LLM tokens."""
    return RateLimitRule("generation", settings.generation_rate_limit_per_hour, 3600)


def _key(rule: RateLimitRule, identifier: str, now: int) -> str:
    """Key includes the window start so an old key is simply never touched again
    and no reset logic is needed."""
    window_start = now - (now % rule.window_seconds)
    return f"ratelimit:{rule.scope}:{identifier}:{window_start}"


async def check_rate_limit(pool, rule: RateLimitRule, identifier: str) -> int:
    """Count one hit against `rule` for `identifier`.

    Returns 0 when allowed, or the number of seconds after which the caller may
    retry. Never raises for infrastructure problems — see module docstring.
    """
    if not settings.rate_limit_enabled:
        return 0
    if pool is None:
        logger.warning("Rate limiter has no Redis pool; skipping (fail open).")
        return 0

    now = int(time.time())
    key = _key(rule, identifier, now)
    try:
        count = await pool.incr(key)
        if count == 1:
            # nx=True: two concurrent first hits must not shrink the TTL.
            await pool.expire(key, rule.window_seconds, nx=True)
    except Exception:
        logger.exception("Rate limiter could not reach Redis; skipping (fail open).")
        return 0

    if count > rule.limit:
        # Retry-After rounded up so a client that sleeps exactly that long is
        # past the window when it returns.
        return rule.window_seconds - (now % rule.window_seconds) + 1
    return 0


async def enforce_rate_limit(pool, rule: RateLimitRule, identifier: str) -> None:
    """Raise `RateLimitError` (429 + Retry-After) when the caller is over limit."""
    retry_after = await check_rate_limit(pool, rule, identifier)
    if retry_after:
        raise RateLimitError(
            "Too many requests. Try again later.",
            details={"retry_after": retry_after},
        )


def _client_ip(request: Request) -> str:
    # Not X-Forwarded-For: behind no trusted proxy that header is client-chosen
    # and defeats the limit entirely. `request.client.host` is the socket peer.
    return request.client.host if request.client else "unknown"


async def auth_rate_limited(request: Request) -> None:
    """Dependency for the auth endpoints. Per client IP."""
    pool = getattr(request.app.state, "redis_pool", None)
    await enforce_rate_limit(pool, auth_rule(), _client_ip(request))


async def generation_rate_limited(
    request: Request,
    current_user=Depends(get_current_user_async),
) -> None:
    """Dependency for the generation endpoints. Per user.

    Depends on `get_current_user_async` itself: FastAPI caches dependency
    results within a request, so the endpoint's own `current_user` dependency
    resolves to the same object and the token is decoded exactly once.
    """
    pool = getattr(request.app.state, "redis_pool", None)
    await enforce_rate_limit(pool, generation_rule(), str(current_user.user_id))
