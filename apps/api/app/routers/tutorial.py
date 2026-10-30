"""Tutorial endpoints.

**Route order matters here.** Literal paths (`/generation/status`, `/explore`,
`/slug/{slug}`) are declared before `/{tutorial_id}`; FastAPI matches in
declaration order, so a literal path placed after a parameterised one is
unreachable — and for single-segment literals like `/explore`, a `/{tutorial_id}`
route declared first would *capture* the request and 422 on UUID validation.
"""

import json
import time
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..core import security
from ..core.dependencies import get_current_user_async, get_optional_user
from ..core.exceptions import AuthenticationError, ExternalServiceError
from ..core.pagination import Page, PageParams, page_params
from ..core.rate_limit import generation_rate_limited
from ..db.session import get_async_db
from ..models.user import User
from ..pipeline import events as generation_events
from ..schemas.tutorial import (
    ExploreTutorialItem,
    GenerateRequest,
    GenerateResponse,
    GenerationStatusResponse,
    StatusResponse,
    TutorialListItem,
    TutorialResponse,
    VisibilityUpdate,
)
from ..services import tutorial as tutorial_service

router = APIRouter()

# Heartbeats keep proxies/load balancers from closing an "idle" connection and
# let the client distinguish "still generating" from "connection died". A
# terminal event closes the stream; the cap below bounds the worst case so a
# wedged worker cannot hold connections open forever.
HEARTBEAT_SECONDS = 15.0
MAX_STREAM_SECONDS = 3600.0


# --- Literal paths (must precede /{tutorial_id}) ----------------------------


@router.post("/generate", response_model=GenerateResponse, status_code=status.HTTP_202_ACCEPTED)
async def generate_tutorial(
    body: GenerateRequest,
    request: Request,
    current_user: User = Depends(get_current_user_async),
    _: None = Depends(generation_rate_limited),
    db: AsyncSession = Depends(get_async_db),
):
    """Queue a tutorial generation.

    202, not 200: nothing is generated when this returns. Poll
    `/{instance_id}/status` — or better, open `/{instance_id}/stream`.
    """
    instance = await tutorial_service.start_generation(
        db,
        current_user.user_id,
        body,
        getattr(request.app.state, "redis_pool", None),
    )
    return GenerateResponse(instance_id=instance.id, status=instance.status)


@router.get("/generation/status", response_model=GenerationStatusResponse)
async def get_generation_status_by_url(
    repo_url: str = Query(..., description="Repository URL to check status for"),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Legacy polling endpoint, keyed by repo URL. Prefer `/{instance_id}/status`."""
    return await tutorial_service.get_status_by_repo_url(db, current_user.user_id, repo_url)


@router.get("/explore", response_model=Page[ExploreTutorialItem])
async def explore_tutorials(
    params: PageParams = Depends(page_params),
    language: str | None = Query(None, max_length=100, description="Filter by repository language"),
    db: AsyncSession = Depends(get_async_db),
):
    """Public catalogue for apps/site `/explore`. No authentication: this is the
    growth channel (D8), and gating it walls off the crawler too."""
    items, total = await tutorial_service.list_public_tutorials(db, params, language)
    return Page[ExploreTutorialItem].build(items, total, params)


@router.get("/slug/{slug}", response_model=TutorialResponse)
async def get_tutorial_by_slug(
    slug: str,
    db: AsyncSession = Depends(get_async_db),
):
    """Public tutorial by slug — the payload behind `/t/{slug}` on apps/site.

    Public rows only; anything else is a plain 404 so the endpoint cannot be
    used to confirm a private tutorial's slug exists.
    """
    return await tutorial_service.get_public_tutorial_by_slug(db, slug)


# --- Collection -------------------------------------------------------------


@router.get("", response_model=Page[TutorialListItem])
async def list_tutorials(
    params: PageParams = Depends(page_params),
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    items, total = await tutorial_service.list_tutorials(db, current_user.user_id, params)
    return Page[TutorialListItem].build(items, total, params)


# --- Single tutorial --------------------------------------------------------


@router.get("/{tutorial_id}", response_model=TutorialResponse)
async def get_tutorial(
    tutorial_id: UUID,
    current_user: User | None = Depends(get_optional_user),
    db: AsyncSession = Depends(get_async_db),
):
    """Read a tutorial.

    Optional auth: the owner sees their private tutorials, and anyone — signed in
    or not — can read a public or unlisted one.

    The previous version took no ownership into account *at all*. It fetched by
    primary key and returned the whole body, so any authenticated user could read
    any other user's tutorial. It also declared `response_model=Any`, so the
    schema was absent from OpenAPI and nothing constrained what came back.
    """
    return await tutorial_service.get_tutorial(
        db, tutorial_id, current_user.user_id if current_user else None
    )


@router.delete("/{tutorial_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tutorial(
    tutorial_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    await tutorial_service.delete_tutorial(db, tutorial_id, current_user.user_id)


@router.patch("/{tutorial_id}/visibility", response_model=TutorialResponse)
async def set_visibility(
    tutorial_id: UUID,
    body: VisibilityUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Publish or unpublish. Owner only — visibility is not a read operation."""
    await tutorial_service.set_visibility(db, tutorial_id, current_user.user_id, body.visibility)
    return await tutorial_service.get_tutorial(db, tutorial_id, current_user.user_id)


# --- Generation instances ---------------------------------------------------


@router.post(
    "/{instance_id}/retry",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def retry_generation(
    instance_id: UUID,
    request: Request,
    current_user: User = Depends(get_current_user_async),
    _: None = Depends(generation_rate_limited),
    db: AsyncSession = Depends(get_async_db),
):
    instance = await tutorial_service.retry_generation(
        db,
        instance_id,
        current_user.user_id,
        getattr(request.app.state, "redis_pool", None),
    )
    return GenerateResponse(instance_id=instance.id, status=instance.status)


@router.get("/{instance_id}/status", response_model=StatusResponse)
async def get_generation_status(
    instance_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await tutorial_service.get_generation_status(db, instance_id, current_user.user_id)


@router.get("/{instance_id}/result")
async def get_generation_result(
    instance_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Raw pipeline output. Internal; use `GET /{tutorial_id}` to read a tutorial."""
    return await tutorial_service.get_generation_result(db, instance_id, current_user.user_id)


# --- Generation event stream (4.8) -------------------------------------------


@router.get("/{instance_id}/stream")
async def stream_generation(
    instance_id: UUID,
    request: Request,
    ticket: str = Query(
        ...,
        description="Short-lived stream ticket from the status payload's `stream_ticket`.",
    ),
):
    """Server-Sent Events feed of pipeline step transitions.

    **Auth is a ticket, not a header, on purpose.** `EventSource` cannot set an
    Authorization header, and one-off `fetch`-based polyfills give up
    auto-reconnect, which is most of the value of SSE. Instead the client takes
    `stream_ticket` from an already-authenticated `GET /{instance_id}/status`
    response and passes it here as a query parameter. The ticket is a JWT bound
    to this instance *and* user, expires in `stream_ticket_expire_seconds` (120s
    by default), and carries type `stream_ticket` — never accepted as a session
    token, and a session token is never accepted as a ticket.

    Rate limiting is deliberately not applied to this endpoint: it produces no
    LLM work, and throttling heartbeats would break live updates. The
    work-producing endpoints (`/generate`, `/{id}/retry`) are limited instead.

    One caveat accepted and documented (docs/adr/): a ticket in a URL can leak
    via referrer headers. The short expiry is the mitigation — a leaked URL is
    dead in two minutes and only ever exposes step transitions, never content.
    """
    ticket_data = security.decode_stream_ticket(ticket)
    if ticket_data is None or ticket_data.instance_id != str(instance_id):
        # Same message for "expired" and "forged": no information either way.
        raise AuthenticationError("Invalid or expired stream ticket.")

    pool = getattr(request.app.state, "redis_pool", None)
    if pool is None:
        raise ExternalServiceError("Live status is unavailable. Poll the status endpoint.")

    return StreamingResponse(
        _generation_event_stream(request, pool, str(instance_id)),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            # Nginx buffers responses by default, which turns a stream into one
            # lump at the end. This header disables it.
            "X-Accel-Buffering": "no",
        },
    )


async def _generation_event_stream(request: Request, pool, instance_id: str):
    """Yield SSE frames from the instance's Redis pub/sub channel until a
    terminal event, a disconnect, or the duration cap."""
    pubsub = pool.pubsub()
    await pubsub.subscribe(generation_events.channel_for(instance_id))
    started = time.monotonic()
    try:
        yield f'event: connected\ndata: {{"instance_id": "{instance_id}"}}\n\n'

        while True:
            # Checked between events, not concurrently: get_message's timeout
            # bounds how long a dead connection goes unnoticed.
            if await request.is_disconnected():
                return
            if time.monotonic() - started > MAX_STREAM_SECONDS:
                yield ": stream duration cap reached; poll the status endpoint\n\n"
                return

            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=HEARTBEAT_SECONDS
            )
            if message is None or message.get("data") is None:
                # Comment-frame heartbeat: invisible to EventSource's event
                # dispatch but proves the transport is alive.
                yield ": heartbeat\n\n"
                continue

            raw = message["data"]
            if isinstance(raw, bytes):
                raw = raw.decode("utf-8", errors="replace")
            try:
                payload = json.loads(raw)
            except (TypeError, ValueError):
                continue

            event_type = str(payload.get("type", "message"))
            yield f"event: {event_type}\ndata: {json.dumps(payload)}\n\n"
            if event_type in generation_events.TERMINAL_EVENTS:
                return
    finally:
        # Clean disconnect handling: the subscription must not outlive the
        # response, or every closed tab leaks a Redis subscription.
        try:
            await pubsub.unsubscribe(generation_events.channel_for(instance_id))
            await pubsub.aclose()
        except Exception:  # noqa: S110 - shutdown of a dead connection
            pass
