"""
RA分析API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.services.ra_service import RaService
from app.schemas.ra import (
    RaOptionsResponse,
    RaOdmAnalyzeRequest, RaOdmAnalyzeResponse,
    RaSegmentAnalyzeRequest, RaSegmentAnalyzeResponse,
    RaModelAnalyzeRequest, RaModelAnalyzeResponse
)

router = APIRouter(prefix="/ra", tags=["RA分析"])


# ==================== Options API ====================

@router.get("/options", response_model=RaOptionsResponse)
async def get_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """
    获取RA筛选项（统一接口，支持任意组合过滤）
    
    - 选择Segment后，ODM和Model选项会相应过滤
    - 选择ODM后，Segment和Model选项会相应过滤
    - 选择Model后，Segment和ODM选项会相应过滤
    """
    try:
        service = RaService(db)
        segments_list = segments.split(",") if segments else None
        odms_list = odms.split(",") if odms else None
        models_list = models.split(",") if models else None
        data = service.get_options(segments=segments_list, odms=odms_list, models=models_list)
        return RaOptionsResponse(data=data)
    except Exception as e:
        return RaOptionsResponse(code=500, message=str(e))


# 兼容旧接口
@router.get("/odm-analysis/options", response_model=RaOptionsResponse)
async def get_odm_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """获取RA ODM分析筛选项"""
    return await get_options(segments, odms, models, db)


@router.get("/segment-analysis/options", response_model=RaOptionsResponse)
async def get_segment_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """获取RA Segment分析筛选项"""
    return await get_options(segments, odms, models, db)


@router.get("/model-analysis/options", response_model=RaOptionsResponse)
async def get_model_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """获取RA Model分析筛选项"""
    return await get_options(segments, odms, models, db)


# ==================== Analyze API ====================

@router.post("/odm-analysis/analyze", response_model=RaOdmAnalyzeResponse)
async def analyze_odm(
    request: RaOdmAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """RA ODM分析"""
    try:
        if not request.filters.odms:
            return RaOdmAnalyzeResponse(code=400, message="ODM列表不能为空")
        
        service = RaService(db)
        data = service.analyze_odm(request)
        return RaOdmAnalyzeResponse(data=data)
    except Exception as e:
        return RaOdmAnalyzeResponse(code=500, message=str(e))


@router.post("/segment-analysis/analyze", response_model=RaSegmentAnalyzeResponse)
async def analyze_segment(
    request: RaSegmentAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """RA Segment分析"""
    try:
        if not request.filters.segments:
            return RaSegmentAnalyzeResponse(code=400, message="Segment列表不能为空")
        
        service = RaService(db)
        data = service.analyze_segment(request)
        return RaSegmentAnalyzeResponse(data=data)
    except Exception as e:
        return RaSegmentAnalyzeResponse(code=500, message=str(e))


@router.post("/model-analysis/analyze", response_model=RaModelAnalyzeResponse)
async def analyze_model(
    request: RaModelAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """RA Model分析"""
    try:
        if not request.filters.models:
            return RaModelAnalyzeResponse(code=400, message="Model列表不能为空")
        
        service = RaService(db)
        data = service.analyze_model(request)
        return RaModelAnalyzeResponse(data=data)
    except Exception as e:
        return RaModelAnalyzeResponse(code=500, message=str(e))
