from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import admin_schemas
from app.auth import auth_models, auth_schemas
from app.auth.dependencies import get_db, require_role
from app.auth.security import get_password_hash

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)

@router.get("/users/", response_model=List[auth_schemas.User])
def get_all_users(
    db: Session = Depends(get_db), 
    current_user: auth_models.User = Depends(require_role(["admin"]))
):
    return db.query(auth_models.User).all()

@router.post("/users/", response_model=auth_schemas.User)
def create_new_user(
    user: auth_schemas.UserCreate, 
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(require_role(["admin"]))
):
    db_user = db.query(auth_models.User).filter(auth_models.User.email == user.email).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    hashed_password = get_password_hash(user.password)
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

@router.put("/users/{user_id}", response_model=auth_schemas.User)
def update_existing_user(
    user_id: int,
    user_update: admin_schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(require_role(["admin"]))
):
    db_user = db.query(auth_models.User).filter(auth_models.User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db_user.username = user_update.username
    db_user.email = user_update.email
    db_user.role = user_update.role
    
    db.commit()
    db.refresh(db_user)
    return db_user