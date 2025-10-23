# ./backend/app/models/user.py
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship

# Import the 'Base' from your session file
from ..db.session import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    
    email = Column(String, unique=True, index=True, nullable=False)
    
    hashed_password = Column(String, nullable=False)
    
    # Add relationships later if needed, e.g.:
    # tutorials = relationship("Tutorial", back_populates="owner")