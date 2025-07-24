from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import inventory_models, location_schemas
from app.auth.dependencies import require_role, get_db, get_current_user
from app.auth import auth_models

router = APIRouter(
    tags=["Locations"]
)

@router.post("/locations/", response_model=location_schemas.Location)
def create_location(
    location: location_schemas.LocationCreate,
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(require_role("admin"))
):
    db_location = db.query(inventory_models.Location).filter(inventory_models.Location.code == location.code).first()
    if db_location:
        raise HTTPException(status_code=400, detail="Location code already exists")
    
    new_location = inventory_models.Location(**location.model_dump())
    db.add(new_location)
    db.commit()
    db.refresh(new_location)
    return new_location

@router.get("/locations/", response_model=List[location_schemas.Location])
def get_all_locations(
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_user)
):
    return db.query(inventory_models.Location).all()


@router.put("/locations/{location_id}", response_model=location_schemas.Location)
def update_location(
    location_id: int, 
    location_update: location_schemas.LocationUpdate, 
    db: Session = Depends(get_db), 
    current_user: auth_models.User = Depends(require_role("admin"))
):
    db_location = db.query(inventory_models.Location).filter(inventory_models.Location.id == location_id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    update_data = location_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_location, key, value)
        
    db.commit()
    db.refresh(db_location)
    return db_location

@router.delete("/locations/{location_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_location(
    location_id: int, 
    db: Session = Depends(get_db), 
    current_user: auth_models.User = Depends(require_role("admin"))
):
    db_location = db.query(inventory_models.Location).filter(inventory_models.Location.id == location_id).first()
    if not db_location:
        raise HTTPException(status_code=404, detail="Location not found")

    db.delete(db_location)
    db.commit()
    return None