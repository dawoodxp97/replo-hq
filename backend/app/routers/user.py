# ./backend/app/routers/user.py
import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from .. import models, schemas
from ..core import security
from ..db.session import get_db
from ..models.user_progress import UserProgress
from ..models.quizzes import Quiz

from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()

@router.post("/signup", response_model=schemas.UserPublic)
def create_user(
    user_in: schemas.UserCreate, # 'user_in' is the Pydantic model from the request
    db: Session = Depends(get_db)  # This is the database session
):
    # Basic password length validation (characters and bytes)
    if len(user_in.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )
    if len(user_in.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at most 72 bytes (UTF-8)",
        )
    # 1. Check if user already exists (This is a SELECT query)
    db_user = db.query(models.User).filter(models.User.email == user_in.email).first()
    if db_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )
    
    # 2. Hash the plain-text password
    hashed_password = security.get_password_hash(user_in.password)
    
    # 3. Create the SQLAlchemy User model instance
    db_user = models.User(
        email=user_in.email, 
        hashed_password=hashed_password
    )
    
    # 4. --- THIS IS THE INSERT QUERY ---
    # Add the new user object to the session
    db.add(db_user)
    
    # Commit the transaction to the database
    db.commit()
    
    # Refresh the object to get the new ID from the DB
    db.refresh(db_user)
    # ------------------------------------
    
    return db_user


@router.post("/login")
def login_for_access_token(
    # Note: We use OAuth2PasswordRequestForm.
    # This automatically expects 'username' and 'password' from a form.
    # In our case, 'username' will be the user's email.
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Basic password length validation (characters and bytes)
    if not form_data.password or len(form_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at least 8 characters long",
        )
    if len(form_data.password.encode("utf-8")) > 72:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Password must be at most 72 bytes (UTF-8)",
        )
    print(f"Login attempt - Username: {form_data.username}, Password provided: {'Yes' if form_data.password else 'No'}")
    # 1. --- THIS IS THE SELECT QUERY ---
    # Get the user by their email.
    # .first() returns the first result or None
    user = db.query(models.User).filter(models.User.email == form_data.username).first()
    print(f"User found: {user.email if user else 'None'}, User ID: {user.id if user else 'N/A'}")
    # ---------------------------------
    
    # 2. Check if user exists and verify password
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 2b. Upgrade legacy bcrypt hashes to bcrypt_sha256 on successful login
    try:
        if security.pwd_context.needs_update(user.hashed_password):
            user.hashed_password = security.get_password_hash(form_data.password)
            db.commit()
            db.refresh(user)
    except Exception:
        # If upgrade fails, continue without blocking login
        pass
    
    # 3. Create the JWT token
    # The 'sub' (subject) of the token is the user's email
    access_token = security.create_access_token(
        data={"sub": user.email}
    )
    
    # 4. Return the token AND the user info
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": schemas.UserPublic.from_orm(user) # Convert model to Pydantic schema
    }

# Don't forget to include this router in your main.py!
# ./backend/app/main.py
# from .routers import user
# app.include_router(user.router, prefix="/api/v1/user", tags=["User"])