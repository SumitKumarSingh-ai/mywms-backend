from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, timezone
from pydantic import BaseModel
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests

from jose import jwt
from app.core.database import SessionLocal
from app.core.config import settings
from . import auth_models, auth_schemas, security

router = APIRouter(
    tags=["Authentication"]
)

class GoogleToken(BaseModel):
    token: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

@router.post("/register/", response_model=auth_schemas.UserInDB)
def register_user(user: auth_schemas.UserCreate, db: Session = Depends(get_db)):
    db_user_by_email = db.query(auth_models.User).filter(auth_models.User.email == user.email).first()
    if db_user_by_email:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    db_user_by_username = db.query(auth_models.User).filter(auth_models.User.username == user.username).first()
    if db_user_by_username:
        raise HTTPException(status_code=400, detail="Username already taken")

    hashed_password = security.get_password_hash(user.password)
    new_user = auth_models.User(
        username=user.username,
        email=user.email, 
        hashed_password=hashed_password,
        role=user.role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.post("/login/", response_model=auth_schemas.Token)
def login_for_access_token(form_data: auth_schemas.UserLogin, db: Session = Depends(get_db)):
    user = db.query(auth_models.User).filter(auth_models.User.username == form_data.username).first()
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role}
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/google-login/", response_model=auth_schemas.Token)
def google_login(google_token: GoogleToken, db: Session = Depends(get_db)):
    try:
        session = requests.session()
        request = google_requests.Request(session)
        idinfo = id_token.verify_oauth2_token(
            google_token.token, request, settings.GOOGLE_CLIENT_ID
        )
        user_email = idinfo['email']
        user = db.query(auth_models.User).filter(auth_models.User.email == user_email).first()
        if not user:
            username_prefix = user_email.split('@')[0]
            db_user_by_username = db.query(auth_models.User).filter(auth_models.User.username == username_prefix).first()
            if db_user_by_username:
                username_prefix = f"{username_prefix}{db.query(auth_models.User).count()}"
            new_user = auth_models.User(
                username=username_prefix,
                email=user_email,
                hashed_password=security.get_password_hash("GOOGLE_SSO_USER")
            )
            db.add(new_user)
            db.commit()
            db.refresh(new_user)
            user = new_user
        access_token = create_access_token(
            data={"sub": user.username, "role": user.role}
        )
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token",
        )