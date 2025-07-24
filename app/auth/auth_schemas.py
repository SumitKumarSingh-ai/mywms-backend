from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    role: str = "operator"

class UserInDB(BaseModel):
    id: int
    username: str
    email: EmailStr
    is_active: bool
    role: str
    class Config:
        from_attributes = True

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None
    role: str | None = None

class UserUpdate(BaseModel):
    email: EmailStr
    role: str
    is_active: bool