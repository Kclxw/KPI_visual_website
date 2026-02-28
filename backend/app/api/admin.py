"""
Admin user management API.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import require_admin
from app.schemas.auth import (
    UserCreate,
    UserUpdate,
    ResetPasswordRequest,
    UserInfo,
    UserResponse,
    UserListData,
    UserListResponse,
)
from app.models.tables import User
from app.services.auth_service import AuthService

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[Depends(require_admin)])


@router.get("/users", response_model=UserListResponse)
async def list_users(
    q: Optional[str] = Query(None, description="搜索用户名或显示名"),
    role: Optional[str] = Query(None, description="角色筛选"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    service = AuthService(db)
    items, total = service.list_users(q=q, role=role, page=page, page_size=page_size)
    users = [
        UserInfo(
            id=u.id,
            username=u.username,
            display_name=u.display_name,
            email=u.email,
            role=u.role,
            is_active=u.is_active,
            last_login=u.last_login,
        )
        for u in items
    ]
    return UserListResponse(
        data=UserListData(items=users, total=total, page=page, page_size=page_size)
    )


@router.post("/users", response_model=UserResponse)
async def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    service = AuthService(db)
    try:
        user = service.create_user(payload)
    except ValueError as e:
        return UserResponse(code=400, message=str(e))
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
    )
    return UserResponse(data=user_info)


@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    service = AuthService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        return UserResponse(code=404, message="用户不存在")
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
    )
    return UserResponse(data=user_info)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if current_user.id == user_id and payload.is_active is False:
        return UserResponse(code=400, message="不能禁用自身账号")

    service = AuthService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        return UserResponse(code=404, message="用户不存在")
    try:
        user = service.update_user(user, payload)
    except ValueError as e:
        return UserResponse(code=400, message=str(e))
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
    )
    return UserResponse(data=user_info)


@router.delete("/users/{user_id}", response_model=UserResponse)
async def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if current_user.id == user_id:
        return UserResponse(code=400, message="不能删除自身账号")

    service = AuthService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        return UserResponse(code=404, message="用户不存在")

    user.is_active = False
    db.commit()
    db.refresh(user)

    user_info = UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
    )
    return UserResponse(data=user_info)


@router.post("/users/{user_id}/reset-password", response_model=UserResponse)
async def reset_password(
    user_id: int,
    payload: ResetPasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    if current_user.id == user_id:
        return UserResponse(code=400, message="不能重置自身密码")

    service = AuthService(db)
    user = service.get_user_by_id(user_id)
    if not user:
        return UserResponse(code=404, message="用户不存在")

    service.set_password(user, payload.new_password)
    user_info = UserInfo(
        id=user.id,
        username=user.username,
        display_name=user.display_name,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
        last_login=user.last_login,
    )
    return UserResponse(data=user_info)
