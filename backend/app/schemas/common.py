"""
通用Schema定义
"""
from typing import TypeVar, Generic, Optional, Any
from pydantic import BaseModel

T = TypeVar("T")


class BaseResponse(BaseModel, Generic[T]):
    """统一响应结构"""
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class TimeRange(BaseModel):
    """时间范围"""
    start_month: str  # YYYY-MM
    end_month: str    # YYYY-MM


class OptionsTimeRange(BaseModel):
    """Options 鏃堕棿鑼冨洿"""
    min_month: str  # YYYY-MM
    max_month: str  # YYYY-MM


class ViewConfig(BaseModel):
    """视图配置"""
    trend_months: int = 6
    top_n: int = 10


class TrendPoint(BaseModel):
    """趋势数据点"""
    month: str
    value: float
    numerator: Optional[int] = None
    denominator: Optional[int] = None


class TopItem(BaseModel):
    """Top排名项"""
    rank: int
    name: str
    value: float
    numerator: Optional[int] = None
    denominator: Optional[int] = None
    share: Optional[float] = None


class PieItem(BaseModel):
    """饼图数据项"""
    name: str
    value: float
    share: float
    numerator: Optional[int] = None
    denominator: Optional[int] = None

