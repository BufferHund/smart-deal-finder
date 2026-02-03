"""
Authentication Router
Endpoints for user registration and login.
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, EmailStr
from services.auth import register_user, login_user
from middleware.auth import get_current_user

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class RegisterRequest(BaseModel):
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class AuthResponse(BaseModel):
    user: dict
    token: str


@router.post("/register")
def register(request: RegisterRequest):
    """Register a new user."""
    if len(request.password) < 6:
        raise HTTPException(400, "Password must be at least 6 characters")
    
    result = register_user(request.email, request.password)
    
    if "error" in result:
        raise HTTPException(400, result["error"])
    
    return result


@router.post("/login")
def login(request: LoginRequest):
    """Login and get JWT token."""
    result = login_user(request.email, request.password)
    
    if "error" in result:
        raise HTTPException(401, result["error"])
    
    return result


@router.get("/me")
def get_me(user = Depends(get_current_user)):
    """Get current user info."""
    return {
        "id": user['id'],
        "email": user['email'],
        "created_at": str(user.get('created_at', ''))
    }
