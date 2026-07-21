from .notifications import (
    MarkAsReadRequest,
    MarkAsReadResponse,
    NotificationListResponse,
    NotificationResponse,
)
from .settings import (
    AppearanceSettingsResponse,
    AppearanceSettingsUpdate,
    ConnectedAccount,
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
from .user import RefreshTokenRequest, Token, UserCreate, UserLogin, UserPublic

# You can add imports from other schema files here as you create them
# e.g.: from .tutorial import Tutorial, TutorialCreate
