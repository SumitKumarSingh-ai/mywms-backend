from pydantic import BaseModel
from datetime import date

class InventoryUpdate(BaseModel):
    quantity: float
    batch: str | None = None
    mfg_date: date | None = None
    exp_date: date | None = None