"""
IFIR分析服务
"""
from datetime import date
from typing import Optional, List
from sqlalchemy import func, desc
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
    MonthlyTopIssues
)
from app.schemas.common import TimeRange


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
        cards = []
        for odm in odms:
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
            
            # 计算IFIR并排序
            top_models_raw = [
                {
                    "model": r.model,
                    "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum),
                    "box_claim": r.box_claim_sum,
                    "box_mm": r.box_mm_sum
                }
                for r in top_data
            ]
            top_models_raw.sort(key=lambda x: x["ifir"], reverse=True)
            
            top_models = [
                TopModelRow(
                    rank=i + 1,
                    model=item["model"],
                    ifir=item["ifir"],
                    box_claim=item["box_claim"],
                    box_mm=item["box_mm"]
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
                    "box_mm": r.box_mm_sum
                })
            
            # 每个月取Top N
            monthly_top_models = []
            for month_str in sorted(monthly_dict.keys()):
                items = monthly_dict[month_str]
                items.sort(key=lambda x: x["ifir"], reverse=True)
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
        
        segments = request.filters.segments
        odms = request.filters.odms
        models = request.filters.models
        
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
            odm_raw.sort(key=lambda x: x["ifir"], reverse=True)
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
            model_raw = [
                {"model": r.model, "ifir": self._calc_ifir(r.box_claim_sum, r.box_mm_sum), "box_claim": r.box_claim_sum, "box_mm": r.box_mm_sum}
                for r in model_data
            ]
            model_raw.sort(key=lambda x: x["ifir"], reverse=True)
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
                items.sort(key=lambda x: x["ifir"], reverse=True)
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
                    "box_mm": r.box_mm_sum
                })
            
            monthly_top_models = []
            for month_str in sorted(monthly_model_dict.keys()):
                items = monthly_model_dict[month_str]
                items.sort(key=lambda x: x["ifir"], reverse=True)
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
            plant_list = [r[0] for r in plant_query.all()]
        
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
            if segments:
                issue_query = issue_query.filter(FactIfirDetail.segment.in_(segments))
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
            if segments:
                monthly_issue_query = monthly_issue_query.filter(FactIfirDetail.segment.in_(segments))
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
