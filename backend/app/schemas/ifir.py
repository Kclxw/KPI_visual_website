"""
IFIR相关Schema定义
"""
from typing import Optional, List, Union, Literal
from pydantic import BaseModel
from app.schemas.common import TimeRange, OptionsTimeRange


# ==================== Options ====================

class IfirOptionsData(BaseModel):
    """IFIR筛选项数据"""
    month_min: str
    month_max: str
    data_as_of: str
    time_range: OptionsTimeRange
    segments: List[str]
    odms: List[str]
    models: List[str]


class IfirOptionsResponse(BaseModel):
    """IFIR Options API响应"""
    code: int = 0
    message: str = "success"
    data: Optional[IfirOptionsData] = None


# ==================== ODM Analyze ====================

class IfirOdmFilters(BaseModel):
    """IFIR ODM分析筛选条件"""
    odms: List[str]  # 必选
    segments: Optional[List[str]] = None
    models: Optional[List[str]] = None


class IfirOdmViewConfig(BaseModel):
    """IFIR ODM分析视图配置"""
    trend_months: int = 6
    top_model_n: int = 10
    top_model_sort: Literal["claim", "ifir"] = "claim"


class IfirOdmAnalyzeRequest(BaseModel):
    """IFIR ODM分析请求"""
    time_range: TimeRange
    filters: IfirOdmFilters
    view: Optional[IfirOdmViewConfig] = None


class IfirTrendPoint(BaseModel):
    """IFIR趋势数据点"""
    month: str
    ifir: float


class TopIssueRow(BaseModel):
    """Top Issue数据行"""
    rank: int
    issue: str
    count: int
    share: Optional[float] = None


class TopModelRow(BaseModel):
    """Top Model数据行"""
    rank: int
    model: str
    ifir: float
    box_claim: Optional[int] = None
    box_mm: Optional[int] = None
    top_issues: Optional[List[TopIssueRow]] = None


class MonthlyTopModels(BaseModel):
    """月度Top Model明细"""
    month: str
    items: List[TopModelRow]


class OdmPieRow(BaseModel):
    """ODM饼图数据行"""
    odm: str
    ifir: float
    share: float
    box_claim: Optional[int] = None
    box_mm: Optional[int] = None


class IfirOdmCard(BaseModel):
    """IFIR ODM分析卡片"""
    odm: str
    trend: List[IfirTrendPoint]
    top_models: List[TopModelRow]  # 汇总数据
    monthly_top_models: Optional[List[MonthlyTopModels]] = None  # 月度明细
    ai_summary: str = ""


class IfirOdmSummary(BaseModel):
    """IFIR ODM汇总数据(Block D)"""
    odm_pie: List[OdmPieRow]


class IfirOdmAnalyzeMeta(BaseModel):
    """IFIR ODM分析元数据"""
    data_as_of: str
    time_range: TimeRange


class IfirOdmAnalyzeData(BaseModel):
    """IFIR ODM分析响应数据"""
    meta: IfirOdmAnalyzeMeta
    summary: Optional[IfirOdmSummary] = None
    cards: List[IfirOdmCard]


class IfirOdmAnalyzeResponse(BaseModel):
    """IFIR ODM分析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[IfirOdmAnalyzeData] = None


# ==================== Segment Analyze ====================

class IfirSegmentFilters(BaseModel):
    """IFIR Segment分析筛选条件"""
    segments: List[str]  # 必选
    odms: Optional[List[str]] = None
    models: Optional[List[str]] = None


class IfirSegmentViewConfig(BaseModel):
    """IFIR Segment分析视图配置"""
    trend_months: int = 6
    top_n: int = 10
    top_odm_sort: Literal["claim", "ifir"] = "claim"
    top_model_sort: Literal["claim", "ifir"] = "claim"


class IfirSegmentAnalyzeRequest(BaseModel):
    """IFIR Segment分析请求"""
    time_range: TimeRange
    filters: IfirSegmentFilters
    view: Optional[IfirSegmentViewConfig] = None


class TopOdmRow(BaseModel):
    """Top ODM数据行"""
    rank: int
    odm: str
    ifir: float
    box_claim: Optional[int] = None
    box_mm: Optional[int] = None


class MonthlyTopOdms(BaseModel):
    """月度Top ODM明细"""
    month: str
    items: List[TopOdmRow]


class SegmentPieRow(BaseModel):
    """Segment饼图数据行"""
    segment: str
    ifir: float
    share: float
    box_claim: Optional[int] = None
    box_mm: Optional[int] = None


class IfirSegmentCard(BaseModel):
    """IFIR Segment分析卡片"""
    segment: str
    trend: List[IfirTrendPoint]
    top_odms: List[TopOdmRow]  # 汇总数据
    top_models: List[TopModelRow]  # 汇总数据
    monthly_top_odms: Optional[List[MonthlyTopOdms]] = None  # 月度明细
    monthly_top_models: Optional[List[MonthlyTopModels]] = None  # 月度明细
    ai_summary: str = ""


class IfirSegmentSummary(BaseModel):
    """IFIR Segment汇总数据(Block D)"""
    segment_pie: List[SegmentPieRow]


class IfirSegmentAnalyzeData(BaseModel):
    """IFIR Segment分析响应数据"""
    meta: IfirOdmAnalyzeMeta
    summary: Optional[IfirSegmentSummary] = None
    cards: List[IfirSegmentCard]


class IfirSegmentAnalyzeResponse(BaseModel):
    """IFIR Segment分析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[IfirSegmentAnalyzeData] = None


# ==================== Model Analyze ====================

class IfirModelFilters(BaseModel):
    """IFIR Model分析筛选条件"""
    models: List[str]  # 必选
    segments: Optional[List[str]] = None
    odms: Optional[List[str]] = None


class IfirModelViewConfig(BaseModel):
    """IFIR Model分析视图配置"""
    top_issue_n: int = 5


class IfirModelAnalyzeRequest(BaseModel):
    """IFIR Model分析请求"""
    time_range: TimeRange
    filters: IfirModelFilters
    view: Optional[IfirModelViewConfig] = None


class MonthlyTopIssues(BaseModel):
    """月度Top Issue明细"""
    month: str
    items: List[TopIssueRow]


class ModelPieRow(BaseModel):
    """Model饼图数据行"""
    model: str
    ifir: float
    share: float
    box_claim: Optional[int] = None
    box_mm: Optional[int] = None


class IfirModelCard(BaseModel):
    """IFIR Model分析卡片"""
    model: str
    trend: List[IfirTrendPoint]
    top_issues: List[TopIssueRow]  # 汇总数据
    monthly_top_issues: Optional[List[MonthlyTopIssues]] = None  # 月度明细
    ai_summary: str = ""


class IfirModelSummary(BaseModel):
    """IFIR Model汇总数据(Block D)"""
    model_pie: List[ModelPieRow]


class IfirModelAnalyzeData(BaseModel):
    """IFIR Model分析响应数据"""
    meta: IfirOdmAnalyzeMeta
    summary: Optional[IfirModelSummary] = None
    cards: List[IfirModelCard]


class IfirModelAnalyzeResponse(BaseModel):
    """IFIR Model分析响应"""
    code: int = 0
    message: str = "success"
    data: Optional[IfirModelAnalyzeData] = None


# ==================== Model Issue Details ====================

class IfirModelIssueFilters(BaseModel):
    """IFIR Model Issue明细筛选条件"""
    model: str
    issue: str
    segments: Optional[List[str]] = None
    odms: Optional[List[str]] = None


class IfirModelIssuePagination(BaseModel):
    """分页参数"""
    page: int = 1
    page_size: int = 10


class IfirModelIssueRequest(BaseModel):
    """IFIR Model Issue明细请求"""
    time_range: TimeRange
    filters: IfirModelIssueFilters
    pagination: Optional[IfirModelIssuePagination] = None


class IfirModelIssueDetailRow(BaseModel):
    """IFIR Model Issue明细行"""
    model: str
    fault_category: str
    problem_descr_by_tech: Optional[str] = None
    claim_nbr: str
    claim_month: str
    plant: Optional[str] = None


class IfirModelIssueDetailData(BaseModel):
    """IFIR Model Issue明细响应数据"""
    total: int
    page: int
    page_size: int
    items: List[IfirModelIssueDetailRow]


class IfirModelIssueDetailResponse(BaseModel):
    """IFIR Model Issue明细响应"""
    code: int = 0
    message: str = "success"
    data: Optional[IfirModelIssueDetailData] = None


# ==================== 通用别名 ====================

IfirAnalyzeRequest = Union[IfirOdmAnalyzeRequest, IfirSegmentAnalyzeRequest, IfirModelAnalyzeRequest]

