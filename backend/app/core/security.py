import os
from datetime import datetime, timedelta
from typing import Optional  # <-- 1. IMPORT THIS
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel

# TODO: Move these to a .env file
SECRET_KEY = os.environ.get("SECRET_KEY", "a_very_secret_key_fallback")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30 # 30 minutes

# Password Hashing
pwd_context = CryptContext(schemes=["bcrypt_sha256", "bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    # Force bcrypt_sha256 to avoid 72-byte limit issues
    return pwd_context.hash(password, scheme="bcrypt_sha256")

# JWT Token
class TokenData(BaseModel):
    email: Optional[str] = None  # <-- 2. THIS LINE IS FIXED

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):  # <-- 3. THIS LINE IS FIXED
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt
