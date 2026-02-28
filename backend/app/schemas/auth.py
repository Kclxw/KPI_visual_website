"""
Auth & user schema definitions.
"""
import re
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.common import BaseResponse

RoleLiteral = Literal["admin", "uploader", "viewer"]


class LoginRequest(BaseModel):
    username: str
    password: str


class UserInfo(BaseModel):
    id: int
    username: str
    display_name: str
    email: Optional[str] = None
    role: RoleLiteral
    is_active: bool
    last_login: Optional[datetime] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserInfo


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    display_name: str = Field(min_length=1, max_length=100)
    email: Optional[EmailStr] = None
    password: str
    role: RoleLiteral = "viewer"

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码需包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码需包含小写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码需包含数字")
        return v


class UserUpdate(BaseModel):
    display_name: Optional[str] = None
    email: Optional[EmailStr] = None
    role: Optional[RoleLiteral] = None
    is_active: Optional[bool] = None


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码需包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码需包含小写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码需包含数字")
        return v


class ResetPasswordRequest(BaseModel):
    new_password: str

    @field_validator("new_password")
    @classmethod
    def validate_reset_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码需包含大写字母")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码需包含小写字母")
        if not re.search(r"[0-9]", v):
            raise ValueError("密码需包含数字")
        return v


class UserListData(BaseModel):
    items: List[UserInfo]
    total: int
    page: int
    page_size: int


class LoginResponse(BaseResponse[TokenResponse]):
    """登录响应"""


class UserResponse(BaseResponse[UserInfo]):
    """用户响应"""


class UserListResponse(BaseResponse[UserListData]):
    """用户列表响应"""
