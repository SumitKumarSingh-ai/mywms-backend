from pydantic import BaseModel
from .inventory_models import LocationTypeEnum

class LocationBase(BaseModel):
    code: str
    location_type: LocationTypeEnum
    # warehouse_id removed

class LocationCreate(LocationBase):
    pass

class LocationUpdate(BaseModel):
    location_type: LocationTypeEnum | None = None

class Location(LocationBase):
    id: int
    class Config:
        from_attributes = True