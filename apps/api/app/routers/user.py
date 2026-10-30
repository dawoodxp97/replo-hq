"""User and authentication endpoints.

First converted slice. Shape to copy for the rest:
  router parses/validates HTTP -> calls a service -> shapes the response.
No ORM queries, no business rules, no HTTPException.
"""

from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..core.rate_limit import auth_rate_limited
from ..db.session import get_async_db
from ..models.enums import OAuthProvider
from ..models.user import User
from ..schemas.user import (
    OAuthAuthorizeResponse,
    RefreshTokenRequest,
    TokenWithUser,
    UserCreate,
    UserPublic,
)
from ..services import auth as auth_service
from ..services import oauth as oauth_service

router = APIRouter()


def _session_response(user: User) -> TokenWithUser:
    """One place builds the login response, so OAuth and password login cannot
    drift apart — the brief for D10 is that providers are interchangeable via
    one session module, and this function is that module's backend half."""
    tokens = auth_service.issue_tokens(user)
    return TokenWithUser(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
    _: None = Depends(auth_rate_limited),
    db: AsyncSession = Depends(get_async_db),
) -> User:
    """Register a new account.

    Password length is enforced by the schema alone — the previous version
    checked it in the schema *and* again in the handler, so the two could drift
    apart and the duplicate was dead code.

    Returns 201; the old handler created a resource and reported 200.
    """
    return await auth_service.create_user(db, user_in)


@router.post("/login", response_model=TokenWithUser)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    _: None = Depends(auth_rate_limited),
    db: AsyncSession = Depends(get_async_db),
) -> TokenWithUser:
    """Exchange credentials for a token pair.

    Still `OAuth2PasswordRequestForm` (form-encoded, `username` field) because
    that is what FastAPI's OAuth2 flow and the Swagger "Authorize" button expect,
    and what the existing frontend already sends.
    """
    user = await auth_service.authenticate(db, form_data.username, form_data.password)
    return _session_response(user)


# --- OAuth (D10) ------------------------------------------------------------


@router.get("/oauth/{provider}/authorize", response_model=OAuthAuthorizeResponse)
async def oauth_authorize(provider: OAuthProvider) -> OAuthAuthorizeResponse:
    """The provider's consent-screen URL.

    Returns JSON rather than a 302: the SPA needs the URL before it can decide
    how to open it (same window, popup), and a redirect from an API endpoint is
    awkward to consume from `fetch`.
    """
    return OAuthAuthorizeResponse(authorization_url=oauth_service.get_authorization_url(provider))


@router.get("/oauth/{provider}/callback", response_model=TokenWithUser)
async def oauth_callback(
    provider: OAuthProvider,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_async_db),
) -> TokenWithUser:
    """The URL the provider redirects back to. Exchanges `code` and issues the
    same token pair password login returns.

    This endpoint is the redirect target, so the browser lands here with the
    authorization code in the query string. `code` and `state` must never be
    logged: the redaction filter in core/logging.py is defence in depth (it
    scrubs `code=`/`state=` query shapes), and this handler deliberately does
    not touch the request log at all.

    An SPA in front of this wants the tokens handed to its own origin. It can
    open the authorize URL directly in the top-level window, since this response
    is JSON the browser will render — the documented flow is: frontend fetches
    `/authorize` for the URL, navigates to it, and the provider's redirect lands
    here, where the response carries the session the SPA then persists.
    """
    user = await oauth_service.handle_callback(db, provider, code, state)
    return _session_response(user)


@router.post("/refresh", response_model=TokenWithUser)
async def refresh(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
) -> TokenWithUser:
    user, tokens = await auth_service.refresh_tokens(db, token_request.refresh_token)
    return _session_response(user)


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user_async)) -> User:
    """The authenticated user.

    New. There was no way to ask "who am I" — the frontend faked it by calling
    the *settings* endpoint and reconstructing a user object, which left
    `id: undefined`, so the client never actually knew the user's id.
    """
    return current_user
