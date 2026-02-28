"""
RA相关Schema定义
"""
from typing import Optional, List, Literal
from pydantic import BaseModel
from app.schemas.common import TimeRange, OptionsTimeRange


# ==================== Options ====================

class RaOptionsData(BaseModel):
    """RA筛选项数据"""
    month_min: str
    month_max: str
    data_as_of: str
    time_range: OptionsTimeRange
    segments: List[str]
    odms: List[str]
    models: List[str]


class RaOptionsResponse(BaseModel):
    """RA Options API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[RaOptionsData] = None


# ==================== ODM Analyze ====================

class RaOdmFilters(BaseModel):
    """RA ODM分析筛选条件"""
    odms: List[str]
    segments: Optional[List[str]] = None
    models: Optional[List[str]] = None


class RaOdmViewConfig(BaseModel):
    """RA ODM分析视图配置"""
    trend_months: int = 6
    top_model_n: int = 10
    top_model_sort: Literal["claim", "ra"] = "claim"


class RaOdmAnalyzeRequest(BaseModel):
    """RA ODM分析请求"""
    time_range: TimeRange
    filters: RaOdmFilters
    view: Optional[RaOdmViewConfig] = None


class RaTrendPoint(BaseModel):
    """RA趋势数据点"""
    month: str
    ra: float


class RaTopModelRow(BaseModel):
    """Top Model数据行"""
    rank: int
    model: str
    ra: float
    ra_claim: Optional[int] = None
    ra_mm: Optional[int] = None


class RaMonthlyTopModels(BaseModel):
    """月度Top Model明细"""
    month: str
    items: List[RaTopModelRow]


class RaOdmPieRow(BaseModel):
    """ODM饼图数据行"""
    odm: str
    ra: float
    share: float
    ra_claim: Optional[int] = None
    ra_mm: Optional[int] = None


class RaOdmCard(BaseModel):
    """RA ODM分析卡片"""
    odm: str
    trend: List[RaTrendPoint]
    top_models: List[RaTopModelRow]  # 汇总数据
    monthly_top_models: Optional[List[RaMonthlyTopModels]] = None  # 月度明细
    ai_summary: str = ""


class RaOdmSummary(BaseModel):
    """RA ODM汇总数据(Block D)"""
    odm_pie: List[RaOdmPieRow]


class RaAnalyzeMeta(BaseModel):
    """RA分析元数据"""
    data_as_of: str
    time_range: TimeRange


class RaOdmAnalyzeData(BaseModel):
    """RA ODM分析响应数据"""
    meta: RaAnalyzeMeta
    summary: Optional[RaOdmSummary] = None
    cards: List[RaOdmCard]


class RaOdmAnalyzeResponse(BaseModel):
    """RA ODM分析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[RaOdmAnalyzeData] = None


# ==================== Segment Analyze ====================

class RaSegmentFilters(BaseModel):
    """RA Segment分析筛选条件"""
    segments: List[str]
    odms: Optional[List[str]] = None
    models: Optional[List[str]] = None


class RaSegmentViewConfig(BaseModel):
    """RA Segment分析视图配置"""
    trend_months: int = 6
    top_n: int = 10
    top_odm_sort: Literal["claim", "ra"] = "claim"
    top_model_sort: Literal["claim", "ra"] = "claim"


class RaSegmentAnalyzeRequest(BaseModel):
    """RA Segment分析请求"""
    time_range: TimeRange
    filters: RaSegmentFilters
    view: Optional[RaSegmentViewConfig] = None


class RaTopOdmRow(BaseModel):
    """Top ODM数据行"""
    rank: int
    odm: str
    ra: float
    ra_claim: Optional[int] = None
    ra_mm: Optional[int] = None


class RaMonthlyTopOdms(BaseModel):
    """月度Top ODM明细"""
    month: str
    items: List[RaTopOdmRow]


class RaSegmentPieRow(BaseModel):
    """Segment饼图数据行"""
    segment: str
    ra: float
    share: float
    ra_claim: Optional[int] = None
    ra_mm: Optional[int] = None


class RaSegmentCard(BaseModel):
    """RA Segment分析卡片"""
    segment: str
    trend: List[RaTrendPoint]
    top_odms: List[RaTopOdmRow]  # 汇总数据
    top_models: List[RaTopModelRow]  # 汇总数据
    monthly_top_odms: Optional[List[RaMonthlyTopOdms]] = None  # 月度明细
    monthly_top_models: Optional[List[RaMonthlyTopModels]] = None  # 月度明细
    ai_summary: str = ""


class RaSegmentSummary(BaseModel):
    """RA Segment汇总数据(Block D)"""
    segment_pie: List[RaSegmentPieRow]


class RaSegmentAnalyzeData(BaseModel):
    """RA Segment分析响应数据"""
    meta: RaAnalyzeMeta
    summary: Optional[RaSegmentSummary] = None
    cards: List[RaSegmentCard]


class RaSegmentAnalyzeResponse(BaseModel):
    """RA Segment分析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[RaSegmentAnalyzeData] = None


# ==================== Model Analyze ====================

class RaModelFilters(BaseModel):
    """RA Model分析筛选条件"""
    models: List[str]
    segments: Optional[List[str]] = None
    segment: Optional[str] = None
    odms: Optional[List[str]] = None


class RaModelViewConfig(BaseModel):
    """RA Model分析视图配置"""
    top_issue_n: int = 10


class RaModelAnalyzeRequest(BaseModel):
    """RA Model分析请求"""
    time_range: TimeRange
    filters: RaModelFilters
    view: Optional[RaModelViewConfig] = None


class RaTopIssueRow(BaseModel):
    """Top Issue数据行"""
    rank: int
    issue: str
    count: int
    share: Optional[float] = None


class RaMonthlyTopIssues(BaseModel):
    """月度Top Issue明细"""
    month: str
    items: List[RaTopIssueRow]


class RaModelPieRow(BaseModel):
    """Model饼图数据行"""
    model: str
    ra: float
    share: float
    ra_claim: Optional[int] = None
    ra_mm: Optional[int] = None


class RaModelCard(BaseModel):
    """RA Model分析卡片"""
    model: str
    trend: List[RaTrendPoint]
    top_issues: List[RaTopIssueRow]  # 汇总数据
    monthly_top_issues: Optional[List[RaMonthlyTopIssues]] = None  # 月度明细
    ai_summary: str = ""


class RaModelSummary(BaseModel):
    """RA Model汇总数据(Block D)"""
    model_pie: List[RaModelPieRow]


class RaModelAnalyzeData(BaseModel):
    """RA Model分析响应数据"""
    meta: RaAnalyzeMeta
    summary: Optional[RaModelSummary] = None
    cards: List[RaModelCard]


class RaModelAnalyzeResponse(BaseModel):
    """RA Model分析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[RaModelAnalyzeData] = None


