from datetime import datetime, timedelta
from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional
from jose import jwt, JWTError
import bcrypt
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.user import User
from app.config import get_settings

settings = get_settings()

def hash_password(password: str) -> str:
    """Hash password using bcrypt"""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    """Verify password against hash"""
    return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    return jwt.encode(to_encode, settings.JWT_SECRET, algorithm=settings.JWT_ALGORITHM)

def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, settings.JWT_SECRET, algorithms=[settings.JWT_ALGORITHM])
    except JWTError:
        return None


security_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security_scheme),
) -> Optional[dict]:
    """Return the authenticated user payload or None if no valid token."""
    if not credentials:
        return None
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        return None
    return {"id": payload["sub"], "username": payload.get("username", "")}


def require_user(
    user: Optional[dict] = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    """Return authenticated user, verifying the user still exists in the database."""
    if not user:
        raise HTTPException(401, "\u8bf7\u5148\u767b\u5f55")
    if not db.query(User).filter(User.id == user["id"]).first():
        raise HTTPException(401, "\u7528\u6237\u4e0d\u5b58\u5728\uff0c\u8bf7\u91cd\u65b0\u767b\u5f55")
    return user
