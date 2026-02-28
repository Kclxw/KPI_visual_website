"""
Authentication & user management service.
"""
from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.models.tables import User
from app.schemas.auth import UserCreate, UserUpdate
from app.core.security import hash_password, verify_password
from passlib.exc import UnknownHashError


class AuthService:
    def __init__(self, db: Session):
        self.db = db

    def get_user_by_username(self, username: str) -> Optional[User]:
        return self.db.query(User).filter(User.username == username).first()

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        return self.db.query(User).filter(User.id == user_id).first()

    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        user = self.get_user_by_username(username)
        if not user:
            return None
        try:
            if not verify_password(password, user.hashed_password):
                return None
        except UnknownHashError:
            # Legacy/plaintext password fallback; upgrade to bcrypt after first successful login.
            if password != user.hashed_password:
                return None
            user.hashed_password = hash_password(password)
            self.db.commit()
            self.db.refresh(user)
        return user

    def list_users(
        self,
        q: Optional[str],
        role: Optional[str],
        page: int,
        page_size: int,
    ) -> Tuple[List[User], int]:
        query = self.db.query(User)
        if q:
            like = f"%{q}%"
            query = query.filter(
                or_(User.username.ilike(like), User.display_name.ilike(like))
            )
        if role:
            query = query.filter(User.role == role)

        total = query.count()
        items = (
            query.order_by(User.id.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
            .all()
        )
        return items, total

    def create_user(self, data: UserCreate) -> User:
        if self.get_user_by_username(data.username):
            raise ValueError("用户名已存在")
        if data.email:
            existing = self.db.query(User).filter(User.email == data.email).first()
            if existing:
                raise ValueError("邮箱已存在")

        user = User(
            username=data.username,
            display_name=data.display_name,
            email=data.email,
            hashed_password=hash_password(data.password),
            role=data.role,
            is_active=True,
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update_user(self, user: User, data: UserUpdate) -> User:
        if data.display_name is not None:
            user.display_name = data.display_name
        if data.email is not None:
            existing = self.db.query(User).filter(User.email == data.email, User.id != user.id).first()
            if existing:
                raise ValueError("邮箱已存在")
            user.email = data.email
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active

        self.db.commit()
        self.db.refresh(user)
        return user

    def set_password(self, user: User, new_password: str) -> User:
        user.hashed_password = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user

    def ensure_default_admin(
        self,
        username: str,
        password: str,
        display_name: str,
        email: Optional[str] = None,
    ) -> Optional[User]:
        if not username or not password:
            return None
        existing = self.get_user_by_username(username)
        if existing:
            return existing
        admin = User(
            username=username,
            display_name=display_name or "系统管理员",
            email=email or None,
            hashed_password=hash_password(password),
            role="admin",
            is_active=True,
            last_login=None,
        )
        self.db.add(admin)
        self.db.commit()
        self.db.refresh(admin)
        return admin
