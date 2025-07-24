from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload
from datetime import datetime, timezone

from . import putaway_schemas
from app.inventory import inventory_models
from app.auth.dependencies import require_role, get_db
from app.auth.auth_models import User

router = APIRouter(
    tags=["Inbound - Putaway"]
)

@router.post("/putaway/execute-item/")
def execute_putaway_item(
    item_data: putaway_schemas.PutawayItem,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor", "operator"]))
):
    grn_item = db.query(inventory_models.GoodsReceiptItem).options(
        selectinload(inventory_models.GoodsReceiptItem.goods_receipt)
        .selectinload(inventory_models.GoodsReceipt.items)
    ).filter(
        inventory_models.GoodsReceiptItem.id == item_data.receipt_item_id
    ).first()

    if not grn_item or grn_item.status == inventory_models.GRNItemStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Item is invalid or already put away.")

    remaining_qty = grn_item.quantity - grn_item.putaway_quantity
    if item_data.quantity > remaining_qty:
        raise HTTPException(status_code=400, detail=f"Putaway quantity ({item_data.quantity}) cannot exceed remaining quantity ({remaining_qty}).")

    inventory_item = db.query(inventory_models.Inventory).filter(
        inventory_models.Inventory.product_id == item_data.product_id,
        inventory_models.Inventory.location_id == item_data.putaway_location_id,
        inventory_models.Inventory.batch == item_data.batch,
        inventory_models.Inventory.mfg_date == item_data.mfg_date,
        inventory_models.Inventory.exp_date == item_data.exp_date
    ).first()

    if inventory_item:
        inventory_item.quantity += item_data.quantity
    else:
        inventory_item = inventory_models.Inventory(
            product_id=item_data.product_id, location_id=item_data.putaway_location_id,
            quantity=item_data.quantity, batch=item_data.batch,
            mfg_date=item_data.mfg_date, exp_date=item_data.exp_date
        )
        db.add(inventory_item)
    
    db.flush() # Get the ID for the new/updated inventory item

    # --- NEW: Create a Putaway Log record ---
    log_entry = inventory_models.PutawayLog(
        goods_receipt_item_id=grn_item.id,
        inventory_id=inventory_item.id,
        quantity=item_data.quantity,
        putaway_by_user_id=current_user.id
    )
    db.add(log_entry)

    grn_item.putaway_quantity += item_data.quantity
    if grn_item.putaway_quantity >= grn_item.quantity:
        grn_item.status = inventory_models.GRNItemStatus.COMPLETED
    
    db.commit()
    # Check if the entire parent GRN is now completed
    parent_grn = grn_item.goods_receipt
    all_items_completed = all(
        item.status == inventory_models.GRNItemStatus.COMPLETED for item in parent_grn.items
    )

    if all_items_completed:
        parent_grn.status = inventory_models.GoodsReceiptStatus.COMPLETED
        db.commit()

    return {"message": f"Item {grn_item.product.name} put away successfully."}