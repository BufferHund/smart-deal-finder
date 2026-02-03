from fastapi import APIRouter, HTTPException, Body
from typing import Dict, List, Optional
from pydantic import BaseModel
from services import storage

router = APIRouter(prefix="/api/user", tags=["User"])

class UserMemory(BaseModel):
    disliked_items: List[str]
    dietary_restrictions: Optional[List[str]] = None

@router.get("/stats")
def get_user_stats():
    try:
        return storage.get_spending_stats()
    except Exception as e:
        raise HTTPException(500, str(e))

@router.get("/memory")
def get_user_memory():
    settings = storage.get_user_settings()
    return {
        "disliked_items": settings.get("disliked_items", []),
        "dietary_restrictions": settings.get("dietary_restrictions", [])
    }

@router.post("/memory")
def update_user_memory(memory: UserMemory):
    storage.update_user_settings({
        "disliked_items": memory.disliked_items,
        "dietary_restrictions": memory.dietary_restrictions or []
    })
    return {"status": "ok", "message": "Memory updated"}
