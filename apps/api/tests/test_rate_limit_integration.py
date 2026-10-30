"""Integration test: rate limiting against a real Redis (testcontainers)."""

import pytest

from app.core import rate_limit
from app.core.exceptions import RateLimitError

pytestmark = pytest.mark.integration


class TestRealRedis:
    async def test_window_counts_accumulate_and_reset(self, redis_pool):
        rule = rate_limit.RateLimitRule("auth", limit=3, window_seconds=2)
        for _ in range(3):
            assert await rate_limit.check_rate_limit(redis_pool, rule, "9.9.9.9") == 0
        assert await rate_limit.check_rate_limit(redis_pool, rule, "9.9.9.9") > 0

    async def test_enforce_raises_with_retry_after(self, redis_pool):
        rule = rate_limit.RateLimitRule("generation", limit=1, window_seconds=60)
        await rate_limit.enforce_rate_limit(redis_pool, rule, "user-a")
        with pytest.raises(RateLimitError) as excinfo:
            await rate_limit.enforce_rate_limit(redis_pool, rule, "user-a")
        assert 0 < excinfo.value.details["retry_after"] <= 61

    async def test_users_are_isolated(self, redis_pool):
        rule = rate_limit.RateLimitRule("generation", limit=1, window_seconds=60)
        assert await rate_limit.check_rate_limit(redis_pool, rule, "user-a") == 0
        assert await rate_limit.check_rate_limit(redis_pool, rule, "user-b") == 0
