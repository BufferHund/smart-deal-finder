from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import upload, deals, wallet, shopping, chat, agent, user, route # history

app = FastAPI(title="SmartDeal API", description="Backend for SmartDeal React App")

# CORS Configuration (allow frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow LAN devices
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(upload.router, prefix="/api", tags=["Upload"])
app.include_router(deals.router, prefix="/api", tags=["Deals"])
app.include_router(shopping.router)
app.include_router(wallet.router)
app.include_router(chat.router)
app.include_router(agent.router)
app.include_router(user.router)
app.include_router(route.router)
# app.include_router(history.router) # If implemented
# app.include_router(chat.router) # If implemented

@app.get("/")
def read_root():
    return {"status": "ok", "message": "SmartDeal API is running"}
