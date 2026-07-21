"""User and authentication endpoints.

First converted slice. Shape to copy for the rest:
  router parses/validates HTTP -> calls a service -> shapes the response.
No ORM queries, no business rules, no HTTPException.
"""

from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.user import RefreshTokenRequest, TokenWithUser, UserCreate, UserPublic
from ..services import auth as auth_service

router = APIRouter()


@router.post("/signup", response_model=UserPublic, status_code=status.HTTP_201_CREATED)
async def signup(
    user_in: UserCreate,
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
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db),
) -> TokenWithUser:
    """Exchange credentials for a token pair.

    Still `OAuth2PasswordRequestForm` (form-encoded, `username` field) because
    that is what FastAPI's OAuth2 flow and the Swagger "Authorize" button expect,
    and what the existing frontend already sends.
    """
    user = await auth_service.authenticate(db, form_data.username, form_data.password)
    tokens = auth_service.issue_tokens(user)
    return TokenWithUser(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=UserPublic.model_validate(user),
    )


@router.post("/refresh", response_model=TokenWithUser)
async def refresh(
    token_request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
) -> TokenWithUser:
    user, tokens = await auth_service.refresh_tokens(db, token_request.refresh_token)
    return TokenWithUser(
        access_token=tokens.access_token,
        refresh_token=tokens.refresh_token,
        user=UserPublic.model_validate(user),
    )


@router.get("/me", response_model=UserPublic)
async def get_me(current_user: User = Depends(get_current_user_async)) -> User:
    """The authenticated user.

    New. There was no way to ask "who am I" — the frontend faked it by calling
    the *settings* endpoint and reconstructing a user object, which left
    `id: undefined`, so the client never actually knew the user's id.
    """
    return current_user
