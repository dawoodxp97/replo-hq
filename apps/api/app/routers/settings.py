"""Settings endpoints — profile, notifications, appearance, learning, security,
and the BYOK credential surface.
"""

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.dependencies import get_current_user_async
from ..core.exceptions import NotFoundError
from ..db.session import get_async_db
from ..models.user import User
from ..schemas.credentials import (
    CredentialCreate,
    CredentialCreateResponse,
    CredentialResponse,
)
from ..schemas.settings import (
    AccountDeleteRequest,
    AppearanceSettingsResponse,
    AppearanceSettingsUpdate,
    LearningSettingsResponse,
    LearningSettingsUpdate,
    NotificationSettingsResponse,
    NotificationSettingsUpdate,
    PasswordChangeRequest,
    PasswordChangeResponse,
    ProfileSettingsResponse,
    ProfileSettingsUpdate,
    UserSettingsResponse,
)
from ..services import credentials as credentials_service
from ..services import settings as settings_service

router = APIRouter()


def _profile(user: User, settings) -> ProfileSettingsResponse:
    return ProfileSettingsResponse(
        first_name=user.first_name,
        last_name=user.last_name,
        email=user.email,
        bio=settings.bio,
        location=settings.location,
        website=settings.website,
        profile_picture_url=settings.profile_picture_url,
        connected_accounts=settings.connected_accounts or [],
    )


# --- Profile ----------------------------------------------------------------


@router.get("/profile", response_model=ProfileSettingsResponse)
async def get_profile(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    settings = await settings_service.get_or_create_settings(db, current_user.user_id)
    return _profile(current_user, settings)


@router.patch("/profile", response_model=ProfileSettingsResponse)
async def update_profile(
    body: ProfileSettingsUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """`connected_accounts` is no longer accepted — it is server-managed."""
    settings = await settings_service.update_profile(db, current_user, body)
    return _profile(current_user, settings)


# --- Preferences ------------------------------------------------------------


@router.get("/notifications", response_model=NotificationSettingsResponse)
async def get_notifications(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await settings_service.get_or_create_settings(db, current_user.user_id)


@router.patch("/notifications", response_model=NotificationSettingsResponse)
async def update_notifications(
    body: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await settings_service.update_notifications(db, current_user.user_id, body)


@router.get("/appearance", response_model=AppearanceSettingsResponse)
async def get_appearance(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await settings_service.get_or_create_settings(db, current_user.user_id)


@router.patch("/appearance", response_model=AppearanceSettingsResponse)
async def update_appearance(
    body: AppearanceSettingsUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await settings_service.update_appearance(db, current_user.user_id, body)


@router.get("/learning", response_model=LearningSettingsResponse)
async def get_learning(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await settings_service.get_or_create_settings(db, current_user.user_id)


@router.patch("/learning", response_model=LearningSettingsResponse)
async def update_learning(
    body: LearningSettingsUpdate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    return await settings_service.update_learning(db, current_user.user_id, body)


@router.get("/all", response_model=UserSettingsResponse)
async def get_all_settings(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    settings = await settings_service.get_or_create_settings(db, current_user.user_id)
    return UserSettingsResponse(
        user_id=current_user.user_id,
        profile=_profile(current_user, settings),
        notifications=NotificationSettingsResponse.model_validate(settings),
        appearance=AppearanceSettingsResponse.model_validate(settings),
        learning=LearningSettingsResponse.model_validate(settings),
        sessions_valid_from=current_user.sessions_valid_from,
    )


# --- Security ---------------------------------------------------------------


@router.put("/security/password", response_model=PasswordChangeResponse)
async def change_password(
    body: PasswordChangeRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Changing the password signs out every session, including this one."""
    await settings_service.change_password(
        db, current_user, body.current_password, body.new_password, body.confirm_new_password
    )
    return PasswordChangeResponse(
        message="Password updated. All sessions have been signed out — please sign in again."
    )


@router.post("/security/revoke-sessions", response_model=PasswordChangeResponse)
async def revoke_sessions(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Sign out everywhere without changing the password."""
    await settings_service.revoke_sessions(db, current_user)
    return PasswordChangeResponse(message="All sessions have been signed out.")


@router.post("/security/delete-account", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    body: AccountDeleteRequest,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """Permanently delete the account and everything it owns.

    POST with a body rather than a bare DELETE: this needs the current password,
    and a DELETE carrying a required body is awkward for clients and proxies.
    """
    await settings_service.delete_account(db, current_user, body.current_password)


# --- BYOK credentials -------------------------------------------------------
#
# The table, the encryption service and the migration all existed; nothing
# exposed them, so BYOK was unreachable. No endpoint here returns a key — see
# schemas/credentials.py.


@router.get("/credentials", response_model=list[CredentialResponse])
async def list_credentials(
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Decrypts nothing: provider, label and last_four are stored in plaintext
    precisely so this page never needs the key."""
    return await credentials_service.list_credentials(db, current_user.user_id)


@router.post(
    "/credentials", response_model=CredentialCreateResponse, status_code=status.HTTP_201_CREATED
)
async def add_credential(
    body: CredentialCreate,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
):
    """Store a key, optionally checking it against the provider first.

    Re-posting the same (provider, label) replaces the key — that is what
    rotation looks like, and forcing a delete first is friction with no benefit.
    """
    validated: bool | None = None
    validation_error: str | None = None

    if body.validate_key:
        validated, validation_error = await credentials_service.validate_credential(
            body.api_key, body.provider, body.base_url
        )

    credential = await credentials_service.store_credential(
        db,
        user_id=current_user.user_id,
        provider=body.provider,
        api_key=body.api_key,
        label=body.label,
        base_url=body.base_url,
        default_model=body.default_model,
    )

    if validated:
        await credentials_service.mark_validated(db, credential)

    return CredentialCreateResponse(
        credential=CredentialResponse.model_validate(credential),
        validated=validated,
        validation_error=validation_error,
    )


@router.delete("/credentials/{credential_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_credential(
    credential_id: UUID,
    current_user: User = Depends(get_current_user_async),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    deleted = await credentials_service.delete_credential(db, current_user.user_id, credential_id)
    if not deleted:
        raise NotFoundError("Credential not found.")
