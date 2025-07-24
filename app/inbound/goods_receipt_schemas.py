from pydantic import BaseModel
from datetime import datetime, date
from typing import List
from app.inventory.inventory_schemas import Product
from app.inventory.inventory_models import GoodsReceiptStatus, GRNItemStatus

class GoodsReceiptItem(BaseModel):
    id: int
    quantity: float
    putaway_quantity: float
    batch: str | None
    status: GRNItemStatus
    product: Product
    class Config:
        from_attributes = True

class GoodsReceipt(BaseModel):
    id: int
    po_number: str
    supplier_name: str
    status: GoodsReceiptStatus
    created_at: datetime
    items: List[GoodsReceiptItem] = []
    class Config:
        from_attributes = True