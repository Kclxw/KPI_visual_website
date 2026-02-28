"""
IFIR分析API路由
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.services.ifir_service import IfirService
from app.schemas.ifir import (
    IfirOptionsResponse, IfirOptionsData,
    IfirOdmAnalyzeRequest, IfirOdmAnalyzeResponse,
    IfirSegmentAnalyzeRequest, IfirSegmentAnalyzeResponse,
    IfirModelAnalyzeRequest, IfirModelAnalyzeResponse,
    IfirModelIssueRequest, IfirModelIssueDetailResponse
)

router = APIRouter(prefix="/ifir", tags=["IFIR分析"], dependencies=[Depends(get_current_user)])


# ==================== Options API ====================

@router.get("/options", response_model=IfirOptionsResponse)
async def get_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """
    获取IFIR筛选项（统一接口，支持任意组合过滤）
    
    - 选择Segment后，ODM和Model选项会相应过滤
    - 选择ODM后，Segment和Model选项会相应过滤
    - 选择Model后，Segment和ODM选项会相应过滤
    """
    try:
        service = IfirService(db)
        segments_list = segments.split(",") if segments else None
        odms_list = odms.split(",") if odms else None
        models_list = models.split(",") if models else None
        data = service.get_options(segments=segments_list, odms=odms_list, models=models_list)
        return IfirOptionsResponse(data=data)
    except Exception as e:
        return IfirOptionsResponse(code=500, message=str(e))


# 兼容旧接口
@router.get("/odm-analysis/options", response_model=IfirOptionsResponse)
async def get_odm_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """获取IFIR ODM分析筛选项"""
    return await get_options(segments, odms, models, db)


@router.get("/segment-analysis/options", response_model=IfirOptionsResponse)
async def get_segment_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """获取IFIR Segment分析筛选项"""
    return await get_options(segments, odms, models, db)


@router.get("/model-analysis/options", response_model=IfirOptionsResponse)
async def get_model_options(
    segments: Optional[str] = Query(None, description="逗号分隔的Segment列表"),
    odms: Optional[str] = Query(None, description="逗号分隔的ODM列表"),
    models: Optional[str] = Query(None, description="逗号分隔的Model列表"),
    db: Session = Depends(get_db)
):
    """获取IFIR Model分析筛选项"""
    return await get_options(segments, odms, models, db)


# ==================== Analyze API ====================

@router.post("/odm-analysis/analyze", response_model=IfirOdmAnalyzeResponse)
async def analyze_odm(
    request: IfirOdmAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    IFIR ODM分析
    
    - **time_range**: 时间范围
    - **filters.odms**: ODM列表（必选）
    - **filters.segments**: Segment列表（可选）
    - **filters.models**: Model列表（可选）
    - **view.trend_months**: 趋势月数，默认6
    - **view.top_model_n**: Top Model数量，默认3
    """
    try:
        if not request.filters.odms:
            return IfirOdmAnalyzeResponse(code=400, message="ODM列表不能为空")
        
        service = IfirService(db)
        data = service.analyze_odm(request)
        return IfirOdmAnalyzeResponse(data=data)
    except Exception as e:
        return IfirOdmAnalyzeResponse(code=500, message=str(e))


@router.post("/segment-analysis/analyze", response_model=IfirSegmentAnalyzeResponse)
async def analyze_segment(
    request: IfirSegmentAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    IFIR Segment分析
    
    - **time_range**: 时间范围
    - **filters.segments**: Segment列表（必选）
    - **filters.odms**: ODM列表（可选）
    - **filters.models**: Model列表（可选）
    - **view.trend_months**: 趋势月数，默认6
    - **view.top_n**: Top数量，默认1
    """
    try:
        if not request.filters.segments:
            return IfirSegmentAnalyzeResponse(code=400, message="Segment列表不能为空")
        
        service = IfirService(db)
        data = service.analyze_segment(request)
        return IfirSegmentAnalyzeResponse(data=data)
    except Exception as e:
        return IfirSegmentAnalyzeResponse(code=500, message=str(e))


@router.post("/model-analysis/analyze", response_model=IfirModelAnalyzeResponse)
async def analyze_model(
    request: IfirModelAnalyzeRequest,
    db: Session = Depends(get_db)
):
    """
    IFIR Model分析
    
    - **time_range**: 时间范围
    - **filters.models**: Model列表（必选）
    - **filters.segments**: Segment列表（可选）
    - **filters.odms**: ODM列表（可选）
    - **view.top_issue_n**: Top Issue数量，默认5
    """
    try:
        if not request.filters.models:
            return IfirModelAnalyzeResponse(code=400, message="Model列表不能为空")
        
        service = IfirService(db)
        data = service.analyze_model(request)
        return IfirModelAnalyzeResponse(data=data)
    except Exception as e:
        return IfirModelAnalyzeResponse(code=500, message=str(e))


@router.post("/model-analysis/issue-details", response_model=IfirModelIssueDetailResponse)
async def model_issue_details(
    request: IfirModelIssueRequest,
    db: Session = Depends(get_db)
):
    """
    IFIR Model Issue明细查询

    - **time_range**: 时间范围
    - **filters.model**: Model（必选）
    - **filters.issue**: Issue类型（必选）
    - **filters.segments**: Segment列表（可选）
    - **filters.odms**: ODM列表（可选）
    - **pagination.page/page_size**: 分页参数
    """
    try:
        service = IfirService(db)
        data = service.get_model_issue_details(request)
        return IfirModelIssueDetailResponse(data=data)
    except Exception as e:
        return IfirModelIssueDetailResponse(code=500, message=str(e))