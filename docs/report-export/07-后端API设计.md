# 后端API设计 - 报告导出

## 一、新增API总览

| 接口 | 方法 | 路径 | 说明 |
|------|------|------|------|
| IFIR Model报告 | POST | `/ifir/report/model` | IFIR Model分析报告 |
| IFIR ODM报告 | POST | `/ifir/report/odm` | IFIR ODM分析报告 |
| IFIR Segment报告 | POST | `/ifir/report/segment` | IFIR Segment分析报告 |
| RA Model报告 | POST | `/ra/report/model` | RA Model分析报告 |
| RA ODM报告 | POST | `/ra/report/odm` | RA ODM分析报告 |
| RA Segment报告 | POST | `/ra/report/segment` | RA Segment分析报告 |

所有接口均需认证（`Depends(get_current_user)`），返回 Excel 文件流。

## 二、请求Schema定义

### 2.1 IFIR 报告请求

```python
# backend/app/schemas/ifir.py 新增

class IfirModelReportRequest(BaseModel):
    """IFIR Model分析报告请求"""
    time_range: TimeRange
    filters: IfirModelFilters       # models(必选), segments, odms
    tgt: Optional[int] = 1500       # TGT目标值(DPPM)

class IfirOdmReportRequest(BaseModel):
    """IFIR ODM分析报告请求"""
    time_range: TimeRange
    filters: IfirOdmFilters         # odms(必选), segments, models
    view: Optional[IfirOdmViewConfig] = None
    tgt: Optional[int] = 1500

class IfirSegmentReportRequest(BaseModel):
    """IFIR Segment分析报告请求"""
    time_range: TimeRange
    filters: IfirSegmentFilters     # segments(必选), odms, models
    view: Optional[IfirSegmentViewConfig] = None
    tgt: Optional[int] = 1500
```

### 2.2 RA 报告请求

```python
# backend/app/schemas/ra.py 新增

class RaModelReportRequest(BaseModel):
    """RA Model分析报告请求"""
    time_range: TimeRange
    filters: RaModelFilters         # models(必选), segments, odms
    tgt: Optional[int] = 1500

class RaOdmReportRequest(BaseModel):
    """RA ODM分析报告请求"""
    time_range: TimeRange
    filters: RaOdmFilters           # odms(必选), segments, models
    view: Optional[RaOdmViewConfig] = None
    tgt: Optional[int] = 1500

class RaSegmentReportRequest(BaseModel):
    """RA Segment分析报告请求"""
    time_range: TimeRange
    filters: RaSegmentFilters       # segments(必选), odms, models
    view: Optional[RaSegmentViewConfig] = None
    tgt: Optional[int] = 1500
```

## 三、响应格式

所有报告接口均返回 **Excel文件下载响应**（成功时为 Excel，失败时为 JSON）：

```python
from pathlib import Path
from urllib.parse import quote
from fastapi import BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse

@router.post("/report/model")
async def generate_model_report(
    request: IfirModelReportRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    try:
        service = IfirService(db)
        file_path, filename = service.generate_model_report(request)
        
        path = Path(file_path)
        background_tasks.add_task(path.unlink, missing_ok=True)
        
        return FileResponse(
            path=path,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={
                "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
            },
            background=background_tasks,
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"code": 500, "message": str(e)}
        )
```

## 四、路由注册

### 4.1 新增路由文件

建议在现有 `ifir.py` 和 `ra.py` 路由文件中直接追加报告接口，无需新建路由文件。

### 4.2 IFIR 路由追加 (backend/app/api/ifir.py)

```python
# ==================== Report API ====================

@router.post("/report/model")
async def generate_ifir_model_report(request, db, current_user):
    ...

@router.post("/report/odm")
async def generate_ifir_odm_report(request, db, current_user):
    ...

@router.post("/report/segment")
async def generate_ifir_segment_report(request, db, current_user):
    ...
```

### 4.3 RA 路由追加 (backend/app/api/ra.py)

```python
# ==================== Report API ====================

@router.post("/report/model")
async def generate_ra_model_report(request, db, current_user):
    ...

@router.post("/report/odm")
async def generate_ra_odm_report(request, db, current_user):
    ...

@router.post("/report/segment")
async def generate_ra_segment_report(request, db, current_user):
    ...
```

## 五、Service层新增方法

### 5.1 IfirService 新增

```python
class IfirService:
    # 已有方法：analyze_odm, analyze_segment, analyze_model, get_model_issue_details
    
    # ====== 新增方法 ======
    
    def generate_model_report(self, request: IfirModelReportRequest) -> Tuple[str, str]:
        """生成IFIR Model分析报告Excel"""
        # 1. 获取分析数据（复用 analyze_model）
        # 2. 获取Detail导出数据（复用现有过滤逻辑）
        # 3. 生成图表
        # 4. 构建Excel
        # 5. 落盘到临时文件
        # 6. 返回 (临时文件路径, 下载文件名)
    
    def generate_odm_report(self, request: IfirOdmReportRequest) -> Tuple[str, str]:
        """生成IFIR ODM分析报告Excel"""
    
    def generate_segment_report(self, request: IfirSegmentReportRequest) -> Tuple[str, str]:
        """生成IFIR Segment分析报告Excel"""
    
    def _get_detail_for_report(self, start_date, end_date, 
                                models=None, segments=None, odms=None,
                                max_rows=200000) -> tuple:
        """获取IFIR Detail全量数据（供报告使用）
        
        通用方法，根据提供的过滤条件查询 fact_ifir_detail
        - models: 直接过滤 model 字段
        - segments: 过滤 segment 或 segment2（兼容）
        - odms: 复用现有 Service 的动态 plant 解析逻辑后过滤 plant
        - max_rows: 最大导出行数（防止超大导出）
        """
```

### 5.2 RaService 新增

结构与 IfirService 完全对称：

```python
class RaService:
    def generate_model_report(self, request: RaModelReportRequest) -> Tuple[str, str]:
    def generate_odm_report(self, request: RaOdmReportRequest) -> Tuple[str, str]:
    def generate_segment_report(self, request: RaSegmentReportRequest) -> Tuple[str, str]:
    def _get_detail_for_report(self, ...) -> tuple:
```

## 六、Detail全量查询方法设计

这是报告功能最关键的新增查询，因为现有 issue-details 接口只支持单个Model + 单个Issue + 分页，而报告需要全量数据。

### 6.1 通用签名

```python
def _get_detail_for_report(
    self,
    start_date: date,
    end_date: date,
    models: Optional[List[str]] = None,
    segments: Optional[List[str]] = None,
    odms: Optional[List[str]] = None,
    max_rows: int = 200000
) -> Tuple[List[dict], int, bool]:
    """
    返回:
        - rows: Detail行列表（dict格式）
        - total: 实际导出前探测到的总行数（或截断下限）
        - truncated: 是否被截断
    """
```

### 6.2 IFIR Detail查询

```python
query = self.db.query(
    FactIfirDetail.claim_nbr,
    FactIfirDetail.claim_month,
    FactIfirDetail.delivery_month,
    FactIfirDetail.model,
    FactIfirDetail.segment,
    FactIfirDetail.plant,
    FactIfirDetail.fault_category,
    FactIfirDetail.problem_descr_by_tech,
    FactIfirDetail.failure_code,
    FactIfirDetail.mtm,
    FactIfirDetail.serial_nbr,
    FactIfirDetail.geo_2012,
    FactIfirDetail.commodity,
    FactIfirDetail.part_nbr,
    FactIfirDetail.part_desc,
    FactIfirDetail.part_supplier,
).filter(
    FactIfirDetail.delivery_month >= start_date,
    FactIfirDetail.delivery_month <= end_date,
)

if models:
    query = query.filter(FactIfirDetail.model.in_(models))
query = self._apply_detail_segment_filter(query, segments)

plant_list = self._resolve_detail_plants(
    start_date=start_date,
    end_date=end_date,
    odms=odms,
    segments=segments,
    models=models,
)
if plant_list:
    query = query.filter(FactIfirDetail.plant.in_(plant_list))

rows = query.order_by(FactIfirDetail.delivery_month.desc()).limit(max_rows + 1).all()
truncated = len(rows) > max_rows
if truncated:
    rows = rows[:max_rows]
total = max_rows + 1 if truncated else len(rows)
```

### 6.3 RA Detail查询

```python
# 同上结构，差异：
# - 无 delivery_month 字段
# - 时间过滤用 claim_month
# - order_by 用 claim_month
```

## 七、超时与性能考虑

| 场景 | 预估耗时 | 优化策略 |
|------|---------|---------|
| 分析数据查询 | 1-3s | 复用已有方法 |
| Detail导出查询(5万行) | 3-8s | 指定列查询、限制行数、避免额外 `count()` 全表扫描 |
| matplotlib图表生成(2-3张) | 1-2s | 使用Agg后端，无GUI |
| Excel生成(含图片嵌入) | 2-5s | 直接写临时文件，避免再复制一份完整 bytes |
| **总计** | **7-18s** | - |

**建议**:
- 前端设置 60~120 秒超时（按接口单独配置）
- 添加加载状态提示（"正在生成报告，请稍候..."）
- Detail数据上限 200,000 行，超出截断
- 后端matplotlib使用非交互式后端 `matplotlib.use('Agg')`
- 如果稳定超过 120 秒，升级为异步任务导出，不继续堆高同步超时
