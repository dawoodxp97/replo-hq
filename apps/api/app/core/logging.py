"""Logging setup, including secret redaction.

Encrypting credentials at rest is pointless if the plaintext then lands in a log
line on the way to the provider. The old `AIClient` built an
`Authorization: Bearer ...` header and logged error responses freely; one
`logger.error(f"...{headers}")` during debugging would have written a user's API
key to disk permanently.

`RedactingFilter` is defence in depth, not the primary control. The primary
control is not putting secrets in log calls. This exists because that rule gets
broken during a 2am debugging session.
"""

import logging
import re

from .context import get_request_id

# Ordered most-specific first so a provider-shaped key is labelled precisely
# rather than being swallowed by the generic Bearer rule.
_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # OpenRouter: sk-or-v1-<64 hex>
    (re.compile(r"sk-or-v1-[A-Za-z0-9]{16,}"), "sk-or-v1-***REDACTED***"),
    # OpenAI / Anthropic style: sk-... and sk-ant-...
    (re.compile(r"sk-ant-[A-Za-z0-9\-_]{16,}"), "sk-ant-***REDACTED***"),
    (re.compile(r"sk-[A-Za-z0-9\-_]{16,}"), "sk-***REDACTED***"),
    # GitHub tokens (ghp_, gho_, ghu_, ghs_, ghr_) — relevant once OAuth lands.
    (re.compile(r"gh[pousr]_[A-Za-z0-9]{16,}"), "gh*_***REDACTED***"),
    # Any Authorization header value, however it was formatted.
    (re.compile(r"(?i)(authorization\"?\s*[:=]\s*\"?)(bearer\s+)?\S+"), r"\1***REDACTED***"),
    (re.compile(r"(?i)bearer\s+[A-Za-z0-9\-._~+/]{16,}=*"), "Bearer ***REDACTED***"),
    # Postgres/Redis URLs carrying inline credentials.
    (re.compile(r"(?i)(postgres(?:ql)?|redis)://([^:/@\s]+):([^@\s]+)@"), r"\1://\2:***@"),
]


def redact(text: str) -> str:
    for pattern, replacement in _PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class RedactingFilter(logging.Filter):
    """Scrubs secret-shaped substrings from messages and args.

    Returns True always — this filter rewrites, it never drops records. A
    dropped log line during an incident is worse than a redacted one.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = redact(record.msg)

        if record.args:
            if isinstance(record.args, dict):
                record.args = {
                    k: redact(v) if isinstance(v, str) else v for k, v in record.args.items()
                }
            else:
                record.args = tuple(redact(a) if isinstance(a, str) else a for a in record.args)

        # Exception text is a common leak path: a provider client that raises
        # with the request URL attached puts a query-string token in the trace.
        if record.exc_info and record.exc_info[1] is not None:
            exc = record.exc_info[1]
            if exc.args and isinstance(exc.args[0], str):
                exc.args = (redact(exc.args[0]), *exc.args[1:])

        return True


class RequestIDFilter(logging.Filter):
    """Attach the current request id to every record.

    Set unconditionally — including to '-' outside a request — because a format
    string referencing a missing attribute raises during logging, which is a
    spectacularly annoying way to lose logs in the worker.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = get_request_id() or "-"
        return True


def configure_logging(level: int = logging.INFO) -> None:
    """Install redaction and request-id filters on the root handlers.

    Filters attached to a *logger* do not apply to records propagated from child
    loggers — attaching them to the handlers is what makes this process-wide.
    """
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(request_id)s] %(name)s %(levelname)s %(message)s",
    )

    filters: list[logging.Filter] = [RequestIDFilter(), RedactingFilter()]
    for handler in logging.getLogger().handlers:
        for f in filters:
            handler.addFilter(f)

    # uvicorn installs its own handlers that bypass the root logger's, so the
    # filters have to be attached there too or its output escapes unredacted.
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        for handler in logging.getLogger(name).handlers:
            for f in filters:
                handler.addFilter(f)

    # RequestIDMiddleware already logs every request *with* a request id, so
    # uvicorn's access log is a second, less useful copy of the same lines.
    # Raised to WARNING rather than disabled, so uvicorn can still report
    # problems it alone knows about.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
