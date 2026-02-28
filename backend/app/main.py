"""
KPI可视化系统后端主入口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import ifir, ra, upload, auth, admin
from app.core.database import SessionLocal
from app.services.auth_service import AuthService

settings = get_settings()

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="联想售后数据分析系统API",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(ifir.router, prefix="/api")
app.include_router(ra.router, prefix="/api")
app.include_router(upload.router, prefix="/api")
app.include_router(auth.router, prefix="/api")
app.include_router(admin.router, prefix="/api")


@app.on_event("startup")
def ensure_default_admin():
    """Create default admin if configured."""
    if not settings.DEFAULT_ADMIN_USERNAME or not settings.DEFAULT_ADMIN_PASSWORD:
        return
    db = SessionLocal()
    try:
        service = AuthService(db)
        service.ensure_default_admin(
            username=settings.DEFAULT_ADMIN_USERNAME,
            password=settings.DEFAULT_ADMIN_PASSWORD,
            display_name=settings.DEFAULT_ADMIN_DISPLAY_NAME,
            email=settings.DEFAULT_ADMIN_EMAIL or None,
        )
    finally:
        db.close()


@app.get("/")
async def root():
    """根路由"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
