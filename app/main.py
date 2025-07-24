from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.auth.auth_router import router as auth_router
from app.auth.user_router import router as user_router
from app.inventory.inventory_router import router as inventory_router
from app.inventory.location_router import router as location_router
from app.inbound.goods_receipt_router import router as grn_router
from app.inbound.putaway_router import router as putaway_router
from app.outbound.picklist_router import router as picklist_router
from app.reports.reports_router import router as reports_router
from app.correction.correction_router import router as correction_router

# Import database engine and models
from app.core.database import engine
from app.auth import auth_models
from app.inventory import inventory_models

# Create all database tables from all models
inventory_models.Base.metadata.create_all(bind=engine)
auth_models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="MyWMS API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Include the routers with their correct prefixes ---
app.include_router(auth_router, prefix="/auth")
app.include_router(user_router, prefix="/admin")
app.include_router(inventory_router, prefix="/inventory")
app.include_router(location_router, prefix="/inventory")
app.include_router(grn_router, prefix="/inbound")
app.include_router(putaway_router, prefix="/inbound")
app.include_router(picklist_router, prefix="/outbound")
app.include_router(reports_router, prefix="/reports")
app.include_router(correction_router, prefix="/correction")

# --- Root and Health Check Endpoints ---
@app.get("/", tags=["Default"])
def read_root():
    return {"Project": "MyWMS - Advanced Warehouse Management System"}

@app.get("/health", tags=["Default"])
def health_check():
    return {"status": "ok"}