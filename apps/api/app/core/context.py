"""Per-request context, carried without threading arguments through every call.

A `ContextVar` is the correct primitive here rather than a global: asyncio copies
the context per task, so concurrent requests each see their own value. A plain
module-level variable would be shared across every in-flight request and return
whichever one wrote last.
"""

from contextvars import ContextVar

_request_id: ContextVar[str | None] = ContextVar("request_id", default=None)


def set_request_id(value: str) -> None:
    _request_id.set(value)


def get_request_id() -> str | None:
    return _request_id.get()
