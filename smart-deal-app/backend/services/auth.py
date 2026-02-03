"""
Authentication Service
Handles user registration, login, and JWT token management.
"""

import os
import bcrypt
import jwt
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict
from db import db

# JWT Configuration
JWT_SECRET = os.environ.get("JWT_SECRET", "smartdeal-secret-key-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24 * 7  # 7 days


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))


def create_token(user_id: int, email: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        "user_id": user_id,
        "email": email,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRE_HOURS),
        "iat": datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> Optional[Dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def register_user(email: str, password: str) -> Dict:
    """
    Register a new user.
    
    Returns:
        Dict with user info and token, or error message
    """
    # Check if email already exists
    existing = db.execute_query("SELECT id FROM users WHERE email = %s", (email,))
    if existing:
        return {"error": "Email already registered"}
    
    # Hash password
    password_hash = hash_password(password)
    
    # Generate unique ID for user
    unique_id = str(uuid.uuid4())
    
    # Insert user with unique_id
    db.execute_query(
        """
        INSERT INTO users (unique_id, email, password_hash, created_at)
        VALUES (%s, %s, %s, NOW())
        """,
        (unique_id, email, password_hash)
    )
    
    # Get the new user
    user = db.execute_query("SELECT id, email FROM users WHERE email = %s", (email,))
    if not user:
        return {"error": "Failed to create user"}
    
    user = user[0]
    token = create_token(user['id'], user['email'])
    
    return {
        "user": {
            "id": user['id'],
            "email": user['email']
        },
        "token": token
    }


def login_user(email: str, password: str) -> Dict:
    """
    Login a user.
    
    Returns:
        Dict with user info and token, or error message
    """
    # Find user
    user = db.execute_query(
        "SELECT id, email, password_hash FROM users WHERE email = %s",
        (email,)
    )
    
    if not user:
        return {"error": "Invalid email or password"}
    
    user = user[0]
    
    # Verify password
    if not verify_password(password, user['password_hash']):
        return {"error": "Invalid email or password"}
    
    token = create_token(user['id'], user['email'])
    
    return {
        "user": {
            "id": user['id'],
            "email": user['email']
        },
        "token": token
    }


def get_user_by_id(user_id: int) -> Optional[Dict]:
    """Get user info by ID."""
    user = db.execute_query(
        "SELECT id, email, created_at FROM users WHERE id = %s",
        (user_id,)
    )
    if user:
        return user[0]
    return None
