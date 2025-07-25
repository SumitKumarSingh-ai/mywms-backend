from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload, selectinload
from typing import List
from datetime import date

from app.inventory import inventory_models
from app.auth.dependencies import get_db, require_role
from app.auth.auth_models import User

router = APIRouter(
    tags=["Reports"]
)

def calculate_shelf_life_percentage(mfg_date, exp_date):
    if not mfg_date or not exp_date: return 0
    today = date.today()
    if today > exp_date: return 0
    total_days = (exp_date - mfg_date).days
    remaining_days = (exp_date - today).days
    if total_days <= 0: return 0
    return round((remaining_days / total_days) * 100)

@router.get("/current-stock/")
def get_current_stock_report(db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin", "manager"]))):
    stock_data = db.query(inventory_models.Inventory).options(
        joinedload(inventory_models.Inventory.product),
        joinedload(inventory_models.Inventory.location)
    ).all()
    report = []
    for item in stock_data:
        report.append({
            "EAN No.": item.product.ean, "Material": item.product.material_code, "Description": item.product.name,
            "MFG Date": item.mfg_date, "EXP Date": item.exp_date,
            "Shelf Life %": calculate_shelf_life_percentage(item.mfg_date, item.exp_date),
            "Qty": item.quantity, "MRP": item.product.mrp, "Batch": item.batch, "Location": item.location.code,
            "Reserved Qty": item.reserved_quantity,
        })
    return report

@router.get("/inward-report/")
def get_inward_report(db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin", "manager"]))):
    inward_items = db.query(inventory_models.GoodsReceiptItem).filter(
        inventory_models.GoodsReceiptItem.status == inventory_models.GRNItemStatus.PENDING
    ).options(
        joinedload(inventory_models.GoodsReceiptItem.goods_receipt),
        joinedload(inventory_models.GoodsReceiptItem.product)
    ).all()
    report = []
    for item in inward_items:
        report.append({
            "Reference No.": item.goods_receipt.po_number, "EAN No.": item.product.ean,
            "Material": item.product.material_code, "Description": item.product.name,
            "Qty": item.quantity, "Open Qty": item.quantity - item.putaway_quantity, "Batch": item.batch,
        })
    return report

@router.get("/putaway-report/")
def get_putaway_report(db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin", "manager"]))):
    putaway_logs = db.query(inventory_models.PutawayLog).options(
        joinedload(inventory_models.PutawayLog.goods_receipt_item).joinedload(inventory_models.GoodsReceiptItem.goods_receipt),
        joinedload(inventory_models.PutawayLog.inventory).joinedload(inventory_models.Inventory.product),
        joinedload(inventory_models.PutawayLog.inventory).joinedload(inventory_models.Inventory.location),
    ).all()
    report = []
    for log in putaway_logs:
        inv = log.inventory
        grn_item = log.goods_receipt_item
        grn = grn_item.goods_receipt
        prod = inv.product
        report.append({
            "Reference No.": grn.po_number, "EAN No.": prod.ean, "Material": prod.material_code,
            "Description": prod.name, "MFG Date": inv.mfg_date, "EXP Date": inv.exp_date,
            "Shelf Life (%)": calculate_shelf_life_percentage(inv.mfg_date, inv.exp_date),
            "Qty": log.quantity, "MRP": prod.mrp, "Batch": inv.batch, "Location": inv.location.code,
        })
    return report

@router.get("/picklist-summary/")
def get_picklist_summary_report(db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin", "manager"]))):
    pick_items = db.query(inventory_models.PickListItem).options(
        joinedload(inventory_models.PickListItem.picklist),
        joinedload(inventory_models.PickListItem.product),
        joinedload(inventory_models.PickListItem.location)
    ).all()
    report = []
    for item in pick_items:
        # Since inventory is no longer directly linked, we can't get shelf life here.
        report.append({
            "OBD No.": item.picklist.obd_number, "Customer Name": item.picklist.customer_name,
            "EAN No.": item.product.ean, "Material": item.product.material_code, "Description": item.product.name,
            "MRP": item.product.mrp, "Asked Qty": item.required_quantity, "Allocated Qty": item.allocated_quantity,
            "Batch": item.batch, "Location": item.location.code if item.location else item.notes or "N/A",
        })
    return report

@router.get("/picking-report/")
def get_picking_report(db: Session = Depends(get_db), current_user: User = Depends(require_role(["admin", "manager"]))):
    picked_items = db.query(inventory_models.PickListItem).filter(
        inventory_models.PickListItem.status == inventory_models.PickListItemStatus.PICKED
    ).options(
        joinedload(inventory_models.PickListItem.picklist),
        joinedload(inventory_models.PickListItem.product),
        joinedload(inventory_models.PickListItem.location)
    ).all()
    report = []
    for item in picked_items:
        # Since inventory is no longer directly linked, we can't get shelf life here.
        report.append({
            "OBD No.": item.picklist.obd_number, "EAN No.": item.product.ean,
            "Material": item.product.material_code, "Description": item.product.name,
            "Qty": item.picked_quantity, "MRP": item.product.mrp, "Batch": item.batch,
            "Location": item.location.code if item.location else "N/A",
        })
    return report