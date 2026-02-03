"""
Authentication Middleware
Provides FastAPI dependencies for protecting routes.
"""

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from services.auth import decode_token, get_user_by_id

# Security scheme for Swagger UI
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    FastAPI dependency to get the current authenticated user.
    
    Usage:
        @router.get("/protected")
        def protected_route(user = Depends(get_current_user)):
            return {"user_id": user['id']}
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user = get_user_by_id(payload['user_id'])
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
):
    """
    FastAPI dependency to optionally get the current user.
    Returns None if not authenticated (doesn't raise error).
    
    Usage:
        @router.get("/public-or-private")
        def mixed_route(user = Depends(get_optional_user)):
            if user:
                return {"message": f"Hello {user['email']}"}
            return {"message": "Hello guest"}
    """
    if not credentials:
        return None
    
    token = credentials.credentials
    payload = decode_token(token)
    
    if not payload:
        return None
    
    return get_user_by_id(payload['user_id'])
