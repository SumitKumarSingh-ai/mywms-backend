from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .core.database import engine, Base
from .auth.auth_router import router as auth_router
from .auth.user_router import router as user_router
from .inventory.inventory_router import router as inventory_router
from .inventory.location_router import router as location_router
from .inbound.goods_receipt_router import router as goods_receipt_router
from .inbound.putaway_router import router as putaway_router
from .outbound.picklist_router import router as picklist_router
from .reports.reports_router import router as reports_router
from .correction.correction_router import router as correction_router
from .admin.admin_router import router as admin_router

# This creates the database tables if they don't exist
Base.metadata.create_all(bind=engine)

app = FastAPI(title="MyWMS API")

# CORS middleware to allow the frontend to communicate with the backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# --- Include all the application routers ---
app.include_router(auth_router)
app.include_router(user_router, prefix="/auth")
app.include_router(inventory_router, prefix="/inventory")
app.include_router(location_router, prefix="/inventory")
app.include_router(goods_receipt_router, prefix="/inbound")
app.include_router(putaway_router, prefix="/inbound")
app.include_router(picklist_router, prefix="/outbound")
app.include_router(reports_router, prefix="/reports")
app.include_router(correction_router, prefix="/correction")
app.include_router(admin_router)

# --- Root and Health Check endpoints ---
@app.get("/")
def read_root():
    return {"message": "Welcome to the WMS API"}

@app.get("/health")
def health_check():
    return {"status": "ok"}