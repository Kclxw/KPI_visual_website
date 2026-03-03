"""
RA分析服务
"""
from datetime import date, datetime
from typing import Optional, List
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session

from app.models.tables import FactRaRow, FactRaDetail, MapOdmToPlant
from typing import Tuple
import logging

from app.schemas.ra import (
    RaOptionsData,
    RaOdmAnalyzeRequest, RaOdmAnalyzeData, RaAnalyzeMeta,
    RaOdmCard, RaOdmSummary, RaTrendPoint, RaTopModelRow, RaOdmPieRow,
    RaMonthlyTopModels,
    RaSegmentAnalyzeRequest, RaSegmentAnalyzeData,
    RaSegmentCard, RaSegmentSummary, RaTopOdmRow, RaSegmentPieRow,
    RaMonthlyTopOdms,
    RaModelAnalyzeRequest, RaModelAnalyzeData,
    RaModelCard, RaModelSummary, RaTopIssueRow, RaModelPieRow,
    RaMonthlyTopIssues,
    RaModelIssueRequest, RaModelIssueDetailData, RaModelIssueDetailRow,
    RaModelReportRequest, RaOdmReportRequest, RaSegmentReportRequest,
)

logger = logging.getLogger(__name__)


class RaService:
    """RA分析服务"""
    
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
            if key == "claim_month":
                return self._format_month(value)
            return value.strftime("%Y-%m-%d")
        return value
    
    def _calc_ra(self, ra_claim: int, ra_mm: int) -> float:
        """计算RA值"""
        if ra_mm == 0:
            return 0.0
        return round(ra_claim / ra_mm, 8)
    
    def _calc_share(self, value: int, total: int) -> float:
        """计算占比"""
        if total == 0:
            return 0.0
        return round(value / total, 4)

    def _sort_top_items(self, items: List[dict], sort_key: str) -> None:
        if sort_key == "claim":
            items.sort(
                key=lambda x: (x.get("ra_claim") or 0, x.get("ra") or 0),
                reverse=True
            )
        else:
            items.sort(
                key=lambda x: (x.get("ra") or 0, x.get("ra_claim") or 0),
                reverse=True
            )

    def _apply_detail_segment_filter(self, query, segments: Optional[List[str]]):
        """RA DETAIL 的 Segment 实际可能落在 segment2，查询时兼容两个字段。"""
        if not segments:
            return query
        return query.filter(
            or_(
                FactRaDetail.segment.in_(segments),
                FactRaDetail.segment2.in_(segments),
            )
        )

    def _resolve_detail_plants(
        self,
        start_date: date,
        end_date: date,
        odms: Optional[List[str]] = None,
        segments: Optional[List[str]] = None,
        models: Optional[List[str]] = None,
    ) -> Optional[List[str]]:
        """优先按当前 ROW 过滤范围动态解析 plant，避免静态映射缺失导致明细/Top Issue 少算。"""
        if not odms:
            return None

        row_query = self.db.query(FactRaRow.plant).filter(
            FactRaRow.claim_month >= start_date,
            FactRaRow.claim_month <= end_date,
            FactRaRow.supplier_new.in_(odms),
            FactRaRow.plant.isnot(None),
            func.trim(FactRaRow.plant) != "",
        )
        if segments:
            row_query = row_query.filter(FactRaRow.segment.in_(segments))
        if models:
            row_query = row_query.filter(FactRaRow.model.in_(models))

        plants = {
            plant.strip()
            for (plant,) in row_query.distinct().all()
            if plant and plant.strip()
        }

        map_query = self.db.query(MapOdmToPlant.plant).filter(
            MapOdmToPlant.kpi_type == "RA",
            MapOdmToPlant.supplier_new.in_(odms),
        )
        plants.update(
            plant.strip()
            for (plant,) in map_query.distinct().all()
            if plant and plant.strip()
        )

        return sorted(plants) if plants else ["__no_match__"]
    
    def _get_top_issue_by_model(
        self,
        start_date: date,
        end_date: date,
        models: List[str],
        segments: Optional[List[str]] = None,
        plant_list: Optional[List[str]] = None,
        top_n: int = 1
    
    ) -> dict:
        """获取每个Model的Top Issue列表（fault_category）"""
        if not models:
            return {}

        issue_query = self.db.query(
            FactRaDetail.model,
            FactRaDetail.fault_category,
            func.count().label("issue_count")
        ).filter(
            FactRaDetail.claim_month >= start_date,
            FactRaDetail.claim_month <= end_date,
            FactRaDetail.model.in_(models),
            FactRaDetail.fault_category.isnot(None),
            func.trim(FactRaDetail.fault_category) != ""
        )
        issue_query = self._apply_detail_segment_filter(issue_query, segments)
        if plant_list:
            issue_query = issue_query.filter(FactRaDetail.plant.in_(plant_list))

        issue_rows = issue_query.group_by(
            FactRaDetail.model, FactRaDetail.fault_category
        ).order_by(FactRaDetail.model, desc("issue_count")).all()

        totals_by_model = {}
        for r in issue_rows:
            totals_by_model[r.model] = totals_by_model.get(r.model, 0) + r.issue_count

        top_issues_by_model = {}
        for r in issue_rows:
            issues = top_issues_by_model.setdefault(r.model, [])
            if len(issues) >= top_n:
                continue
            total = totals_by_model.get(r.model, 0)
            issues.append(RaTopIssueRow(
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
    ) -> RaOptionsData:
        """
        获取RA筛选项
        支持任意组合过滤: 任一条件变化都会影响其他选项
        """
        # 获取月份范围 (RA时间主轴是claim_month)
        month_result = self.db.query(
            func.min(FactRaRow.claim_month).label("month_min"),
            func.max(FactRaRow.claim_month).label("month_max")
        ).first()
        
        month_min = self._format_month(month_result.month_min) if month_result.month_min else ""
        month_max = self._format_month(month_result.month_max) if month_result.month_max else ""
        
        # Segment列表 (根据odms和models过滤)
        segment_query = self.db.query(FactRaRow.segment).filter(FactRaRow.segment.isnot(None))
        if odms:
            segment_query = segment_query.filter(FactRaRow.supplier_new.in_(odms))
        if models:
            segment_query = segment_query.filter(FactRaRow.model.in_(models))
        segments_list = [r[0] for r in segment_query.distinct().order_by(FactRaRow.segment).all()]
        
        # ODM列表 (根据segments和models过滤)
        odm_query = self.db.query(FactRaRow.supplier_new).filter(FactRaRow.supplier_new.isnot(None))
        if segments:
            odm_query = odm_query.filter(FactRaRow.segment.in_(segments))
        if models:
            odm_query = odm_query.filter(FactRaRow.model.in_(models))
        odms_list = [r[0] for r in odm_query.distinct().order_by(FactRaRow.supplier_new).all()]
        
        # Model列表 (根据segments和odms过滤)
        model_query = self.db.query(FactRaRow.model).filter(FactRaRow.model.isnot(None))
        if segments:
            model_query = model_query.filter(FactRaRow.segment.in_(segments))
        if odms:
            model_query = model_query.filter(FactRaRow.supplier_new.in_(odms))
        models_list = [r[0] for r in model_query.distinct().order_by(FactRaRow.model).all()]
        
        return RaOptionsData(
            month_min=month_min,
            month_max=month_max,
            data_as_of=month_max,
            time_range={"min_month": month_min, "max_month": month_max},
            segments=segments_list,
            odms=odms_list,
            models=models_list
        )
    
    # ==================== ODM Analyze API ====================
    
    def analyze_odm(self, request: RaOdmAnalyzeRequest) -> RaOdmAnalyzeData:
        """RA ODM分析"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        view = request.view
        top_model_n = view.top_model_n if view else 10
        top_model_sort = view.top_model_sort if view else "claim"
        
        odms = request.filters.odms
        segments = request.filters.segments
        models = request.filters.models
        
        # Block D - ODM饼图汇总
        summary = None
        if len(odms) > 1:
            pie_query = self.db.query(
                FactRaRow.supplier_new,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.supplier_new.in_(odms)
            )
            if segments:
                pie_query = pie_query.filter(FactRaRow.segment.in_(segments))
            if models:
                pie_query = pie_query.filter(FactRaRow.model.in_(models))
            
            pie_data = pie_query.group_by(FactRaRow.supplier_new).all()
            total_claim = sum(r.ra_claim_sum for r in pie_data)
            
            odm_pie = [
                RaOdmPieRow(
                    odm=r.supplier_new,
                    ra=self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    share=self._calc_share(r.ra_claim_sum, total_claim),
                    ra_claim=r.ra_claim_sum,
                    ra_mm=r.ra_mm_sum
                )
                for r in pie_data
            ]
            summary = RaOdmSummary(odm_pie=odm_pie)
        
        # 为每个ODM生成卡片
        cards = []
        for odm in odms:
            plant_list = self._resolve_detail_plants(
                start_date=start_date,
                end_date=end_date,
                odms=[odm],
                segments=segments,
                models=models,
            )

            # Block A - 趋势 (返回完整数据)
            trend_query = self.db.query(
                FactRaRow.claim_month,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.supplier_new == odm
            )
            if segments:
                trend_query = trend_query.filter(FactRaRow.segment.in_(segments))
            if models:
                trend_query = trend_query.filter(FactRaRow.model.in_(models))
            
            trend_data = trend_query.group_by(FactRaRow.claim_month).order_by(FactRaRow.claim_month).all()
            
            trend = [
                RaTrendPoint(
                    month=self._format_month(r.claim_month),
                    ra=self._calc_ra(r.ra_claim_sum, r.ra_mm_sum)
                )
                for r in trend_data
            ]
            
            # Block B - Top Model (汇总)
            top_query = self.db.query(
                FactRaRow.model,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.supplier_new == odm,
                FactRaRow.model.isnot(None)
            )
            if segments:
                top_query = top_query.filter(FactRaRow.segment.in_(segments))
            if models:
                top_query = top_query.filter(FactRaRow.model.in_(models))
            
            top_data = top_query.group_by(FactRaRow.model).all()

            top_issues_map = self._get_top_issue_by_model(
                start_date=start_date,
                end_date=end_date,
                models=[r.model for r in top_data],
                segments=segments,
                plant_list=plant_list
            )
            
            top_models_raw = [
                {
                    "model": r.model,
                    "ra": self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    "ra_claim": r.ra_claim_sum,
                    "ra_mm": r.ra_mm_sum,
                    "top_issues": top_issues_map.get(r.model)
                }
                for r in top_data
            ]
            self._sort_top_items(top_models_raw, top_model_sort)
            
            top_models = [
                RaTopModelRow(rank=i+1, **item)
                for i, item in enumerate(top_models_raw[:top_model_n])
            ]
            
            # 月度明细 - Top Model
            monthly_query = self.db.query(
                FactRaRow.claim_month,
                FactRaRow.model,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.supplier_new == odm,
                FactRaRow.model.isnot(None)
            )
            if segments:
                monthly_query = monthly_query.filter(FactRaRow.segment.in_(segments))
            if models:
                monthly_query = monthly_query.filter(FactRaRow.model.in_(models))
            
            monthly_data = monthly_query.group_by(
                FactRaRow.claim_month, FactRaRow.model
            ).order_by(FactRaRow.claim_month).all()
            
            monthly_dict = {}
            for r in monthly_data:
                month_str = self._format_month(r.claim_month)
                if month_str not in monthly_dict:
                    monthly_dict[month_str] = []
                monthly_dict[month_str].append({
                    "model": r.model,
                    "ra": self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    "ra_claim": r.ra_claim_sum,
                    "ra_mm": r.ra_mm_sum,
                    "top_issues": top_issues_map.get(r.model)
                })
            
            monthly_top_models = []
            for month_str in sorted(monthly_dict.keys()):
                items = monthly_dict[month_str]
                month_date = self._parse_month(month_str)
                month_issue_map = self._get_top_issue_by_model(
                    start_date=month_date,
                    end_date=month_date,
                    models=[item["model"] for item in items],
                    segments=segments,
                    plant_list=plant_list
                )
                for item in items:
                    item["top_issues"] = month_issue_map.get(item["model"])
                self._sort_top_items(items, top_model_sort)
                monthly_top_models.append(RaMonthlyTopModels(
                    month=month_str,
                    items=[RaTopModelRow(rank=i+1, **item) for i, item in enumerate(items[:top_model_n])]
                ))
            
            cards.append(RaOdmCard(
                odm=odm,
                trend=trend,
                top_models=top_models,
                monthly_top_models=monthly_top_models,
                ai_summary=""
            ))
        
        max_month = self.db.query(func.max(FactRaRow.claim_month)).scalar()
        data_as_of = self._format_month(max_month) if max_month else request.time_range.end_month
        
        return RaOdmAnalyzeData(
            meta=RaAnalyzeMeta(data_as_of=data_as_of, time_range=request.time_range),
            summary=summary,
            cards=cards
        )
    
    # ==================== Segment Analyze API ====================
    
    def analyze_segment(self, request: RaSegmentAnalyzeRequest) -> RaSegmentAnalyzeData:
        """RA Segment分析"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        view = request.view
        top_n = view.top_n if view else 10
        top_odm_sort = view.top_odm_sort if view else "claim"
        top_model_sort = view.top_model_sort if view else "claim"
        
        segments = request.filters.segments
        odms = request.filters.odms
        models = request.filters.models
        
        # Block D - Segment饼图汇总
        summary = None
        if len(segments) > 1:
            pie_query = self.db.query(
                FactRaRow.segment,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.segment.in_(segments)
            )
            if odms:
                pie_query = pie_query.filter(FactRaRow.supplier_new.in_(odms))
            if models:
                pie_query = pie_query.filter(FactRaRow.model.in_(models))
            
            pie_data = pie_query.group_by(FactRaRow.segment).all()
            total_claim = sum(r.ra_claim_sum for r in pie_data)
            
            segment_pie = [
                RaSegmentPieRow(
                    segment=r.segment,
                    ra=self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    share=self._calc_share(r.ra_claim_sum, total_claim),
                    ra_claim=r.ra_claim_sum,
                    ra_mm=r.ra_mm_sum
                )
                for r in pie_data
            ]
            summary = RaSegmentSummary(segment_pie=segment_pie)
        
        # 为每个Segment生成卡片
        cards = []
        for segment in segments:
            # Block A - 趋势 (返回完整数据)
            trend_query = self.db.query(
                FactRaRow.claim_month,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.segment == segment
            )
            if odms:
                trend_query = trend_query.filter(FactRaRow.supplier_new.in_(odms))
            if models:
                trend_query = trend_query.filter(FactRaRow.model.in_(models))
            
            trend_data = trend_query.group_by(FactRaRow.claim_month).order_by(FactRaRow.claim_month).all()
            
            trend = [
                RaTrendPoint(
                    month=self._format_month(r.claim_month),
                    ra=self._calc_ra(r.ra_claim_sum, r.ra_mm_sum)
                )
                for r in trend_data
            ]  # 返回完整数据
            
            # Block B - Top ODM (汇总)
            odm_query = self.db.query(
                FactRaRow.supplier_new,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.segment == segment,
                FactRaRow.supplier_new.isnot(None)
            )
            if odms:
                odm_query = odm_query.filter(FactRaRow.supplier_new.in_(odms))
            if models:
                odm_query = odm_query.filter(FactRaRow.model.in_(models))
            
            odm_data = odm_query.group_by(FactRaRow.supplier_new).all()
            odm_raw = [
                {"odm": r.supplier_new, "ra": self._calc_ra(r.ra_claim_sum, r.ra_mm_sum), "ra_claim": r.ra_claim_sum, "ra_mm": r.ra_mm_sum}
                for r in odm_data
            ]
            self._sort_top_items(odm_raw, top_odm_sort)
            top_odms = [RaTopOdmRow(rank=i+1, **item) for i, item in enumerate(odm_raw[:top_n])]
            
            # Block B - Top Model (汇总)
            model_query = self.db.query(
                FactRaRow.model,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.segment == segment,
                FactRaRow.model.isnot(None)
            )
            if odms:
                model_query = model_query.filter(FactRaRow.supplier_new.in_(odms))
            if models:
                model_query = model_query.filter(FactRaRow.model.in_(models))
            
            model_data = model_query.group_by(FactRaRow.model).all()

            seg_plant_list = self._resolve_detail_plants(
                start_date=start_date,
                end_date=end_date,
                odms=odms,
                segments=[segment],
                models=models,
            )

            seg_top_issues_map = self._get_top_issue_by_model(
                start_date=start_date,
                end_date=end_date,
                models=[r.model for r in model_data],
                segments=[segment],
                plant_list=seg_plant_list
            )

            model_raw = [
                {
                    "model": r.model,
                    "ra": self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    "ra_claim": r.ra_claim_sum,
                    "ra_mm": r.ra_mm_sum,
                    "top_issues": seg_top_issues_map.get(r.model)
                }
                for r in model_data
            ]
            self._sort_top_items(model_raw, top_model_sort)
            top_models = [RaTopModelRow(rank=i+1, **item) for i, item in enumerate(model_raw[:top_n])]
            
            # 月度明细 - Top ODM
            monthly_odm_query = self.db.query(
                FactRaRow.claim_month,
                FactRaRow.supplier_new,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.segment == segment,
                FactRaRow.supplier_new.isnot(None)
            )
            if odms:
                monthly_odm_query = monthly_odm_query.filter(FactRaRow.supplier_new.in_(odms))
            if models:
                monthly_odm_query = monthly_odm_query.filter(FactRaRow.model.in_(models))
            
            monthly_odm_data = monthly_odm_query.group_by(
                FactRaRow.claim_month, FactRaRow.supplier_new
            ).order_by(FactRaRow.claim_month).all()
            
            monthly_odm_dict = {}
            for r in monthly_odm_data:
                month_str = self._format_month(r.claim_month)
                if month_str not in monthly_odm_dict:
                    monthly_odm_dict[month_str] = []
                monthly_odm_dict[month_str].append({
                    "odm": r.supplier_new,
                    "ra": self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    "ra_claim": r.ra_claim_sum,
                    "ra_mm": r.ra_mm_sum
                })
            
            monthly_top_odms = []
            for month_str in sorted(monthly_odm_dict.keys()):
                items = monthly_odm_dict[month_str]
                self._sort_top_items(items, top_odm_sort)
                monthly_top_odms.append(RaMonthlyTopOdms(
                    month=month_str,
                    items=[RaTopOdmRow(rank=i+1, **item) for i, item in enumerate(items[:top_n])]
                ))
            
            # 月度明细 - Top Model
            monthly_model_query = self.db.query(
                FactRaRow.claim_month,
                FactRaRow.model,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.segment == segment,
                FactRaRow.model.isnot(None)
            )
            if odms:
                monthly_model_query = monthly_model_query.filter(FactRaRow.supplier_new.in_(odms))
            if models:
                monthly_model_query = monthly_model_query.filter(FactRaRow.model.in_(models))
            
            monthly_model_data = monthly_model_query.group_by(
                FactRaRow.claim_month, FactRaRow.model
            ).order_by(FactRaRow.claim_month).all()
            
            monthly_model_dict = {}
            for r in monthly_model_data:
                month_str = self._format_month(r.claim_month)
                if month_str not in monthly_model_dict:
                    monthly_model_dict[month_str] = []
                monthly_model_dict[month_str].append({
                    "model": r.model,
                    "ra": self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    "ra_claim": r.ra_claim_sum,
                    "ra_mm": r.ra_mm_sum,
                    "top_issues": seg_top_issues_map.get(r.model)
                })
            
            monthly_top_models = []
            for month_str in sorted(monthly_model_dict.keys()):
                items = monthly_model_dict[month_str]
                month_date = self._parse_month(month_str)
                month_issue_map = self._get_top_issue_by_model(
                    start_date=month_date,
                    end_date=month_date,
                    models=[item["model"] for item in items],
                    segments=[segment],
                    plant_list=seg_plant_list
                )
                for item in items:
                    item["top_issues"] = month_issue_map.get(item["model"])
                self._sort_top_items(items, top_model_sort)
                monthly_top_models.append(RaMonthlyTopModels(
                    month=month_str,
                    items=[RaTopModelRow(rank=i+1, **item) for i, item in enumerate(items[:top_n])]
                ))
            
            cards.append(RaSegmentCard(
                segment=segment,
                trend=trend,
                top_odms=top_odms,
                top_models=top_models,
                monthly_top_odms=monthly_top_odms,
                monthly_top_models=monthly_top_models,
                ai_summary=""
            ))
        
        max_month = self.db.query(func.max(FactRaRow.claim_month)).scalar()
        data_as_of = self._format_month(max_month) if max_month else request.time_range.end_month
        
        return RaSegmentAnalyzeData(
            meta=RaAnalyzeMeta(data_as_of=data_as_of, time_range=request.time_range),
            summary=summary,
            cards=cards
        )
    
    # ==================== Model Analyze API ====================
    
    def analyze_model(self, request: RaModelAnalyzeRequest) -> RaModelAnalyzeData:
        """RA Model分析 - 使用DETAIL表获取Top Issue"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        view = request.view
        top_issue_n = view.top_issue_n if view else 10
        
        models_list = request.filters.models
        segments = list(request.filters.segments or [])
        if request.filters.segment and request.filters.segment not in segments:
            segments.append(request.filters.segment)
        segments = segments or None
        odms = request.filters.odms
        
        plant_list = self._resolve_detail_plants(
            start_date=start_date,
            end_date=end_date,
            odms=odms,
            segments=segments,
            models=models_list,
        )
        
        # Block D - Model饼图汇总
        summary = None
        if len(models_list) > 1:
            pie_query = self.db.query(
                FactRaRow.model,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.model.in_(models_list)
            )
            if segments:
                pie_query = pie_query.filter(FactRaRow.segment.in_(segments))
            if odms:
                pie_query = pie_query.filter(FactRaRow.supplier_new.in_(odms))
            
            pie_data = pie_query.group_by(FactRaRow.model).all()
            total_claim = sum(r.ra_claim_sum for r in pie_data)
            
            model_pie = [
                RaModelPieRow(
                    model=r.model,
                    ra=self._calc_ra(r.ra_claim_sum, r.ra_mm_sum),
                    share=self._calc_share(r.ra_claim_sum, total_claim),
                    ra_claim=r.ra_claim_sum,
                    ra_mm=r.ra_mm_sum
                )
                for r in pie_data
            ]
            summary = RaModelSummary(model_pie=model_pie)
        
        # 为每个Model生成卡片
        cards = []
        for model in models_list:
            # Block A - 趋势 (返回完整数据)
            trend_query = self.db.query(
                FactRaRow.claim_month,
                func.sum(FactRaRow.ra_claim).label("ra_claim_sum"),
                func.sum(FactRaRow.ra_mm).label("ra_mm_sum")
            ).filter(
                FactRaRow.claim_month >= start_date,
                FactRaRow.claim_month <= end_date,
                FactRaRow.model == model
            )
            if segments:
                trend_query = trend_query.filter(FactRaRow.segment.in_(segments))
            if odms:
                trend_query = trend_query.filter(FactRaRow.supplier_new.in_(odms))
            
            trend_data = trend_query.group_by(FactRaRow.claim_month).order_by(FactRaRow.claim_month).all()
            
            trend = [
                RaTrendPoint(
                    month=self._format_month(r.claim_month),
                    ra=self._calc_ra(r.ra_claim_sum, r.ra_mm_sum)
                )
                for r in trend_data
            ]  # 返回完整数据
            
            # Block B - Top Issue (从DETAIL表，汇总)
            issue_query = self.db.query(
                FactRaDetail.fault_category,
                func.count().label("issue_count")
            ).filter(
                FactRaDetail.claim_month >= start_date,
                FactRaDetail.claim_month <= end_date,
                FactRaDetail.model == model,
                FactRaDetail.fault_category.isnot(None),
                func.trim(FactRaDetail.fault_category) != ""
            )
            issue_query = self._apply_detail_segment_filter(issue_query, segments)
            if plant_list:
                issue_query = issue_query.filter(FactRaDetail.plant.in_(plant_list))
            
            issue_data = issue_query.group_by(FactRaDetail.fault_category).order_by(desc("issue_count")).limit(top_issue_n).all()
            
            total_issues = sum(r.issue_count for r in issue_data)
            top_issues = [
                RaTopIssueRow(
                    rank=i + 1,
                    issue=r.fault_category,
                    count=r.issue_count,
                    share=self._calc_share(r.issue_count, total_issues) if total_issues > 0 else 0
                )
                for i, r in enumerate(issue_data)
            ]
            
            # 月度明细 - Top Issue
            monthly_issue_query = self.db.query(
                FactRaDetail.claim_month,
                FactRaDetail.fault_category,
                func.count().label("issue_count")
            ).filter(
                FactRaDetail.claim_month >= start_date,
                FactRaDetail.claim_month <= end_date,
                FactRaDetail.model == model,
                FactRaDetail.fault_category.isnot(None),
                func.trim(FactRaDetail.fault_category) != ""
            )
            monthly_issue_query = self._apply_detail_segment_filter(monthly_issue_query, segments)
            if plant_list:
                monthly_issue_query = monthly_issue_query.filter(FactRaDetail.plant.in_(plant_list))
            
            monthly_issue_data = monthly_issue_query.group_by(
                FactRaDetail.claim_month, FactRaDetail.fault_category
            ).order_by(FactRaDetail.claim_month).all()
            
            monthly_issue_dict = {}
            for r in monthly_issue_data:
                month_str = self._format_month(r.claim_month)
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
                monthly_top_issues.append(RaMonthlyTopIssues(
                    month=month_str,
                    items=[
                        RaTopIssueRow(
                            rank=i+1,
                            issue=item["issue"],
                            count=item["count"],
                            share=self._calc_share(item["count"], month_total) if month_total > 0 else 0
                        )
                        for i, item in enumerate(items[:top_issue_n])
                    ]
                ))
            
            cards.append(RaModelCard(
                model=model,
                trend=trend,
                top_issues=top_issues,
                monthly_top_issues=monthly_top_issues,
                ai_summary=""
            ))
        
        max_month = self.db.query(func.max(FactRaRow.claim_month)).scalar()
        data_as_of = self._format_month(max_month) if max_month else request.time_range.end_month
        
        return RaModelAnalyzeData(
            meta=RaAnalyzeMeta(data_as_of=data_as_of, time_range=request.time_range),
            summary=summary,
            cards=cards
        )

    # ==================== Model Issue Details API ====================

    def get_model_issue_details(self, request: RaModelIssueRequest) -> RaModelIssueDetailData:
        """RA Model Issue明细查询"""
        start_date = self._parse_month(request.time_range.start_month)
        end_date = self._parse_month(request.time_range.end_month)
        model = request.filters.model
        issue = request.filters.issue
        month = request.filters.month
        segments = request.filters.segments
        odms = request.filters.odms
        page = request.pagination.page if request.pagination else 1
        page_size = request.pagination.page_size if request.pagination else 10

        plant_list = self._resolve_detail_plants(
            start_date=start_date,
            end_date=end_date,
            odms=odms,
            segments=segments,
            models=[model],
        )

        query = self.db.query(FactRaDetail).filter(
            FactRaDetail.claim_month >= start_date,
            FactRaDetail.claim_month <= end_date,
            FactRaDetail.model == model,
            FactRaDetail.fault_category == issue
        )
        if month:
            query = query.filter(FactRaDetail.claim_month == self._parse_month(month))
        query = self._apply_detail_segment_filter(query, segments)
        if plant_list:
            query = query.filter(FactRaDetail.plant.in_(plant_list))

        total = query.count()
        rows = query.order_by(FactRaDetail.claim_month.desc()).offset((page - 1) * page_size).limit(page_size).all()

        items = [
            RaModelIssueDetailRow(
                model=r.model,
                fault_category=r.fault_category,
                problem_descr_by_tech=r.problem_descr_by_tech,
                claim_nbr=r.claim_nbr,
                claim_month=self._format_month(r.claim_month),
                plant=r.plant
            )
            for r in rows
        ]
        return RaModelIssueDetailData(total=total, page=page, page_size=page_size, items=items)

    # ==================== Report Generation ====================

    RA_DETAIL_COLUMNS = [
        ("Claim_Nbr", "claim_nbr"),
        ("Claim_Month", "claim_month"),
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

    def _get_detail_for_report(
        self,
        start_date: date,
        end_date: date,
        models: Optional[List[str]] = None,
        segments: Optional[List[str]] = None,
        odms: Optional[List[str]] = None,
        max_rows: int = 100000,
    ) -> Tuple[list, int, bool]:
        """获取 RA Detail 全量数据（供报告使用）"""
        detail_fields = [getattr(FactRaDetail, key) for _, key in self.RA_DETAIL_COLUMNS]

        query = self.db.query(*detail_fields).filter(
            FactRaDetail.claim_month >= start_date,
            FactRaDetail.claim_month <= end_date,
        )

        if models:
            query = query.filter(FactRaDetail.model.in_(models))
        query = self._apply_detail_segment_filter(query, segments)

        plant_list = self._resolve_detail_plants(
            start_date, end_date, odms=odms, segments=segments, models=models
        )
        if plant_list:
            query = query.filter(FactRaDetail.plant.in_(plant_list))

        col_keys = [k for _, k in self.RA_DETAIL_COLUMNS]
        detail = []
        truncated = False
        for idx, r in enumerate(
            query.order_by(FactRaDetail.claim_month.desc()).limit(max_rows + 1)
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

    def generate_model_report(self, request: RaModelReportRequest) -> Tuple[str, str]:
        from tempfile import NamedTemporaryFile
        from app.services.report_chart import generate_trend_chart, generate_pie_chart
        from app.services.report_excel import ReportExcelBuilder, build_report_filename

        analyze_req = RaModelAnalyzeRequest(
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

        trend_entities = [
            {"name": c.model, "trend": [{"month": t.month, "value": t.ra} for t in c.trend]}
            for c in data.cards
        ]
        trend_png = generate_trend_chart(trend_entities, tgt=request.tgt,
                                          value_label="RA", title="RA Model 趋势对比")

        pie_png = None
        pie_table = []
        if data.summary and data.summary.model_pie:
            pie_items = [{"name": p.model, "value": p.ra * 1_000_000, "share": p.share}
                         for p in data.summary.model_pie]
            pie_png = generate_pie_chart(pie_items, value_label="RA", title="Model RA 占比")
            pie_table = [
                {"name": p.model, "dppm": round(p.ra * 1_000_000),
                 "share": p.share, "ra_claim": p.ra_claim, "ra_mm": p.ra_mm}
                for p in data.summary.model_pie
            ]

        builder = ReportExcelBuilder(kpi_type="RA", dimension="Model")
        builder.add_info_sheet(meta={
            "data_as_of": data.meta.data_as_of,
            "time_range": f"{request.time_range.start_month} ~ {request.time_range.end_month}",
            "entities": ", ".join(request.filters.models),
            "extra_filters": {
                "筛选Segment": ", ".join(request.filters.segments) if request.filters.segments else "全部",
                "筛选ODM": ", ".join(request.filters.odms) if request.filters.odms else "全部",
            },
        }, tgt=request.tgt)

        ra_trend = [
            {"name": e["name"], "trend": e["trend"]} for e in trend_entities
        ]
        builder.add_trend_sheet(ra_trend, trend_png, value_key="ra", unit_label="RA")

        cards_dict = [c.dict() if hasattr(c, 'dict') else c.model_dump() for c in data.cards]
        builder.add_top_issue_sheet(cards_dict, entity_key="model")
        builder.add_monthly_top_issue_sheet(cards_dict, entity_key="model")
        builder.add_detail_sheet(detail_rows, self.RA_DETAIL_COLUMNS, detail_total, truncated)

        if pie_png:
            builder.add_comparison_sheet(pie_table, pie_png, entity_key="name",
                                          value_label="RA", claim_key="ra_claim", mm_key="ra_mm")

        filename = build_report_filename("RA", "Model", request.filters.models,
                                          request.time_range.start_month, request.time_range.end_month)
        with NamedTemporaryFile(prefix="ra-model-", suffix=".xlsx", delete=False) as tmp:
            builder.save_to_file(tmp.name)
            return tmp.name, filename

    def generate_odm_report(self, request: RaOdmReportRequest) -> Tuple[str, str]:
        from tempfile import NamedTemporaryFile
        from app.services.report_chart import generate_trend_chart, generate_pie_chart
        from app.services.report_excel import ReportExcelBuilder, build_report_filename

        analyze_req = RaOdmAnalyzeRequest(
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
            {"name": c.odm, "trend": [{"month": t.month, "value": t.ra} for t in c.trend]}
            for c in data.cards
        ]
        trend_png = generate_trend_chart(trend_entities, tgt=request.tgt,
                                          value_label="RA", title="RA ODM 趋势对比")

        pie_png = None
        pie_table = []
        if data.summary and data.summary.odm_pie:
            pie_items = [{"name": p.odm, "value": p.ra * 1_000_000, "share": p.share}
                         for p in data.summary.odm_pie]
            pie_png = generate_pie_chart(pie_items, value_label="RA", title="ODM RA 占比")
            pie_table = [
                {"name": p.odm, "dppm": round(p.ra * 1_000_000),
                 "share": p.share, "ra_claim": p.ra_claim, "ra_mm": p.ra_mm}
                for p in data.summary.odm_pie
            ]

        builder = ReportExcelBuilder(kpi_type="RA", dimension="ODM")
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
        builder.add_trend_sheet(trend_entities, trend_png, value_key="ra", unit_label="RA")

        cards_dict = [c.dict() if hasattr(c, 'dict') else c.model_dump() for c in data.cards]
        builder.add_top_model_sheet(cards_dict, entity_key="odm", value_label="RA",
                                     claim_key="ra_claim", mm_key="ra_mm")
        builder.add_monthly_top_model_sheet(cards_dict, entity_key="odm", value_label="RA",
                                             claim_key="ra_claim", mm_key="ra_mm")
        builder.add_detail_sheet(detail_rows, self.RA_DETAIL_COLUMNS, detail_total, truncated)

        if pie_png:
            builder.add_comparison_sheet(pie_table, pie_png, entity_key="name",
                                          value_label="RA", claim_key="ra_claim", mm_key="ra_mm")

        filename = build_report_filename("RA", "ODM", request.filters.odms,
                                          request.time_range.start_month, request.time_range.end_month)
        with NamedTemporaryFile(prefix="ra-odm-", suffix=".xlsx", delete=False) as tmp:
            builder.save_to_file(tmp.name)
            return tmp.name, filename

    def generate_segment_report(self, request: RaSegmentReportRequest) -> Tuple[str, str]:
        from tempfile import NamedTemporaryFile
        from app.services.report_chart import generate_trend_chart, generate_pie_chart
        from app.services.report_excel import ReportExcelBuilder, build_report_filename

        analyze_req = RaSegmentAnalyzeRequest(
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
            {"name": c.segment, "trend": [{"month": t.month, "value": t.ra} for t in c.trend]}
            for c in data.cards
        ]
        trend_png = generate_trend_chart(trend_entities, tgt=request.tgt,
                                          value_label="RA", title="RA Segment 趋势对比")

        pie_png = None
        pie_table = []
        if data.summary and data.summary.segment_pie:
            pie_items = [{"name": p.segment, "value": p.ra * 1_000_000, "share": p.share}
                         for p in data.summary.segment_pie]
            pie_png = generate_pie_chart(pie_items, value_label="RA", title="Segment RA 占比")
            pie_table = [
                {"name": p.segment, "dppm": round(p.ra * 1_000_000),
                 "share": p.share, "ra_claim": p.ra_claim, "ra_mm": p.ra_mm}
                for p in data.summary.segment_pie
            ]

        builder = ReportExcelBuilder(kpi_type="RA", dimension="Segment")
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
        builder.add_trend_sheet(trend_entities, trend_png, value_key="ra", unit_label="RA")

        cards_dict = [c.dict() if hasattr(c, 'dict') else c.model_dump() for c in data.cards]
        builder.add_top_odm_sheet(cards_dict, value_label="RA",
                                   claim_key="ra_claim", mm_key="ra_mm")
        builder.add_monthly_top_odm_sheet(cards_dict, value_label="RA",
                                           claim_key="ra_claim", mm_key="ra_mm")
        builder.add_top_model_sheet(cards_dict, entity_key="segment", value_label="RA",
                                     claim_key="ra_claim", mm_key="ra_mm")
        builder.add_monthly_top_model_sheet(cards_dict, entity_key="segment", value_label="RA",
                                             claim_key="ra_claim", mm_key="ra_mm")
        builder.add_detail_sheet(detail_rows, self.RA_DETAIL_COLUMNS, detail_total, truncated)

        if pie_png:
            builder.add_comparison_sheet(pie_table, pie_png, entity_key="name",
                                          value_label="RA", claim_key="ra_claim", mm_key="ra_mm")

        filename = build_report_filename("RA", "Segment", request.filters.segments,
                                          request.time_range.start_month, request.time_range.end_month)
        with NamedTemporaryFile(prefix="ra-seg-", suffix=".xlsx", delete=False) as tmp:
            builder.save_to_file(tmp.name)
            return tmp.name, filename
