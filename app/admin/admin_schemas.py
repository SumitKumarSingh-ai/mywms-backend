from pydantic import BaseModel
from app.auth.auth_models import UserRole

class UserUpdate(BaseModel):
    username: str
    email: str
    role: UserRole