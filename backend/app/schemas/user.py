from uuid import UUID
from typing import Optional
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class UserPublic(BaseModel):
    user_id: UUID
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    first_name: str
    last_name: Optional[str] = None
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class RefreshTokenRequest(BaseModel):
    refresh_token: str