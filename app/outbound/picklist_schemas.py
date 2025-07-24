from pydantic import BaseModel
from datetime import datetime, date
from typing import List
from app.inventory.inventory_schemas import Product
from app.inventory.location_schemas import Location
from app.inventory.inventory_models import PickListStatus, PickListItemStatus

class PickListItem(BaseModel):
    id: int
    product: Product
    location: Location | None = None
    batch: str | None
    required_quantity: float
    allocated_quantity: float
    status: PickListItemStatus
    notes: str | None = None
    mfg_date: date | None = None
    exp_date: date | None = None
    
    class Config:
        from_attributes = True

class PickList(BaseModel):
    id: int
    obd_number: str
    customer_name: str
    status: PickListStatus
    created_at: datetime
    items: List[PickListItem] = []
    class Config:
        from_attributes = True