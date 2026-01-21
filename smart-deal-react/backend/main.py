from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, deals

app = FastAPI(title="SmartDeal API", description="Backend for SmartDeal React App")

# CORS Configuration (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(deals.router, prefix="/api", tags=["Deals"])

@app.get("/")
def read_root():
    return {"status": "ok", "message": "SmartDeal API is running"}
