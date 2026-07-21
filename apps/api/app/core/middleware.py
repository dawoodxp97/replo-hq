"""HTTP middleware.

Request IDs are the thing that turns "a user says it broke" into "here is the
exact request". Every log line, every error body, and every response carries the
same id.
"""

import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

from .context import set_request_id

logger = logging.getLogger("app.access")

REQUEST_ID_HEADER = "X-Request-ID"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Assign or propagate a request id, then log the outcome.

    An inbound `X-Request-ID` is honoured so a trace survives across services and
    from a frontend that generates its own — otherwise one request produces two
    unrelated ids and correlating them by hand is miserable.
    """

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get(REQUEST_ID_HEADER) or uuid.uuid4().hex
        set_request_id(request_id)
        request.state.request_id = request_id

        started = time.perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            # The exception handlers build the response body; this only records
            # timing and re-raises so the outcome is never silently missing from
            # the access log.
            duration_ms = (time.perf_counter() - started) * 1000
            logger.exception(
                "%s %s -> unhandled in %.1fms", request.method, request.url.path, duration_ms
            )
            raise

        duration_ms = (time.perf_counter() - started) * 1000
        response.headers[REQUEST_ID_HEADER] = request_id

        # Path only, never the query string — it can carry tokens and ids we
        # would rather not persist in access logs.
        logger.info(
            "%s %s -> %s in %.1fms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
