"""Typed application errors and their HTTP rendering.

Replaces `raise HTTPException(status_code=404, detail="...")` scattered through
routers. Two reasons that pattern hurts:

1. Services cannot raise it without importing FastAPI, which couples domain logic
   to the transport. A service should be callable from a worker, a CLI, or a test
   without HTTP being involved.
2. Every endpoint invents its own error body, so clients cannot handle failures
   generically.

Everything here is transport-agnostic; `register_exception_handlers` is the only
part that knows about HTTP.

## On leaking existence

`NotFoundError` is raised for "does not exist" **and** for "exists but is not
yours". Returning 403 for the second case tells an attacker the id is real,
turning a guessable id into an enumeration oracle. The ownership helpers in
`app/core/ownership.py` therefore raise `NotFoundError`, never
`PermissionDeniedError`.

`PermissionDeniedError` is for cases where the caller is *known* to have access
to the object but not to the operation — a role check, not an ownership check.
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from .context import get_request_id

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base for every deliberate application failure."""

    status_code: int = 500
    code: str = "internal_error"
    default_message: str = "Something went wrong."

    def __init__(self, message: str | None = None, *, details: dict[str, Any] | None = None):
        self.message = message or self.default_message
        self.details = details or {}
        super().__init__(self.message)


class NotFoundError(AppError):
    status_code = 404
    code = "not_found"
    default_message = "The requested resource was not found."


class PermissionDeniedError(AppError):
    """Caller may see the object but not perform this operation."""

    status_code = 403
    code = "permission_denied"
    default_message = "You do not have permission to perform this action."


class AuthenticationError(AppError):
    status_code = 401
    code = "unauthenticated"
    default_message = "Authentication required."


class ConflictError(AppError):
    status_code = 409
    code = "conflict"
    default_message = "That conflicts with something that already exists."


class InvalidInputError(AppError):
    """Semantic validation, past the point Pydantic can help."""

    status_code = 422
    code = "invalid_input"
    default_message = "The request was not valid."


class RateLimitError(AppError):
    status_code = 429
    code = "rate_limited"
    default_message = "Too many requests. Please slow down."


class ExternalServiceError(AppError):
    """An upstream we depend on failed — the LLM provider, GitHub, Stripe.

    502 rather than 500: the distinction between "we are broken" and "someone we
    call is broken" is the first thing you want when reading an alert.
    """

    status_code = 502
    code = "upstream_error"
    default_message = "An upstream service failed."


class CredentialError(AppError):
    status_code = 400
    code = "credential_error"
    default_message = "There is a problem with the configured API credential."


def _body(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    """One error shape for every failure, so clients can handle them generically.

    `request_id` is included so a user can quote it in a bug report and it can be
    grepped straight out of the logs.
    """
    payload: dict[str, Any] = {
        "error": {
            "code": code,
            "message": message,
            "request_id": get_request_id(),
        }
    }
    if details:
        payload["error"]["details"] = details
    return payload


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(request: Request, exc: AppError) -> JSONResponse:
        # 5xx is our fault and needs a stack trace; 4xx is the caller's and would
        # only be noise at ERROR level.
        if exc.status_code >= 500:
            logger.exception("%s: %s", exc.code, exc.message)
        else:
            logger.info("%s: %s", exc.code, exc.message)
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(exc.code, exc.message, exc.details),
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
        # Normalised into the same envelope as everything else. FastAPI's default
        # body is a bare `{"detail": [...]}`, which is a second shape clients
        # would otherwise have to special-case.
        return JSONResponse(
            status_code=422,
            content=_body(
                "invalid_input",
                "The request was not valid.",
                {"fields": jsonable_errors(exc)},
            ),
        )

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        # Covers HTTPExceptions still raised by unconverted routers, plus 404s
        # raised by the router itself for unknown paths.
        return JSONResponse(
            status_code=exc.status_code,
            content=_body(f"http_{exc.status_code}", str(exc.detail)),
        )

    @app.exception_handler(Exception)
    async def _unhandled(request: Request, exc: Exception) -> JSONResponse:
        # Never surface the exception text: it routinely contains connection
        # strings, SQL, or upstream payloads. The request_id is the bridge
        # between what the user sees and the full trace in the logs.
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content=_body("internal_error", "Something went wrong on our end."),
        )


def jsonable_errors(exc: RequestValidationError) -> list[dict[str, Any]]:
    """Trim Pydantic's error list to what a client can act on."""
    out: list[dict[str, Any]] = []
    for err in exc.errors():
        out.append(
            {
                # Drop the leading "body"/"query" segment — the caller knows
                # where they put it.
                "field": ".".join(str(p) for p in err.get("loc", ())[1:]) or "body",
                "message": err.get("msg", "invalid"),
                "type": err.get("type", "invalid"),
            }
        )
    return out
