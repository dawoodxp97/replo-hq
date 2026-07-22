"""Outbound URL validation.

BYOK lets a user supply their own `base_url` so they can point at any
OpenAI-compatible endpoint (LiteLLM, a gateway, a self-hosted runtime). That URL
is then fetched **by the server**, which makes it the second SSRF surface in the
product — the first being `git clone`, handled in `utils/repo_utils.py`.

It was unvalidated. `services/credentials.py::validate_credential` would issue a
GET to whatever was stored, and return the status code to the caller:

    base_url = "http://169.254.169.254/latest/meta-data"   → cloud metadata
    base_url = "http://127.0.0.1:6379"                     → our Redis
    base_url = "http://10.0.0.5/admin"                     → anything internal

Reporting "Provider returned HTTP 401" versus a timeout turns that into a port
scanner with a readable oracle.

## What is enforced

https only, no embedded credentials, and every address the hostname resolves to
must be a public unicast address. Checking *all* resolved addresses matters: a
name with both a public A record and a private AAAA record would otherwise pass
on the public one and connect over the private one.

## What is not

**DNS rebinding.** The name is resolved here and again by the HTTP client when it
connects, and a hostile resolver can answer differently the second time. Closing
that requires pinning the validated address into the connector. The mitigations
in place are that redirects are disabled at the call site (otherwise a public
host can simply 302 to a private one, which needs no rebinding at all) and that
response bodies are never returned to the caller.
"""

import ipaddress
import socket
from urllib.parse import urlparse

from .exceptions import InvalidInputError

ALLOWED_SCHEMES = frozenset({"https"})


def _is_public(address: str) -> bool:
    ip = ipaddress.ip_address(address)
    # `is_global` alone is not sufficient: it does not exclude every reserved
    # range, and the loopback/link-local checks are what block 127.0.0.1 and the
    # 169.254.169.254 metadata endpoint specifically.
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def validate_outbound_url(raw_url: str, *, field: str = "base_url") -> str:
    """Validate a user-supplied URL the server will fetch. Returns it normalised.

    Blocking: `getaddrinfo` hits the resolver. Call it from a worker thread if
    the calling path is latency-sensitive; credential validation already makes a
    network request, so one more resolve is not the cost that matters there.
    """
    url = (raw_url or "").strip().rstrip("/")
    if not url:
        raise InvalidInputError(f"{field} must not be empty.")

    parsed = urlparse(url)

    if parsed.scheme not in ALLOWED_SCHEMES:
        raise InvalidInputError(
            f"{field} must start with https:// — plain http would send your API key "
            "over an unencrypted connection."
        )

    if parsed.username or parsed.password:
        raise InvalidInputError(f"{field} must not contain credentials.")

    host = parsed.hostname
    if not host:
        raise InvalidInputError(f"{field} is not a valid URL.")

    try:
        infos = socket.getaddrinfo(host, parsed.port or 443, proto=socket.IPPROTO_TCP)
    except socket.gaierror as exc:
        raise InvalidInputError(f"Could not resolve the host in {field}.") from exc

    addresses = {info[4][0] for info in infos}
    if not addresses:
        raise InvalidInputError(f"Could not resolve the host in {field}.")

    for address in addresses:
        if not _is_public(address):
            # The address itself is not echoed back: on an internal name that
            # would confirm the mapping to the caller.
            raise InvalidInputError(
                f"{field} must point at a publicly reachable host. Private, loopback "
                "and link-local addresses are not allowed."
            )

    return url
