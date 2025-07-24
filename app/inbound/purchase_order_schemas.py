from pydantic import BaseModel
from datetime import datetime
from typing import List
from app.inventory.inventory_schemas import Product
from app.inventory.inventory_models import PurchaseOrderStatus

# --- PO Item Schemas ---
class PurchaseOrderItemBase(BaseModel):
    product_id: int
    expected_quantity: float

class PurchaseOrderItemCreate(PurchaseOrderItemBase):
    pass

class PurchaseOrderItem(PurchaseOrderItemBase):
    id: int
    received_quantity: float
    product: Product

    class Config:
        from_attributes = True

# --- PO Schemas ---
class PurchaseOrderBase(BaseModel):
    po_number: str
    supplier_name: str

class PurchaseOrderCreate(PurchaseOrderBase):
    items: List[PurchaseOrderItemCreate]

class PurchaseOrderUpdate(BaseModel):
    supplier_name: str | None = None
    status: PurchaseOrderStatus | None = None

class PurchaseOrder(PurchaseOrderBase):
    id: int
    status: PurchaseOrderStatus
    created_at: datetime
    items: List[PurchaseOrderItem] = []

    class Config:
        from_attributes = True