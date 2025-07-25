from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func
from typing import List
import pandas as pd
from datetime import datetime, date, timezone

from . import picklist_schemas
from app.inventory import inventory_models
from app.auth.dependencies import require_role, get_db, get_current_user
from app.auth.auth_models import User

router = APIRouter(
    tags=["Outbound - Pick List"]
)

def calculate_shelf_life_percentage(mfg_date, exp_date):
    if not mfg_date or not exp_date: return 0
    today = date.today()
    if today > exp_date: return 0
    total_days = (exp_date - mfg_date).days
    remaining_days = (exp_date - today).days
    if total_days <= 0: return 0
    return round((remaining_days / total_days) * 100)

@router.get("/picklists/{picklist_id}", response_model=picklist_schemas.PickList)
def get_picklist_details(
    picklist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    picklist = db.query(inventory_models.PickList).options(
        selectinload(inventory_models.PickList.items)
        .joinedload(inventory_models.PickListItem.product),
        selectinload(inventory_models.PickList.items)
        .joinedload(inventory_models.PickListItem.location)
    ).filter(inventory_models.PickList.id == picklist_id).first()

    if not picklist:
        raise HTTPException(status_code=404, detail="Pick List not found")

    for item in picklist.items:
        if item.location_id and item.batch:
            inventory_record = db.query(inventory_models.Inventory).filter(
                inventory_models.Inventory.product_id == item.product_id,
                inventory_models.Inventory.location_id == item.location_id,
                inventory_models.Inventory.batch == item.batch
            ).first()
            if inventory_record:
                item.mfg_date = inventory_record.mfg_date
                item.exp_date = inventory_record.exp_date
            
    return picklist

@router.get("/picklists/", response_model=List[picklist_schemas.PickList])
def get_all_picklists(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(inventory_models.PickList).options(
        selectinload(inventory_models.PickList.items)
    ).filter(
        inventory_models.PickList.status == inventory_models.PickListStatus.PENDING
    ).order_by(inventory_models.PickList.id.desc()).all()

@router.post("/picklists/upload/")
def upload_picklist(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor"]))
):
    try:
        df = pd.read_excel(file.file).fillna('')
        obd_number = str(df.iloc[0]["OBD No."])
        customer_name = str(df.iloc[0]["Customer Name"])

        if db.query(inventory_models.PickList).filter(inventory_models.PickList.obd_number == obd_number).first():
            raise HTTPException(status_code=400, detail=f"OBD Number {obd_number} already exists.")

        picklist = inventory_models.PickList(obd_number=obd_number, customer_name=customer_name)
        db.add(picklist)
        db.flush()

        for index, row in df.iterrows():
            ean = str(row["EAN No."])
            required_qty = float(row["Quantity"])
            product = db.query(inventory_models.Product).filter(inventory_models.Product.ean == ean).first()
            if not product:
                raise HTTPException(status_code=400, detail=f"Product with EAN {ean} not found.")

            available_inventory = db.query(inventory_models.Inventory).filter(
                inventory_models.Inventory.product_id == product.id,
                inventory_models.Inventory.quantity > func.coalesce(inventory_models.Inventory.reserved_quantity, 0)
            ).all()

            if not available_inventory:
                item = inventory_models.PickListItem(picklist_id=picklist.id, product_id=product.id, required_quantity=required_qty, allocated_quantity=0, notes="Out of Stock")
                db.add(item)
                continue

            shelf_life_req = str(row["Shelf Life"])
            min_sl, max_sl = map(int, shelf_life_req.split('-'))

            valid_stock = [s for s in available_inventory if min_sl <= calculate_shelf_life_percentage(s.mfg_date, s.exp_date) <= max_sl]

            if not valid_stock:
                item = inventory_models.PickListItem(picklist_id=picklist.id, product_id=product.id, required_quantity=required_qty, allocated_quantity=0, notes="Low Shelf Life")
                db.add(item)
                continue
            
            valid_stock.sort(key=lambda x: (x.exp_date, x.quantity))
            
            qty_to_allocate = required_qty
            for stock in valid_stock:
                if qty_to_allocate <= 0: break
                
                current_reserved = stock.reserved_quantity if stock.reserved_quantity is not None else 0
                available_qty = stock.quantity - current_reserved
                alloc_qty = min(qty_to_allocate, available_qty)

                new_picklist_item = inventory_models.PickListItem(
                    picklist_id=picklist.id, product_id=product.id, location_id=stock.location_id,
                    required_quantity=required_qty, allocated_quantity=alloc_qty, batch=stock.batch
                )
                db.add(new_picklist_item)
                stock.reserved_quantity = current_reserved + alloc_qty
                qty_to_allocate -= alloc_qty

            if qty_to_allocate > 0:
                item = inventory_models.PickListItem(picklist_id=picklist.id, product_id=product.id, required_quantity=required_qty, allocated_quantity=(required_qty - qty_to_allocate), notes=f"Shortfall of {qty_to_allocate}")
                db.add(item)

        db.commit()
        db.refresh(picklist)
        return picklist

    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@router.post("/picking/execute-item/{item_id}")
def execute_pick_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor", "operator"]))
):
    pick_item = db.query(inventory_models.PickListItem).options(
        joinedload(inventory_models.PickListItem.picklist)
        .selectinload(inventory_models.PickList.items)
    ).filter(inventory_models.PickListItem.id == item_id).first()

    if not pick_item:
        raise HTTPException(status_code=404, detail="Pick list item not found.")
    if pick_item.status == inventory_models.PickListItemStatus.PICKED:
        raise HTTPException(status_code=400, detail="This item has already been picked.")
    if not pick_item.location_id:
        raise HTTPException(status_code=400, detail="Cannot pick item with no allocated inventory.")

    inventory_record = db.query(inventory_models.Inventory).filter(
        inventory_models.Inventory.product_id == pick_item.product_id,
        inventory_models.Inventory.location_id == pick_item.location_id,
        inventory_models.Inventory.batch == pick_item.batch
    ).first()

    if not inventory_record:
        raise HTTPException(status_code=404, detail="Inventory to pick from does not exist.")

    inventory_record.quantity -= pick_item.allocated_quantity
    inventory_record.reserved_quantity -= pick_item.allocated_quantity
    
    if inventory_record.quantity <= 0:
        db.delete(inventory_record)

    pick_item.picked_quantity = pick_item.allocated_quantity
    pick_item.status = inventory_models.PickListItemStatus.PICKED
    pick_item.picked_by_user_id = current_user.id
    pick_item.picked_at = datetime.now(timezone.utc)
    
    db.commit()

    parent_picklist = pick_item.picklist
    all_items_picked = all(
        item.status == inventory_models.PickListItemStatus.PICKED for item in parent_picklist.items
    )
    if all_items_picked:
        parent_picklist.status = inventory_models.PickListStatus.COMPLETED
        db.commit()

    return {"message": "Pick confirmed successfully."}

@router.post("/picking/force-close-item/{item_id}")
def force_close_pick_item(
    item_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(["admin", "manager", "supervisor"]))
):
    pick_item = db.query(inventory_models.PickListItem).options(
        joinedload(inventory_models.PickListItem.picklist)
        .selectinload(inventory_models.PickList.items)
    ).filter(inventory_models.PickListItem.id == item_id).first()

    if not pick_item:
        raise HTTPException(status_code=404, detail="Pick list item not found.")
    
    if pick_item.location_id is not None:
        raise HTTPException(status_code=400, detail="Cannot force close an item that has allocated stock.")

    pick_item.status = inventory_models.PickListItemStatus.PICKED
    pick_item.picked_by_user_id = current_user.id
    pick_item.picked_at = datetime.now(timezone.utc)
    db.commit()

    parent_picklist = pick_item.picklist
    all_items_resolved = all(
        item.status == inventory_models.PickListItemStatus.PICKED for item in parent_picklist.items
    )
    if all_items_resolved:
        parent_picklist.status = inventory_models.PickListStatus.COMPLETED
        db.commit()

    return {"message": "Item has been manually closed."}