from uuid import UUID
from pydantic import BaseModel, EmailStr, ConfigDict, Field

class Token(BaseModel):
    access_token: str
    token_type: str

class UserPublic(BaseModel):
    user_id: UUID
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)

class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)