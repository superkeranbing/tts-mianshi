from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas import UserRegisterRequest, UserLoginRequest, TokenResponse, UserResponse

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=TokenResponse)
async def register(req: UserRegisterRequest, db: Session = Depends(get_db)):
    try:
        existing = db.execute(select(User).where(User.username == req.username)).scalar_one_or_none()
        if existing:
            raise HTTPException(400, "用户名已存在")
        user = User(
            username=req.username,
            email=req.email,
            password_hash=hash_password(req.password),
        )
        from datetime import datetime
        user.created_at = datetime.utcnow()
        db.add(user)
        db.commit()
        db.refresh(user)
        token = create_access_token({"sub": user.id, "username": user.username})
        return TokenResponse(
            access_token=token,
            user=UserResponse(
                id=user.id, username=user.username, email=user.email, created_at=user.created_at
            ),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"注册失败: {str(e)}")


@router.post("/login", response_model=TokenResponse)
async def login(req: UserLoginRequest, db: Session = Depends(get_db)):
    user = db.execute(select(User).where(User.username == req.username)).scalar_one_or_none()
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    token = create_access_token({"sub": user.id, "username": user.username})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            id=user.id, username=user.username, email=user.email, created_at=user.created_at
        ),
    )