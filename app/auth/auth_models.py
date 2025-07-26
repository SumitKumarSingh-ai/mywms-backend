import enum
from sqlalchemy import Column, Integer, String, Boolean, Enum as SAEnum
from app.core.database import Base

class UserRole(str, enum.Enum):
    OPERATOR = "operator"
    SUPERVISOR = "supervisor"
    MANAGER = "manager"
    ADMIN = "admin"

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True) # <-- THIS LINE IS FIXED
    role = Column(String, default=UserRole.OPERATOR)