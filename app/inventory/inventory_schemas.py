from pydantic import BaseModel
from datetime import date
from .inventory_models import BrandEnum, UomEnum

class ProductCreate(BaseModel):
    ean: str
    material_code: str
    name: str
    brand: BrandEnum
    uom: UomEnum = UomEnum.EA
    mrp: float
    case_size: int = 1
    min_qty: float = 0.0
    max_qty: float = 0.0

# --- ADD THIS NEW CLASS ---
class ProductUpdate(BaseModel):
    name: str | None = None
    brand: BrandEnum | None = None
    mrp: float | None = None
    case_size: int | None = None
    min_qty: float | None = None
    max_qty: float | None = None

class Product(BaseModel):
    id: int
    ean: str
    material_code: str
    name: str
    brand: BrandEnum
    uom: UomEnum
    mrp: float
    case_size: int
    min_qty: float
    max_qty: float
    class Config:
        from_attributes = True

class Inventory(BaseModel):
    id: int
    quantity: float
    reserved_quantity: float
    batch: str | None = None
    mfg_date: date | None = None
    exp_date: date | None = None
    product_id: int
    location_id: int
    product: Product
    
    class Config:
        from_attributes = True