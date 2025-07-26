from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from . import auth_schemas, auth_models
from .dependencies import get_db, get_current_user

router = APIRouter()

@router.get("/users/me", response_model=auth_schemas.User)
def read_users_me(current_user: auth_models.User = Depends(get_current_user)):
    return current_user