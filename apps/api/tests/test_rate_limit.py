"""Rate limiter tests.

`check_rate_limit` runs against a minimal in-memory stand-in for the Redis
client, so the window logic is testable without Docker. The integration suite
additionally covers a real Redis (tests/test_rate_limit_integration.py).
"""

import pytest

from app.core import rate_limit
from app.core.exceptions import RateLimitError


class FakeRedis:
    """Just enough of redis.asyncio for the limiter: INCR + EXPIRE."""

    def __init__(self):
        self.counters: dict[str, int] = {}
        self.ttls: dict[str, int] = {}

    async def incr(self, key: str) -> int:
        self.counters[key] = self.counters.get(key, 0) + 1
        return self.counters[key]

    async def expire(self, key: str, seconds: int, nx: bool = False) -> None:
        if nx and key in self.ttls:
            return
        self.ttls[key] = seconds


class FailingRedis(FakeRedis):
    async def incr(self, key: str) -> int:
        raise ConnectionError("redis down")


@pytest.fixture(autouse=True)
def _enable(monkeypatch):
    monkeypatch.setattr("app.core.config.settings.rate_limit_enabled", True)


@pytest.fixture(autouse=True)
def _fixed_window(monkeypatch):
    monkeypatch.setattr(rate_limit.time, "time", lambda: 10_000)
    return 10_000


class TestWindowLogic:
    async def test_under_limit_is_allowed(self):
        rule = rate_limit.RateLimitRule("auth", limit=3, window_seconds=60)
        fake = FakeRedis()
        for _ in range(3):
            assert await rate_limit.check_rate_limit(fake, rule, "1.2.3.4") == 0

    async def test_over_limit_returns_retry_after(self):
        rule = rate_limit.RateLimitRule("auth", limit=2, window_seconds=60)
        fake = FakeRedis()
        await rate_limit.check_rate_limit(fake, rule, "1.2.3.4")
        await rate_limit.check_rate_limit(fake, rule, "1.2.3.4")
        retry_after = await rate_limit.check_rate_limit(fake, rule, "1.2.3.4")

        # Window started at 10_000 - (10_000 % 60); retry lands past its end.
        assert 0 < retry_after <= 61

    async def test_identifier_isolation(self):
        rule = rate_limit.RateLimitRule("auth", limit=1, window_seconds=60)
        fake = FakeRedis()
        assert await rate_limit.check_rate_limit(fake, rule, "1.1.1.1") == 0
        assert await rate_limit.check_rate_limit(fake, rule, "2.2.2.2") == 0
        assert await rate_limit.check_rate_limit(fake, rule, "1.1.1.1") > 0

    async def test_scope_isolation(self):
        rule = rate_limit.RateLimitRule("auth", limit=1, window_seconds=60)
        other = rate_limit.RateLimitRule("generation", limit=1, window_seconds=60)
        fake = FakeRedis()
        assert await rate_limit.check_rate_limit(fake, rule, "u1") == 0
        # Same identifier, different scope — a separate key.
        assert await rate_limit.check_rate_limit(fake, other, "u1") == 0

    async def test_new_window_resets_count(self, monkeypatch):
        rule = rate_limit.RateLimitRule("auth", limit=1, window_seconds=60)
        fake = FakeRedis()
        assert await rate_limit.check_rate_limit(fake, rule, "u1") == 0
        assert await rate_limit.check_rate_limit(fake, rule, "u1") > 0

        monkeypatch.setattr(rate_limit.time, "time", lambda: 10_000 + 61)
        assert await rate_limit.check_rate_limit(fake, rule, "u1") == 0


class TestFailureBehaviour:
    async def test_disabled_limiter_allows_everything(self, monkeypatch):
        monkeypatch.setattr("app.core.config.settings.rate_limit_enabled", False)
        rule = rate_limit.RateLimitRule("auth", limit=0, window_seconds=60)
        assert await rate_limit.check_rate_limit(FakeRedis(), rule, "u1") == 0

    async def test_missing_pool_fails_open(self):
        # Redis down must not take the product down (see module docstring).
        rule = rate_limit.RateLimitRule("auth", limit=1, window_seconds=60)
        assert await rate_limit.check_rate_limit(None, rule, "u1") == 0

    async def test_redis_error_fails_open(self):
        rule = rate_limit.RateLimitRule("auth", limit=1, window_seconds=60)
        assert await rate_limit.check_rate_limit(FailingRedis(), rule, "u1") == 0


class TestEnforce:
    async def test_enforce_raises_429_with_retry_after(self):
        rule = rate_limit.RateLimitRule("auth", limit=1, window_seconds=60)
        fake = FakeRedis()
        await rate_limit.enforce_rate_limit(fake, rule, "u1")

        with pytest.raises(RateLimitError) as excinfo:
            await rate_limit.enforce_rate_limit(fake, rule, "u1")
        assert excinfo.value.status_code == 429
        assert excinfo.value.details["retry_after"] > 0
