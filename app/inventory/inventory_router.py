from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from . import inventory_models, inventory_schemas
from app.auth.dependencies import get_current_user, get_db
from app.auth import auth_models

router = APIRouter(
    tags=["Products"]
)

@router.post("/products/", response_model=inventory_schemas.Product)
def create_product(
    product: inventory_schemas.ProductCreate, 
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_user)
):
    if db.query(inventory_models.Product).filter(inventory_models.Product.ean == product.ean).first():
        raise HTTPException(status_code=400, detail="EAN already registered")
    if db.query(inventory_models.Product).filter(inventory_models.Product.material_code == product.material_code).first():
        raise HTTPException(status_code=400, detail="Material Code already registered")
    
    new_product = inventory_models.Product(**product.model_dump())
    db.add(new_product)
    db.commit()
    db.refresh(new_product)
    return new_product

@router.get("/products/", response_model=List[inventory_schemas.Product])
def read_products(
    skip: int = 0, 
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: auth_models.User = Depends(get_current_user)
):
    products = db.query(inventory_models.Product).offset(skip).limit(limit).all()
    return products

@router.put("/products/{product_id}", response_model=inventory_schemas.Product)
def update_product(
    product_id: int, 
    product_update: inventory_schemas.ProductUpdate, 
    db: Session = Depends(get_db), 
    current_user: auth_models.User = Depends(get_current_user)
):
    db_product = db.query(inventory_models.Product).filter(inventory_models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_product, key, value)
        
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product

@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int, 
    db: Session = Depends(get_db), 
    current_user: auth_models.User = Depends(get_current_user)
):
    db_product = db.query(inventory_models.Product).filter(inventory_models.Product.id == product_id).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")

    db.delete(db_product)
    db.commit()
    return None