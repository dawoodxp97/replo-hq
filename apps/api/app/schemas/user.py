from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class UserPublic(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None
    model_config = ConfigDict(from_attributes=True)


class UserCreate(BaseModel):
    first_name: str
    last_name: str | None = None
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)


class RefreshTokenRequest(BaseModel):
    refresh_token: str
