from pydantic import BaseModel
from typing import List
from datetime import date

class PutawayItem(BaseModel):
    receipt_item_id: int
    product_id: int
    putaway_location_id: int
    quantity: float
    batch: str | None = None
    mfg_date: date | None = None
    exp_date: date | None = None

class PutawayExecutionRequest(BaseModel):
    goods_receipt_id: int
    items: List[PutawayItem]