
"""
IFIR分析服务
"""
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from app.models.tables import FactIfirRow, FactIfirDetail, MapOdmToPlant
from app.schemas.ifir import (
    IfirOptionsData,
    IfirOdmAnalyzeRequest, IfirOdmAnalyzeData, IfirOdmAnalyzeMeta,
    IfirOdmCard, IfirOdmSummary, IfirTrendPoint, TopModelRow, OdmPieRow,
    MonthlyTopModels,
    IfirSegmentAnalyzeRequest, IfirSegmentAnalyzeData,
    IfirSegmentCard, IfirSegmentSummary, TopOdmRow, SegmentPieRow,
    MonthlyTopOdms,
    IfirModelAnalyzeRequest, IfirModelAnalyzeData,
    IfirModelCard, IfirModelSummary, TopIssueRow, ModelPieRow,
    MonthlyTopIssues,
    IfirModelIssueRequest, IfirModelIssueDetailData, IfirModelIssueDetailRow,
    IfirModelReportRequest, IfirOdmReportRequest, IfirSegmentReportRequest,
)
from app.schemas.common import TimeRange

import logging
from typing import Tuple

logger = logging.getLogger(__name__)


class IfirService:
    """IFIR分析服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    # ==================== 工具方法 ====================
    
    def _parse_month(self, month_str: str) -> date:
        """解析月份字符串为日期"""
        return date.fromisoformat(f"{month_str}-01")
    
    def _format_month(self, d: date) -> str:
        """格式化日期为月份字符串"""
        return d.strftime("%Y-%m")

    def _serialize_detail_value(self, key: str, value):
        """Serialize exported detail values while preserving raw columns."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.strftime("%Y-%m-%d %H:%M:%S")
        if isinstance(value, date):
            if key in {"claim_month", "delivery_month"}:
                return self._format_month(value)
            return value.strftime("%Y-%m-%d")
        return value
    
    def _calc_ifir(self, box_claim: int, box_mm: int) -> float:
        """计算IFIR值"""
        if box_mm == 0:
            return 0.0
        return round(box_claim / box_mm, 8)
    
    def _calc_share(self, value: int, total: int) -> float:
        """计算占比"""
        if total == 0:
            return 0.0
        return round(value / total, 4)

    def _sort_top_items(self, items: List[dict], sort_key: str) -> None:
        if sort_key == "claim":
            items.sort(
                key=lambda x: (x.get("box_claim") or 0, x.get("ifir") or 0),
                reverse=True
            )
        else:
            items.sort(
                key=lambda x: (x.get("ifir") or 0, x.get("box_claim") or 0),
                reverse=True
            )

    def _apply_detail_segment_filter(self, query, segments: Optional[List[str]]):
        """IFIR DETAIL 的 Segment 实际可能落在 segment2，查询时兼容两个字段。"""
        if not segments:
            return query
        return query.filter(
            or_(
                FactIfirDetail.segment.in_(segments),
                FactIfirDetail.segment2.in_(segments),
            )
        )

    def _get_top_issue_by_model(
        self,
        start_date: date,
        end_date: date,
        models: List[str],
        segments: Optional[List[str]] = None,
        plant_list: Optional[List[str]] = None,
        top_n: int = 1
    ) -> dict:
        """鑾峰彇姣忎釜Model鐨凾op Issue鍒楄〃锛坒ault_category锛?"""
        if not models:
            return {}

        issue_query = self.db.query(
            FactIfirDetail.model,
            FactIfirDetail.fault_category,
            func.count().label("issue_count")
        ).filter(
            FactIfirDetail.delivery_month >= start_date,
            FactIfirDetail.delivery_month <= end_date,
            FactIfirDetail.model.in_(models),
            FactIfirDetail.fault_category.isnot(None),
            FactIfirDetail.fault_category != ""
        )
        issue_query = self._apply_detail_segment_filter(issue_query, segments)
        if plant_list:
            issue_query = issue_query.filter(FactIfirDetail.plant.in_(plant_list))

        issue_rows = issue_query.group_by(
            FactIfirDetail.model, FactIfirDetail.fault_category
        ).order_by(FactIfirDetail.model, desc("issue_count")).all()

        totals_by_model = {}
        for r in issue_rows:
            totals_by_model[r.model] = totals_by_model.get(r.model, 0) + r.issue_count

        top_issues_by_model = {}
        for r in issue_rows:
            issues = top_issues_by_model.setdefault(r.model, [])
            if len(issues) >= top_n:
                continue
            total = totals_by_model.get(r.model, 0)
            issues.append(TopIssueRow(
                rank=len(issues) + 1,
                issue=r.fault_category,
                count=r.issue_count,
                share=self._calc_share(r.issue_count, total) if total > 0 else 0
            ))
        return top_issues_by_model
    
    # ==================== Options API ====================
    
    def get_options(
        self,
        segments: Optional[List[str]] = None,
        odms: Optional[List[str]] = None,
        models: Optional[List[str]] = None
    ) -> IfirOptionsData:
        """
        获取IFIR筛选项
        支持任意组合过滤: 任一条件变化都会影响其他选项
        """
        # 获取月份范围（全局）
        month_result = self.db.query(
            func.min(FactIfirRow.delivery_month).label("month_min"),
            func.max(FactIfirRow.delivery_month).label("month_max")
        ).first()
        
        month_min = self._format_month(month_result.month_min) if month_result.month_min else ""
        month_max = self._format_month(month_result.month_max) if month_result.month_max else ""
        
        # Segment列表 (根据odms和models过滤)
        segment_query = self.db.query(FactIfirRow.segment).filter(FactIfirRow.segment.isnot(None))
        if odms:
            segment_query = segment_query.filter(FactIfirRow.supplier_new.in_(odms))
        if models:
            segment_query = segment_query.filter(FactIfirRow.model.in_(models))
        segments_list = [r[0] for r in segment_query.distinct().order_by(FactIfirRow.segment).all()]
        
        # ODM列表 (根据segments和models过滤)
        odm_query = self.db.query(FactIfirRow.supplier_new).filter(FactIfirRow.supplier_new.isnot(None))
        if segments:
            odm_query = odm_query.filter(FactIfirRow.segment.in_(segments))
        if models:
            odm_query = odm_query.filter(FactIfirRow.model.in_(models))
        odms_list = [r[0] for r in odm_query.distinct().order_by(FactIfirRow.supplier_new).all()]
        
        # Model列表 (根据segments和odms过滤)
        model_query = self.db.query(FactIfirRow.model).filter(FactIfirRow.model.isnot(None))
        if segments:
            model_query = model_query.filter(FactIfirRow.segment.in_(segments))
        if odms:
            model_query = model_query.filter(FactIfirRow.supplier_new.in_(odms))
        models_list = [r[0] for r in model_query.distinct().order_by(FactIfirRow.model).all()]
        
        return IfirOptionsData(
            month_min=month_min,
            month_max=month_max,
            data_as_of=month_max,
            time_range={"min_month": month_min, "max_month": month_max},
            segments=segments_list,
            odms=odms_list,
            models=models_list
        )
    
    # ==================== ODM Analyze API ====================
    
    def analyze_odm(self, request: IfirOdmAnalyzeRequest) -> IfirOdmAnalyzeData:
        """IFIR ODM分析"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        view = request.view or IfirOdmAnalyzeRequest.__fields__["view"].default
        top_model_n = view.top_model_n if view else 10
        top_model_sort = view.top_model_sort if view else "claim"
        
        odms = request.filters.odms
        segments = request.filters.segments
        models = request.filters.models
        
        # 基础过滤条件
        def apply_filters(query):
            query = query.filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.supplier_new.in_(odms)
            )
            if segments:
                query = query.filter(FactIfirRow.segment.in_(segments))
            if models:
                query = query.filter(FactIfirRow.model.in_(models))
            return query
        
        # 1. Block D - ODM饼图汇总 (多ODM时)
        summary = None
        if len(odms) > 1:
            pie_query = apply_filters(
                self.db.query(
                    FactIfirRow.supplier_new,
                    func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                    func.sum(FactIfirRow.box_mm).label("box_mm_sum")
                )
            ).group_by(FactIfirRow.supplier_new)
            
            pie_data = pie_query.all()
            total_claim = sum(r.box_claim_sum for r in pie_data)
            
            odm_pie = [
                OdmPieRow(
                    odm=r.supplier_new,
                    ifir=self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    share=self._calc_share(r.box_claim_sum, total_claim),
                    box_claim=r.box_claim_sum,
                    box_mm=r.box_mm_sum
                )
                for r in pie_data
            ]
            summary = IfirOdmSummary(odm_pie=odm_pie)
        
        # 2. 为每个ODM生成卡片
        odm_plant_map = {}
        if odms:
            odm_plant_rows = self.db.query(
                MapOdmToPlant.supplier_new,
                MapOdmToPlant.plant
            ).filter(
                MapOdmToPlant.kpi_type == "IFIR",
                MapOdmToPlant.supplier_new.in_(odms)
            ).all()
            for odm_name, plant in odm_plant_rows:
                odm_plant_map.setdefault(odm_name, []).append(plant)

        cards = []
        for odm in odms:
            # 若 ODM 在映射表中无记录，使用不可能匹配的哨兵值，避免 Top Issue 泄露为全量数据
            plant_list = odm_plant_map.get(odm) or ["__no_match__"]
            # Block A - 趋势 (返回完整时间范围数据)
            trend_query = self.db.query(
                FactIfirRow.delivery_month,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.supplier_new == odm
            )
            if segments:
                trend_query = trend_query.filter(FactIfirRow.segment.in_(segments))
            if models:
                trend_query = trend_query.filter(FactIfirRow.model.in_(models))
            
            trend_data = trend_query.group_by(FactIfirRow.delivery_month).order_by(FactIfirRow.delivery_month).all()
            
            trend = [
                IfirTrendPoint(
                    month=self._format_month(r.delivery_month),
                    ifir=self._calc_ifir(r.box_claim_sum, r.box_mm_sum)
                )
                for r in trend_data
            ]  # 返回完整数据，不再截取
            
            # Block B - Top Model (汇总)
            top_query = self.db.query(
                FactIfirRow.model,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.supplier_new == odm,
                FactIfirRow.model.isnot(None)
            )
            if segments:
                top_query = top_query.filter(FactIfirRow.segment.in_(segments))
            if models:
                top_query = top_query.filter(FactIfirRow.model.in_(models))
            
            top_data = top_query.group_by(FactIfirRow.model).all()

            top_issues_map = self._get_top_issue_by_model(
                start_date=start_date,
                end_date=end_date,
                models=[r.model for r in top_data],
                segments=segments,
                plant_list=plant_list
            )
            
            # 计算IFIR并排序
            top_models_raw = [
                {
                    "model": r.model,
                    "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    "box_claim": r.box_claim_sum,
                    "box_mm": r.box_mm_sum,
                    "top_issues": top_issues_map.get(r.model)
                }
                for r in top_data
            ]
            self._sort_top_items(top_models_raw, top_model_sort)
            
            top_models = [
                TopModelRow(
                    rank=i + 1,
                    model=item["model"],
                    ifir=item["ifir"],
                    box_claim=item["box_claim"],
                    box_mm=item["box_mm"],
                    top_issues=item.get("top_issues")
                )
                for i, item in enumerate(top_models_raw[:top_model_n])
            ]
            
            # Block B - Top Model (月度明细)
            monthly_query = self.db.query(
                FactIfirRow.delivery_month,
                FactIfirRow.model,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.supplier_new == odm,
                FactIfirRow.model.isnot(None)
            )
            if segments:
                monthly_query = monthly_query.filter(FactIfirRow.segment.in_(segments))
            if models:
                monthly_query = monthly_query.filter(FactIfirRow.model.in_(models))
            
            monthly_data = monthly_query.group_by(
                FactIfirRow.delivery_month, FactIfirRow.model
            ).order_by(FactIfirRow.delivery_month).all()
            
            # 按月份分组
            monthly_dict = {}
            for r in monthly_data:
                month_str = self._format_month(r.delivery_month)
                if month_str not in monthly_dict:
                    monthly_dict[month_str] = []
                monthly_dict[month_str].append({
                    "model": r.model,
                    "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    "box_claim": r.box_claim_sum,
                    "box_mm": r.box_mm_sum,
                    "top_issues": top_issues_map.get(r.model)
                })
            
            # 每个月取Top N
            monthly_top_models = []
            for month_str in sorted(monthly_dict.keys()):
                items = monthly_dict[month_str]
                self._sort_top_items(items, top_model_sort)
                monthly_top_models.append(MonthlyTopModels(
                    month=month_str,
                    items=[
                        TopModelRow(rank=i+1, **item)
                        for i, item in enumerate(items[:top_model_n])
                    ]
                ))
            
            cards.append(IfirOdmCard(
                odm=odm,
                trend=trend,
                top_models=top_models,
                monthly_top_models=monthly_top_models,
                ai_summary=""
            ))
        
        # 获取data_as_of
        max_month = self.db.query(func.max(FactIfirRow.delivery_month)).scalar()
        data_as_of = self._format_month(max_month) if max_month else request.time_range.end_month
        
        return IfirOdmAnalyzeData(
            meta=IfirOdmAnalyzeMeta(
                data_as_of=data_as_of,
                time_range=request.time_range
            ),
            summary=summary,
            cards=cards
        )
    
    # ==================== Segment Analyze API ====================
    
    def analyze_segment(self, request: IfirSegmentAnalyzeRequest) -> IfirSegmentAnalyzeData:
        """IFIR Segment分析"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        view = request.view or IfirSegmentAnalyzeRequest.__fields__["view"].default
        top_n = view.top_n if view else 10
        top_odm_sort = view.top_odm_sort if view else "claim"
        top_model_sort = view.top_model_sort if view else "claim"
        
        segments = request.filters.segments
        odms = request.filters.odms
        models = request.filters.models

        plant_list = None
        if odms:
            plant_rows = self.db.query(MapOdmToPlant.plant).filter(
                MapOdmToPlant.kpi_type == "IFIR",
                MapOdmToPlant.supplier_new.in_(odms)
            ).distinct().all()
            # 若 ODM 在映射表中无记录，使用不可能匹配的哨兵值，避免 Top Issue 泄露为全量数据
            plant_list = [r[0] for r in plant_rows] or ["__no_match__"]
        
        def apply_filters(query):
            query = query.filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.segment.in_(segments)
            )
            if odms:
                query = query.filter(FactIfirRow.supplier_new.in_(odms))
            if models:
                query = query.filter(FactIfirRow.model.in_(models))
            return query

        
        # Block D - Segment饼图汇总
        summary = None
        if len(segments) > 1:
            pie_query = apply_filters(
                self.db.query(
                    FactIfirRow.segment,
                    func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                    func.sum(FactIfirRow.box_mm).label("box_mm_sum")
                )
            ).group_by(FactIfirRow.segment)
            
            pie_data = pie_query.all()
            total_claim = sum(r.box_claim_sum for r in pie_data)
            
            segment_pie = [
                SegmentPieRow(
                    segment=r.segment,
                    ifir=self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    share=self._calc_share(r.box_claim_sum, total_claim),
                    box_claim=r.box_claim_sum,
                    box_mm=r.box_mm_sum
                )
                for r in pie_data
            ]
            summary = IfirSegmentSummary(segment_pie=segment_pie)
        
        # 为每个Segment生成卡片
        cards = []
        for segment in segments:
            # Block A - 趋势 (返回完整数据)
            trend_query = self.db.query(
                FactIfirRow.delivery_month,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.segment == segment
            )
            if odms:
                trend_query = trend_query.filter(FactIfirRow.supplier_new.in_(odms))
            if models:
                trend_query = trend_query.filter(FactIfirRow.model.in_(models))
            
            trend_data = trend_query.group_by(FactIfirRow.delivery_month).order_by(FactIfirRow.delivery_month).all()
            
            trend = [
                IfirTrendPoint(
                    month=self._format_month(r.delivery_month),
                    ifir=self._calc_ifir(r.box_claim_sum, r.box_mm_sum)
                )
                for r in trend_data
            ]  # 返回完整数据
            
            # Block B - Top ODM (汇总)
            odm_query = self.db.query(
                FactIfirRow.supplier_new,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.segment == segment,
                FactIfirRow.supplier_new.isnot(None)
            )
            if odms:
                odm_query = odm_query.filter(FactIfirRow.supplier_new.in_(odms))
            if models:
                odm_query = odm_query.filter(FactIfirRow.model.in_(models))
            
            odm_data = odm_query.group_by(FactIfirRow.supplier_new).all()
            odm_raw = [
                {"odm": r.supplier_new, "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum), "box_claim": r.box_claim_sum, "box_mm": r.box_mm_sum}
                for r in odm_data
            ]
            self._sort_top_items(odm_raw, top_odm_sort)
            top_odms = [TopOdmRow(rank=i+1, **item) for i, item in enumerate(odm_raw[:top_n])]
            
            # Block B - Top Model (汇总)
            model_query = self.db.query(
                FactIfirRow.model,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.segment == segment,
                FactIfirRow.model.isnot(None)
            )
            if odms:
                model_query = model_query.filter(FactIfirRow.supplier_new.in_(odms))
            if models:
                model_query = model_query.filter(FactIfirRow.model.in_(models))
            
            model_data = model_query.group_by(FactIfirRow.model).all()
            top_issues_map = self._get_top_issue_by_model(
                start_date=start_date,
                end_date=end_date,
                models=[r.model for r in model_data],
                segments=[segment],
                plant_list=plant_list
            )
            model_raw = [
                {
                    "model": r.model,
                    "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    "box_claim": r.box_claim_sum,
                    "box_mm": r.box_mm_sum,
                    "top_issues": top_issues_map.get(r.model)
                }
                for r in model_data
            ]
            self._sort_top_items(model_raw, top_model_sort)
            top_models = [TopModelRow(rank=i+1, **item) for i, item in enumerate(model_raw[:top_n])]
            
            # 月度明细 - Top ODM
            monthly_odm_query = self.db.query(
                FactIfirRow.delivery_month,
                FactIfirRow.supplier_new,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.segment == segment,
                FactIfirRow.supplier_new.isnot(None)
            )
            if odms:
                monthly_odm_query = monthly_odm_query.filter(FactIfirRow.supplier_new.in_(odms))
            if models:
                monthly_odm_query = monthly_odm_query.filter(FactIfirRow.model.in_(models))
            
            monthly_odm_data = monthly_odm_query.group_by(
                FactIfirRow.delivery_month, FactIfirRow.supplier_new
            ).order_by(FactIfirRow.delivery_month).all()
            
            monthly_odm_dict = {}
            for r in monthly_odm_data:
                month_str = self._format_month(r.delivery_month)
                if month_str not in monthly_odm_dict:
                    monthly_odm_dict[month_str] = []
                monthly_odm_dict[month_str].append({
                    "odm": r.supplier_new,
                    "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    "box_claim": r.box_claim_sum,
                    "box_mm": r.box_mm_sum
                })
            
            monthly_top_odms = []
            for month_str in sorted(monthly_odm_dict.keys()):
                items = monthly_odm_dict[month_str]
                self._sort_top_items(items, top_odm_sort)
                monthly_top_odms.append(MonthlyTopOdms(
                    month=month_str,
                    items=[TopOdmRow(rank=i+1, **item) for i, item in enumerate(items[:top_n])]
                ))
            
            # 月度明细 - Top Model
            monthly_model_query = self.db.query(
                FactIfirRow.delivery_month,
                FactIfirRow.model,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.segment == segment,
                FactIfirRow.model.isnot(None)
            )
            if odms:
                monthly_model_query = monthly_model_query.filter(FactIfirRow.supplier_new.in_(odms))
            if models:
                monthly_model_query = monthly_model_query.filter(FactIfirRow.model.in_(models))
            
            monthly_model_data = monthly_model_query.group_by(
                FactIfirRow.delivery_month, FactIfirRow.model
            ).order_by(FactIfirRow.delivery_month).all()
            
            monthly_model_dict = {}
            for r in monthly_model_data:
                month_str = self._format_month(r.delivery_month)
                if month_str not in monthly_model_dict:
                    monthly_model_dict[month_str] = []
                monthly_model_dict[month_str].append({
                    "model": r.model,
                    "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    "box_claim": r.box_claim_sum,
                    "box_mm": r.box_mm_sum,
                    "top_issues": top_issues_map.get(r.model)
                })
            
            monthly_top_models = []
            for month_str in sorted(monthly_model_dict.keys()):
                items = monthly_model_dict[month_str]
                self._sort_top_items(items, top_model_sort)
                monthly_top_models.append(MonthlyTopModels(
                    month=month_str,
                    items=[TopModelRow(rank=i+1, **item) for i, item in enumerate(items[:top_n])]
                ))
            
            cards.append(IfirSegmentCard(
                segment=segment,
                trend=trend,
                top_odms=top_odms,
                top_models=top_models,
                monthly_top_odms=monthly_top_odms,
                monthly_top_models=monthly_top_models,
                ai_summary=""
            ))
        
        max_month = self.db.query(func.max(FactIfirRow.delivery_month)).scalar()
        data_as_of = self._format_month(max_month) if max_month else request.time_range.end_month
        
        return IfirSegmentAnalyzeData(
            meta=IfirOdmAnalyzeMeta(data_as_of=data_as_of, time_range=request.time_range),
            summary=summary,
            cards=cards
        )
    
    # ==================== Model Analyze API ====================
    
    def analyze_model(self, request: IfirModelAnalyzeRequest) -> IfirModelAnalyzeData:
        """IFIR Model分析 - 使用DETAIL表获取Top Issue"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        view = request.view or IfirModelAnalyzeRequest.__fields__["view"].default
        top_issue_n = view.top_issue_n if view else 10
        
        models_list = request.filters.models
        segments = request.filters.segments
        odms = request.filters.odms
        
        # 获取ODM对应的plant列表(用于DETAIL表过滤)
        plant_list = None
        if odms:
            plant_query = self.db.query(MapOdmToPlant.plant).filter(
                MapOdmToPlant.kpi_type == "IFIR",
                MapOdmToPlant.supplier_new.in_(odms)
            ).distinct()
            # 若 ODM 在映射表中无记录，使用不可能匹配的哨兵值，避免 Top Issue 泄露为全量数据
            plant_list = [r[0] for r in plant_query.all()] or ["__no_match__"]
        
        # Block D - Model饼图汇总
        summary = None
        if len(models_list) > 1:
            pie_query = self.db.query(
                FactIfirRow.model,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.model.in_(models_list)
            )
            if segments:
                pie_query = pie_query.filter(FactIfirRow.segment.in_(segments))
            if odms:
                pie_query = pie_query.filter(FactIfirRow.supplier_new.in_(odms))
            
            pie_data = pie_query.group_by(FactIfirRow.model).all()
            total_claim = sum(r.box_claim_sum for r in pie_data)
            
            model_pie = [
                ModelPieRow(
                    model=r.model,
                    ifir=self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    share=self._calc_share(r.box_claim_sum, total_claim),
                    box_claim=r.box_claim_sum,
                    box_mm=r.box_mm_sum
                )
                for r in pie_data
            ]
            summary = IfirModelSummary(model_pie=model_pie)
        
        # 为每个Model生成卡片
        cards = []
        for model in models_list:
            # Block A - 趋势 (从ROW表，返回完整数据)
            trend_query = self.db.query(
                FactIfirRow.delivery_month,
                func.sum(FactIfirRow.box_claim).label("box_claim_sum"),
                func.sum(FactIfirRow.box_mm).label("box_mm_sum")
            ).filter(
                FactIfirRow.delivery_month >= start_date,
                FactIfirRow.delivery_month <= end_date,
                FactIfirRow.model == model
            )
            if segments:
                trend_query = trend_query.filter(FactIfirRow.segment.in_(segments))
            if odms:
                trend_query = trend_query.filter(FactIfirRow.supplier_new.in_(odms))
            
            trend_data = trend_query.group_by(FactIfirRow.delivery_month).order_by(FactIfirRow.delivery_month).all()
            
            trend = [
                IfirTrendPoint(
                    month=self._format_month(r.delivery_month),
                    ifir=self._calc_ifir(r.box_claim_sum, r.box_mm_sum)
                )
                for r in trend_data
            ]  # 返回完整数据
            
            # Block B - Top Issue (从DETAIL表，汇总)
            issue_query = self.db.query(
                FactIfirDetail.fault_category,
                func.count().label("issue_count")
            ).filter(
                FactIfirDetail.delivery_month >= start_date,
                FactIfirDetail.delivery_month <= end_date,
                FactIfirDetail.model == model,
                FactIfirDetail.fault_category.isnot(None)
            )
            issue_query = self._apply_detail_segment_filter(issue_query, segments)
            if plant_list:
                issue_query = issue_query.filter(FactIfirDetail.plant.in_(plant_list))
            
            issue_data = issue_query.group_by(FactIfirDetail.fault_category).order_by(desc("issue_count")).limit(top_issue_n).all()
            
            total_issues = sum(r.issue_count for r in issue_data)
            top_issues = [
                TopIssueRow(
                    rank=i + 1,
                    issue=r.fault_category,
                    count=r.issue_count,
                    share=self._calc_share(r.issue_count, total_issues) if total_issues > 0 else 0
                )
                for i, r in enumerate(issue_data)
            ]
            
            # 月度明细 - Top Issue
            monthly_issue_query = self.db.query(
                FactIfirDetail.delivery_month,
                FactIfirDetail.fault_category,
                func.count().label("issue_count")
            ).filter(
                FactIfirDetail.delivery_month >= start_date,
                FactIfirDetail.delivery_month <= end_date,
                FactIfirDetail.model == model,
                FactIfirDetail.fault_category.isnot(None)
            )
            monthly_issue_query = self._apply_detail_segment_filter(monthly_issue_query, segments)
            if plant_list:
                monthly_issue_query = monthly_issue_query.filter(FactIfirDetail.plant.in_(plant_list))
            
            monthly_issue_data = monthly_issue_query.group_by(
                FactIfirDetail.delivery_month, FactIfirDetail.fault_category
            ).order_by(FactIfirDetail.delivery_month).all()
            
            monthly_issue_dict = {}
            for r in monthly_issue_data:
                month_str = self._format_month(r.delivery_month)
                if month_str not in monthly_issue_dict:
                    monthly_issue_dict[month_str] = []
                monthly_issue_dict[month_str].append({
                    "issue": r.fault_category,
                    "count": r.issue_count
                })
            
            monthly_top_issues = []
            for month_str in sorted(monthly_issue_dict.keys()):
                items = monthly_issue_dict[month_str]
                items.sort(key=lambda x: x["count"], reverse=True)
                month_total = sum(item["count"] for item in items)
                monthly_top_issues.append(MonthlyTopIssues(
                    month=month_str,
                    items=[
                        TopIssueRow(
                            rank=i+1,
                            issue=item["issue"],
                            count=item["count"],
                            share=self._calc_share(item["count"], month_total) if month_total > 0 else 0
                        )
                        for i, item in enumerate(items[:top_issue_n])
                    ]
                ))
            
            cards.append(IfirModelCard(
                model=model,
                trend=trend,
                top_issues=top_issues,
                monthly_top_issues=monthly_top_issues,
                ai_summary=""
            ))
        
        max_month = self.db.query(func.max(FactIfirRow.delivery_month)).scalar()
        data_as_of = self._format_month(max_month) if max_month else request.time_range.end_month
        
        return IfirModelAnalyzeData(
            meta=IfirOdmAnalyzeMeta(data_as_of=data_as_of, time_range=request.time_range),
            summary=summary,
            cards=cards
        )

    def get_model_issue_details(self, request: IfirModelIssueRequest) -> IfirModelIssueDetailData:
        """IFIR Model Issue明细查询"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        model = request.filters.model
        issue = request.filters.issue
        segments = request.filters.segments
        odms = request.filters.odms
        page = request.pagination.page if request.pagination else 1
        page_size = request.pagination.page_size if request.pagination else 10

        plant_list = None
        if odms:
            plant_list = [r[0] for r in self.db.query(MapOdmToPlant.plant).filter(
                MapOdmToPlant.kpi_type == "IFIR",
                MapOdmToPlant.supplier_new.in_(odms)
            ).distinct().all()] or ["__no_match__"]

        query = self.db.query(FactIfirDetail).filter(
            FactIfirDetail.delivery_month >= start_date,
            FactIfirDetail.delivery_month <= end_date,
            FactIfirDetail.model == model,
            FactIfirDetail.fault_category == issue
        )
        query = self._apply_detail_segment_filter(query, segments)
        if plant_list:
            query = query.filter(FactIfirDetail.plant.in_(plant_list))

        total = query.count()
        rows = query.order_by(FactIfirDetail.delivery_month.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = [
            IfirModelIssueDetailRow(
                model=r.model,
                fault_category=r.fault_category,
                problem_descr_by_tech=r.problem_descr_by_tech,
                claim_nbr=r.claim_nbr,
                claim_month=self._format_month(r.delivery_month or r.claim_month) if (r.delivery_month or r.claim_month) else "",
                plant=r.plant
            )
            for r in rows
        ]
        return IfirModelIssueDetailData(total=total, page=page, page_size=page_size, items=items)

    # ==================== Report Generation ====================

    IFIR_DETAIL_COLUMNS = [
        ("Claim_Nbr", "claim_nbr"),
        ("Claim_Month", "claim_month"),
        ("Claim_Date", "claim_date"),
        ("Delivery_Month", "delivery_month"),
        ("Delivery_Day", "delivery_day"),
        ("Geo_2012", "geo_2012"),
        ("Financial_Region", "financial_region"),
        ("Plant", "plant"),
        ("Brand", "brand"),
        ("Segment", "segment"),
        ("Segment2", "segment2"),
        ("Style", "style"),
        ("Series", "series"),
        ("Model", "model"),
        ("MTM", "mtm"),
        ("Serial_Nbr", "serial_nbr"),
        ("StationName", "stationname"),
        ("Station_Id", "station_id"),
        ("Data_Source", "data_source"),
        ("Lastsln", "lastsln"),
        ("Failure_Code", "failure_code"),
        ("Fault_Category", "fault_category"),
        ("Mach_Desc", "mach_desc"),
        ("Problem_Descr", "problem_descr"),
        ("Problem_Descr_By_Tech", "problem_descr_by_tech"),
        ("Commodity", "commodity"),
        ("Down_Part_Code", "down_part_code"),
        ("Part_Nbr", "part_nbr"),
        ("Part_Desc", "part_desc"),
        ("Part_Supplier", "part_supplier"),
        ("Part_Barcode", "part_barcode"),
        ("Packing_Lot_No", "packing_lot_no"),
        ("Claim_Item_Nbr", "claim_item_nbr"),
        ("Claim_Status", "claim_status"),
        ("Channel", "channel"),
        ("Cust_Nbr", "cust_nbr"),
        ("Load_Ts", "load_ts"),
    ]

    def _resolve_detail_plants_ifir(
        self,
        start_date: date,
        end_date: date,
        odms: Optional[List[str]] = None,
        segments: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
    ) -> Optional[List[str]]:
        """将 ODM 列表动态解析为 plant 列表（IFIR）"""
        if not odms:
            return None

        row_query = self.db.query(FactIfirRow.plant).filter(
            FactIfirRow.delivery_month >= start_date,
            FactIfirRow.delivery_month <= end_date,
            FactIfirRow.supplier_new.in_(odms),
            FactIfirRow.plant.isnot(None),
            func.trim(FactIfirRow.plant) != "",
        )
        if segments:
            row_query = row_query.filter(FactIfirRow.segment.in_(segments))
        if models:
            row_query = row_query.filter(FactIfirRow.model.in_(models))

        plants = {
            p.strip() for (p,) in row_query.distinct().all() if p and p.strip()
        }

        map_query = self.db.query(MapOdmToPlant.plant).filter(
            MapOdmToPlant.kpi_type == "IFIR",
            MapOdmToPlant.supplier_new.in_(odms),
        )
        plants.update(
            p.strip() for (p,) in map_query.distinct().all() if p and p.strip()
        )
        return sorted(plants) if plants else ["__no_match__"]

    def _get_detail_for_report(
        self,
        start_date: date,
        end_date: date,
        models: Optional[List[str]] = None,
        segments: Optional[List[str]] = None,
        odms: Optional[List[str]] = None,
        max_rows: int = 100000,
    ) -> Tuple[list, int, bool]:
        """获取 IFIR Detail 全量数据（供报告使用）"""
        detail_fields = [getattr(FactIfirDetail, key) for _, key in self.IFIR_DETAIL_COLUMNS]

        query = self.db.query(*detail_fields).filter(
            FactIfirDetail.delivery_month >= start_date,
            FactIfirDetail.delivery_month <= end_date,
        )

        if models:
            query = query.filter(FactIfirDetail.model.in_(models))
        query = self._apply_detail_segment_filter(query, segments)

        plant_list = self._resolve_detail_plants_ifir(
            start_date, end_date, odms=odms, segments=segments, models=models
        )
        if plant_list:
            query = query.filter(FactIfirDetail.plant.in_(plant_list))

        col_keys = [k for _, k in self.IFIR_DETAIL_COLUMNS]
        detail = []
        truncated = False
        for idx, r in enumerate(
            query.order_by(FactIfirDetail.delivery_month.desc()).limit(max_rows + 1)
        ):
            if idx >= max_rows:
                truncated = True
                break
            d = {}
            for i, key in enumerate(col_keys):
                d[key] = self._serialize_detail_value(key, r[i])
            detail.append(d)

        total = max_rows + 1 if truncated else len(detail)
        return detail, total, truncated

    # ----- generate report helpers -----

    def _build_trend_entities(self, cards, entity_key: str) -> list:
        return [
            {
                "name": getattr(card, entity_key) if hasattr(card, entity_key) else card.get(entity_key, ""),
                "trend": [
                    {"month": t.month, "value": t.ifir}
                    for t in (card.trend if hasattr(card, 'trend') else [])
                ],
            }
            for card in cards
        ]

    def generate_model_report(self, request: IfirModelReportRequest) -> Tuple[str, str]:
        from tempfile import NamedTemporaryFile
        from app.services.report_chart import generate_trend_chart, generate_pie_chart
        from app.services.report_excel import ReportExcelBuilder, build_report_filename

        analyze_req = IfirModelAnalyzeRequest(
            time_range=request.time_range, filters=request.filters
        )
        data = self.analyze_model(analyze_req)

        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        detail_rows, detail_total, truncated = self._get_detail_for_report(
            start_date, end_date,
            models=request.filters.models,
            segments=request.filters.segments,
            odms=request.filters.odms,
        )

        trend_entities = self._build_trend_entities(data.cards, "model")
        trend_png = generate_trend_chart(trend_entities, tgt=request.tgt,
                                          value_label="IFIR", title="IFIR Model 趋势对比")

        pie_png = None
        pie_table = []
        if data.summary and data.summary.model_pie:
            pie_items = [{"name": p.model, "value": p.ifir * 1_000_000, "share": p.share}
                         for p in data.summary.model_pie]
            pie_png = generate_pie_chart(pie_items, value_label="IFIR", title="Model IFIR 占比")
            pie_table = [
                {"name": p.model, "dppm": round(p.ifir * 1_000_000),
                 "share": p.share, "box_claim": p.box_claim, "box_mm": p.box_mm}
                for p in data.summary.model_pie
            ]

        builder = ReportExcelBuilder(kpi_type="IFIR", dimension="Model")
        builder.add_info_sheet(meta={
            "data_as_of": data.meta.data_as_of,
            "time_range": f"{request.time_range.start_month} ~ {request.time_range.end_month}",
            "entities": ", ".join(request.filters.models),
            "extra_filters": {
                "筛选Segment": ", ".join(request.filters.segments) if request.filters.segments else "全部",
                "筛选ODM": ", ".join(request.filters.odms) if request.filters.odms else "全部",
            },
        }, tgt=request.tgt)
        builder.add_trend_sheet(trend_entities, trend_png, value_key="ifir", unit_label="IFIR")

        cards_dict = [c.dict() if hasattr(c, 'dict') else c.model_dump() for c in data.cards]
        builder.add_top_issue_sheet(cards_dict, entity_key="model")
        builder.add_monthly_top_issue_sheet(cards_dict, entity_key="model")
        builder.add_detail_sheet(detail_rows, self.IFIR_DETAIL_COLUMNS, detail_total, truncated)

        if pie_png:
            builder.add_comparison_sheet(pie_table, pie_png, entity_key="name",
                                          value_label="IFIR", claim_key="box_claim", mm_key="box_mm")

        filename = build_report_filename("IFIR", "Model", request.filters.models,
                                          request.time_range.start_month, request.time_range.end_month)
        with NamedTemporaryFile(prefix="ifir-model-", suffix=".xlsx", delete=False) as tmp:
            builder.save_to_file(tmp.name)
            return tmp.name, filename

    def generate_odm_report(self, request: IfirOdmReportRequest) -> Tuple[str, str]:
        from tempfile import NamedTemporaryFile
        from app.services.report_chart import generate_trend_chart, generate_pie_chart
        from app.services.report_excel import ReportExcelBuilder, build_report_filename

        analyze_req = IfirOdmAnalyzeRequest(
            time_range=request.time_range, filters=request.filters,
            view=request.view,
        )
        data = self.analyze_odm(analyze_req)

        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        detail_rows, detail_total, truncated = self._get_detail_for_report(
            start_date, end_date,
            models=request.filters.models,
            segments=request.filters.segments,
            odms=request.filters.odms,
        )

        trend_entities = [
            {"name": c.odm, "trend": [{"month": t.month, "value": t.ifir} for t in c.trend]}
            for c in data.cards
        ]
        trend_png = generate_trend_chart(trend_entities, tgt=request.tgt,
                                          value_label="IFIR", title="IFIR ODM 趋势对比")

        pie_png = None
        pie_table = []
        if data.summary and data.summary.odm_pie:
            pie_items = [{"name": p.odm, "value": p.ifir * 1_000_000, "share": p.share}
                         for p in data.summary.odm_pie]
            pie_png = generate_pie_chart(pie_items, value_label="IFIR", title="ODM IFIR 占比")
            pie_table = [
                {"name": p.odm, "dppm": round(p.ifir * 1_000_000),
                 "share": p.share, "box_claim": p.box_claim, "box_mm": p.box_mm}
                for p in data.summary.odm_pie
            ]

        builder = ReportExcelBuilder(kpi_type="IFIR", dimension="ODM")
        sort_label = (request.view.top_model_sort if request.view else "claim").upper()
        builder.add_info_sheet(meta={
            "data_as_of": data.meta.data_as_of,
            "time_range": f"{request.time_range.start_month} ~ {request.time_range.end_month}",
            "entities": ", ".join(request.filters.odms),
            "extra_filters": {
                "筛选Segment": ", ".join(request.filters.segments) if request.filters.segments else "全部",
                "筛选Model": ", ".join(request.filters.models) if request.filters.models else "全部",
                "Top Model排序": sort_label,
            },
        }, tgt=request.tgt)
        builder.add_trend_sheet(trend_entities, trend_png, value_key="ifir", unit_label="IFIR")

        cards_dict = [c.dict() if hasattr(c, 'dict') else c.model_dump() for c in data.cards]
        builder.add_top_model_sheet(cards_dict, entity_key="odm", value_label="IFIR",
                                     claim_key="box_claim", mm_key="box_mm")
        builder.add_monthly_top_model_sheet(cards_dict, entity_key="odm", value_label="IFIR",
                                             claim_key="box_claim", mm_key="box_mm")
        builder.add_detail_sheet(detail_rows, self.IFIR_DETAIL_COLUMNS, detail_total, truncated)

        if pie_png:
            builder.add_comparison_sheet(pie_table, pie_png, entity_key="name",
                                          value_label="IFIR", claim_key="box_claim", mm_key="box_mm")

        filename = build_report_filename("IFIR", "ODM", request.filters.odms,
                                          request.time_range.start_month, request.time_range.end_month)
        with NamedTemporaryFile(prefix="ifir-odm-", suffix=".xlsx", delete=False) as tmp:
            builder.save_to_file(tmp.name)
            return tmp.name, filename

    def generate_segment_report(self, request: IfirSegmentReportRequest) -> Tuple[str, str]:
        from tempfile import NamedTemporaryFile
        from app.services.report_chart import generate_trend_chart, generate_pie_chart
        from app.services.report_excel import ReportExcelBuilder, build_report_filename

        analyze_req = IfirSegmentAnalyzeRequest(
            time_range=request.time_range, filters=request.filters,
            view=request.view,
        )
        data = self.analyze_segment(analyze_req)

        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        detail_rows, detail_total, truncated = self._get_detail_for_report(
            start_date, end_date,
            models=request.filters.models,
            segments=request.filters.segments,
            odms=request.filters.odms,
        )

        trend_entities = [
            {"name": c.segment, "trend": [{"month": t.month, "value": t.ifir} for t in c.trend]}
            for c in data.cards
        ]
        trend_png = generate_trend_chart(trend_entities, tgt=request.tgt,
                                          value_label="IFIR", title="IFIR Segment 趋势对比")

        pie_png = None
        pie_table = []
        if data.summary and data.summary.segment_pie:
            pie_items = [{"name": p.segment, "value": p.ifir * 1_000_000, "share": p.share}
                         for p in data.summary.segment_pie]
            pie_png = generate_pie_chart(pie_items, value_label="IFIR", title="Segment IFIR 占比")
            pie_table = [
                {"name": p.segment, "dppm": round(p.ifir * 1_000_000),
                 "share": p.share, "box_claim": p.box_claim, "box_mm": p.box_mm}
                for p in data.summary.segment_pie
            ]

        builder = ReportExcelBuilder(kpi_type="IFIR", dimension="Segment")
        view = request.view
        builder.add_info_sheet(meta={
            "data_as_of": data.meta.data_as_of,
            "time_range": f"{request.time_range.start_month} ~ {request.time_range.end_month}",
            "entities": ", ".join(request.filters.segments),
            "extra_filters": {
                "筛选ODM": ", ".join(request.filters.odms) if request.filters.odms else "全部",
                "筛选Model": ", ".join(request.filters.models) if request.filters.models else "全部",
                "Top ODM排序": (view.top_odm_sort if view else "claim").upper(),
                "Top Model排序": (view.top_model_sort if view else "claim").upper(),
            },
        }, tgt=request.tgt)
        builder.add_trend_sheet(trend_entities, trend_png, value_key="ifir", unit_label="IFIR")

        cards_dict = [c.dict() if hasattr(c, 'dict') else c.model_dump() for c in data.cards]
        builder.add_top_odm_sheet(cards_dict, value_label="IFIR",
                                   claim_key="box_claim", mm_key="box_mm")
        builder.add_monthly_top_odm_sheet(cards_dict, value_label="IFIR",
                                           claim_key="box_claim", mm_key="box_mm")
        builder.add_top_model_sheet(cards_dict, entity_key="segment", value_label="IFIR",
                                     claim_key="box_claim", mm_key="box_mm")
        builder.add_monthly_top_model_sheet(cards_dict, entity_key="segment", value_label="IFIR",
                                             claim_key="box_claim", mm_key="box_mm")
        builder.add_detail_sheet(detail_rows, self.IFIR_DETAIL_COLUMNS, detail_total, truncated)

        if pie_png:
            builder.add_comparison_sheet(pie_table, pie_png, entity_key="name",
                                          value_label="IFIR", claim_key="box_claim", mm_key="box_mm")

        filename = build_report_filename("IFIR", "Segment", request.filters.segments,
                                          request.time_range.start_month, request.time_range.end_month)
        with NamedTemporaryFile(prefix="ifir-seg-", suffix=".xlsx", delete=False) as tmp:
            builder.save_to_file(tmp.name)
            return tmp.name, filename


