from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from . import auth_models, auth_schemas
from app.auth.dependencies import require_role, get_db

router = APIRouter(
    tags=["Users"]
)

@router.get("/users/", response_model=List[auth_schemas.UserInDB])
def get_all_users(
    db: Session = Depends(get_db), 
    current_user: auth_models.User = Depends(require_role("admin"))
):
    return db.query(auth_models.User).all()