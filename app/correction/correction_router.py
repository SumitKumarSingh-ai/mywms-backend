from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, joinedload
from typing import List

from . import correction_schemas
from app.inventory import inventory_models, inventory_schemas
from app.auth.dependencies import get_db, require_role
from app.auth.auth_models import User

router = APIRouter(
    tags=["Correction"]
)

@router.get("/location/{location_code}", response_model=List[inventory_schemas.Inventory])
def get_inventory_at_location(
    location_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor"]))
):
    location = db.query(inventory_models.Location).filter(inventory_models.Location.code == location_code).first()
    if not location:
        raise HTTPException(status_code=404, detail="Location not found")
    
    return db.query(inventory_models.Inventory).options(
        joinedload(inventory_models.Inventory.product)
    ).filter(inventory_models.Inventory.location_id == location.id).all()

@router.put("/inventory/{inventory_id}", response_model=inventory_schemas.Inventory)
def update_inventory_item(
    inventory_id: int,
    inventory_data: correction_schemas.InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor"]))
):
    db_inventory = db.query(inventory_models.Inventory).filter(inventory_models.Inventory.id == inventory_id).first()
    if not db_inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    update_data = inventory_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_inventory, key, value)
    
    db.commit()
    db.refresh(db_inventory)
    return db_inventory

@router.delete("/inventory/{inventory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_inventory_item(
    inventory_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor"]))
):
    db_inventory = db.query(inventory_models.Inventory).filter(inventory_models.Inventory.id == inventory_id).first()
    if not db_inventory:
        raise HTTPException(status_code=404, detail="Inventory item not found")

    db.delete(db_inventory)
    db.commit()
    return None