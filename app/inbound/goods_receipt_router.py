from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, selectinload
from typing import List
import pandas as pd
import logging

from . import goods_receipt_schemas
from app.inventory import inventory_models
from app.auth.dependencies import require_role, get_db, get_current_user
from app.auth.auth_models import User

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter(
    tags=["Inbound - Goods Receipt"]
)

@router.get("/receipts/{grn_id}", response_model=goods_receipt_schemas.GoodsReceipt)
def get_goods_receipt(
    grn_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a single Goods Receipt by its ID, including its items and their products.
    """
    grn = db.query(inventory_models.GoodsReceipt).options(
        selectinload(inventory_models.GoodsReceipt.items)
        .selectinload(inventory_models.GoodsReceiptItem.product)
    ).filter(inventory_models.GoodsReceipt.id == grn_id).first()

    if not grn:
        raise HTTPException(status_code=404, detail="Goods Receipt not found")
    return grn

@router.get("/receipts/", response_model=List[goods_receipt_schemas.GoodsReceipt])
def get_pending_receipts(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get all Goods Receipts that are pending putaway.
    """
    return db.query(inventory_models.GoodsReceipt).options(
        selectinload(inventory_models.GoodsReceipt.items)
    ).filter(
        inventory_models.GoodsReceipt.status == inventory_models.GoodsReceiptStatus.PENDING_PUTAWAY
    ).order_by(inventory_models.GoodsReceipt.id.desc()).all()

@router.post("/receipts/upload/", response_model=goods_receipt_schemas.GoodsReceipt)
def upload_goods_receipt(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor"]))
):
    try:
        df = pd.read_excel(file.file).fillna('')
        if df.empty:
            raise ValueError("Excel file is empty.")

        po_number = str(df.iloc[0]["PO No."])
        supplier_name = str(df.iloc[0]["Supplier Name"])
        
        # Corrected: Removed all references to warehouse_id
        grn = inventory_models.GoodsReceipt(
            po_number=po_number, 
            supplier_name=supplier_name
        )
        db.add(grn)
        db.flush()

        items_to_add = []
        for index, row in df.iterrows():
            ean = str(row["EAN No."])
            product = db.query(inventory_models.Product).filter(inventory_models.Product.ean == ean).first()
            if not product:
                raise ValueError(f"Product with EAN {ean} not found in row {index + 2}")
            
            item = inventory_models.GoodsReceiptItem(
                goods_receipt_id=grn.id,
                product_id=product.id,
                quantity=row["Qty"],
                batch=str(row["Batch"]) if row["Batch"] else None
            )
            items_to_add.append(item)
        
        db.bulk_save_objects(items_to_add)
        db.commit()
        db.refresh(grn)
        logger.info(f"Successfully created GRN {grn.id} for PO {po_number}")
        return grn

    except Exception as e:
        logger.error(f"Error processing GRN upload: {e}")
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))