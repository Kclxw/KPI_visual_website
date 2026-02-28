"""
应用配置
"""
from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",          # 忽略 .env 中未声明的字段，避免 extra_forbidden 报错
    )

    # 应用信息
    APP_NAME: str = "KPI Visual API"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # 数据库配置
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306
    DB_USER: str = "root"
    DB_PASSWORD: str = ""
    DB_NAME: str = "kpi_visual"

    # CORS配置
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173", "http://localhost:3000",
        "http://localhost:3001", "http://localhost:3002",
        "http://127.0.0.1:5173", "http://127.0.0.1:3000",
        "http://127.0.0.1:3001", "http://127.0.0.1:3002",
    ]

    # JWT配置
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_HOURS: int = 8

    # 初始管理员账号（通过环境变量配置，留空则不创建）
    DEFAULT_ADMIN_USERNAME: str = ""
    DEFAULT_ADMIN_PASSWORD: str = ""
    DEFAULT_ADMIN_DISPLAY_NAME: str = "系统管理员"
    DEFAULT_ADMIN_EMAIL: str = ""

    @property
    def DATABASE_URL(self) -> str:
        """构建数据库连接URL"""
        return (
            f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}?charset=utf8mb4"
        )


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()
