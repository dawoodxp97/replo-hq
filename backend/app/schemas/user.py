from pydantic import BaseModel, EmailStr, ConfigDict

# Schema for token response
class Token(BaseModel):
    access_token: str
    token_type: str

# Schema for user data in response
class UserPublic(BaseModel):
    id: int
    email: EmailStr

    # This replaces 'class Config: orm_mode = True'
    model_config = ConfigDict(from_attributes=True)

# Schema for creating a new user (registration)
class UserCreate(BaseModel):
    email: EmailStr
    password: str

# Schema for user login
class UserLogin(BaseModel):
    email: EmailStr
    password: str