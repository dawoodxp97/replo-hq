from .user import UserPublic, UserCreate, UserLogin, Token, RefreshTokenRequest
from .settings import (
    ConnectedAccount,
    ProfileSettingsUpdate,
    ProfileSettingsResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
    AppearanceSettingsUpdate,
    AppearanceSettingsResponse,
    LearningSettingsUpdate,
    LearningSettingsResponse,
    PasswordChangeRequest,
    PasswordChangeResponse,
    UserSettingsResponse,
    LLMSettingsUpdate,
    LLMSettingsResponse,
)
from .notifications import (
    NotificationResponse,
    NotificationListResponse,
    MarkAsReadRequest,
    MarkAsReadResponse,
)

# You can add imports from other schema files here as you create them
# e.g.: from .tutorial import Tutorial, TutorialCreate
