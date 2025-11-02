# ./backend/app/models/user.py
from sqlalchemy import Column, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import text
from sqlalchemy.orm import relationship

# Import the 'Base' from your session file
from ..db.session import Base

class User(Base):
    __tablename__ = "users"

    user_id = Column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
    )

    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    
    email = Column(String, unique=True, index=True, nullable=False)
    
    hashed_password = Column(String, nullable=False)
    
    # Add relationships later if needed, e.g.:
    # tutorials = relationship("Tutorial", back_populates="owner")
    settings = relationship("UserSettings", back_populates="user", uselist=False)