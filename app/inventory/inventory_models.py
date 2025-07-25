import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum, UniqueConstraint, DateTime, Date
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base

# --- Enums (Data Definitions) ---
class BrandEnum(str, enum.Enum):
    MAMAEARTH = "Mamaearth"
    BBLUNT = "B-Blunt"
    TDC = "TDC"
    AQUALOGICA = "Aqualogica"
    AYUGA = "Ayuga"
    STAZE = "Staze"
    PURE_ORIGIN = "Pure Origin"

class UomEnum(str, enum.Enum):
    EA = "EA"
    CASE = "CASE"

class LocationTypeEnum(str, enum.Enum):
    STORAGE_BIN = "Storage Bin"
    PICKING_LOCATION = "Picking Location"
    RECEIVING_DOCK = "Receiving Dock"
    PACKING_STATION = "Packing Station"
    QC_AREA = "QC Area"
    DAMAGED_GOODS_AREA = "Damaged Goods Area"
    SHORT_STOCK_LOCATION = "Short Stock Location"

class GoodsReceiptStatus(str, enum.Enum):
    PENDING_PUTAWAY = "Pending Putaway"
    COMPLETED = "Completed"

class GRNItemStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"
    
class PickListStatus(str, enum.Enum):
    PENDING = "Pending"
    COMPLETED = "Completed"

class PickListItemStatus(str, enum.Enum):
    PENDING = "Pending"
    PICKED = "Picked"

# --- Master Data Models ---
class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True, index=True)
    ean = Column(String, unique=True, index=True, nullable=False)
    material_code = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    brand = Column(String, nullable=False)
    uom = Column(String, default='EA', nullable=False)
    mrp = Column(Float, nullable=False)
    case_size = Column(Integer, default=1)
    min_qty = Column(Float, default=0.0)
    max_qty = Column(Float, default=0.0)
    inventory_items = relationship("Inventory", back_populates="product")

class Location(Base):
    __tablename__ = "locations"
    id = Column(Integer, primary_key=True, index=True)
    code = Column(String, unique=True, index=True, nullable=False)
    location_type = Column(String, default='Storage Bin')
    max_weight = Column(Float, nullable=True)
    max_volume = Column(Float, nullable=True)
    inventory_items = relationship("Inventory", back_populates="location")

# --- Transactional Data Models ---
class Inventory(Base):
    __tablename__ = "inventory"
    id = Column(Integer, primary_key=True, index=True)
    quantity = Column(Float, nullable=False)
    reserved_quantity = Column(Float, default=0.0)
    batch = Column(String, nullable=True)
    mfg_date = Column(Date, nullable=True)
    exp_date = Column(Date, nullable=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    product = relationship("Product", back_populates="inventory_items")
    location = relationship("Location", back_populates="inventory_items")
    __table_args__ = (UniqueConstraint('product_id', 'location_id', 'batch', 'mfg_date', name='_inventory_uc'),)

class GoodsReceipt(Base):
    __tablename__ = "goods_receipts"
    id = Column(Integer, primary_key=True, index=True)
    po_number = Column(String, index=True)
    supplier_name = Column(String)
    status = Column(Enum(GoodsReceiptStatus, native_enum=False), default=GoodsReceiptStatus.PENDING_PUTAWAY)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    items = relationship("GoodsReceiptItem", back_populates="goods_receipt")

class GoodsReceiptItem(Base):
    __tablename__ = "goods_receipt_items"
    id = Column(Integer, primary_key=True, index=True)
    goods_receipt_id = Column(Integer, ForeignKey("goods_receipts.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    quantity = Column(Float, nullable=False)
    putaway_quantity = Column(Float, default=0.0, nullable=False)
    batch = Column(String, nullable=True)
    status = Column(Enum(GRNItemStatus, native_enum=False), default=GRNItemStatus.PENDING)
    goods_receipt = relationship("GoodsReceipt", back_populates="items")
    product = relationship("Product")

class PutawayLog(Base):
    __tablename__ = "putaway_log"
    id = Column(Integer, primary_key=True, index=True)
    goods_receipt_item_id = Column(Integer, ForeignKey("goods_receipt_items.id"))
    inventory_id = Column(Integer, ForeignKey("inventory.id"))
    quantity = Column(Float, nullable=False)
    putaway_by_user_id = Column(Integer, ForeignKey("users.id"))
    putaway_at = Column(DateTime(timezone=True), server_default=func.now())
    goods_receipt_item = relationship("GoodsReceiptItem")
    inventory = relationship("Inventory")

class PickList(Base):
    __tablename__ = "pick_lists"
    id = Column(Integer, primary_key=True, index=True)
    obd_number = Column(String, unique=True, index=True)
    customer_name = Column(String)
    status = Column(Enum(PickListStatus, native_enum=False), default=PickListStatus.PENDING)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    items = relationship("PickListItem", back_populates="picklist")

class PickListItem(Base):
    __tablename__ = "pick_list_items"
    id = Column(Integer, primary_key=True, index=True)
    picklist_id = Column(Integer, ForeignKey("pick_lists.id"))
    product_id = Column(Integer, ForeignKey("products.id"))
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=True)
    required_quantity = Column(Float, nullable=False)
    allocated_quantity = Column(Float, nullable=False)
    picked_quantity = Column(Float, default=0.0)
    batch = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    status = Column(Enum(PickListItemStatus, native_enum=False), default=PickListItemStatus.PENDING)
    picked_by_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    picked_at = Column(DateTime(timezone=True), nullable=True)
    
    picklist = relationship("PickList", back_populates="items")
    product = relationship("Product")
    location = relationship("Location")