"""
Auth API routes.
"""
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, get_current_user, verify_password, hash_password
from app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserResponse,
    ChangePasswordRequest,
    UserInfo,
    TokenResponse,
)
from app.models.tables import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Auth"])
settings = get_settings()


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.authenticate_user(request.username, request.password)
    if not user:
        return LoginResponse(code=401, message="用户名或密码错误")
    if not user.is_active:
        return LoginResponse(code=403, message="账号已被禁用")

    user.last_login = datetime.now(timezone.utc)
    db.commit()

    expires_delta = timedelta(hours=settings.JWT_ACCESS_TOKEN_EXPIRE_HOURS)
    token = create_access_token({"sub": user.username, "role": user.role}, expires_delta=expires_delta)
    expires_in = int(expires_delta.total_seconds())

    user_info = UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
    )
    return LoginResponse(
        data=TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_in=expires_in,
            user=user_info,
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
    )
    return UserResponse(data=user_info)


@router.put("/me/password", response_model=UserResponse)
async def change_password(
    payload: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not verify_password(payload.old_password, current_user.hashed_password):
        return UserResponse(code=400, message="旧密码不正确")

    current_user.hashed_password = hash_password(payload.new_password)
    db.commit()
    db.refresh(current_user)

    user_info = UserInfo(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        email=current_user.email,
        role=current_user.role,
        is_active=current_user.is_active,
        last_login=current_user.last_login,
    )
    return UserResponse(data=user_info)
