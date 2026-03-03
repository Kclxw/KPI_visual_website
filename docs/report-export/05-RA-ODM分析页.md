# RA ODM分析页 - 报告导出设计

## 一、页面现状

**路径**: `frontend/src/pages/ra/OdmAnalysisPage.vue`
**组件**: `frontend/src/components/kpi/ra/odm/RaOdmCard.vue`
**API**: `POST /ra/odm-analysis/analyze`

### 与 IFIR ODM 页的差异

| 差异项 | IFIR ODM | RA ODM |
|--------|----------|--------|
| KPI指标 | ifir / box_claim / box_mm | ra / ra_claim / ra_mm |
| 时间主轴 | delivery_month | claim_month |
| Detail表 | fact_ifir_detail | fact_ra_detail |
| 排序选项 | "claim" \| "ifir" | "claim" \| "ra" |

### 筛选参数
| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| time_range | {start_month, end_month} | 是 | 时间范围 |
| odms | string[] | 是 | 选中的ODM列表 |
| segments | string[] | 否 | 可选Segment过滤 |
| models | string[] | 否 | 可选Model过滤 |
| top_model_sort | "claim" \| "ra" | 否 | Top Model排序方式 |
| tgt | number | 否 | TGT目标值(DPPM) |

## 二、Excel报告结构

### 共6个Sheet，结构与 IFIR ODM 页对应：

| Sheet | 内容 | 差异 |
|-------|------|------|
| 1. 报告信息 | 元数据 | 标题 "RA ODM分析报告" |
| 2. 趋势数据 | Month × ODM RA(DPPM) | 值 = ra × 1,000,000 |
| 3. Top Model汇总 | ODM × Top Model | IFIR→RA, box_claim→ra_claim, box_mm→ra_mm |
| 4. 月度Top Model | Month × ODM × Model | 同上 |
| 5. Detail明细数据 | 全量claim明细 | 来自 fact_ra_detail |
| 6. 多ODM对比 | 饼图数据 | RA指标 |

### Sheet 3 Top Model汇总

| ODM | Rank | Model | Top Issues | RA(DPPM) | RA_CLAIM | RA_MM |
|-----|------|-------|-----------|---------|----------|-------|
| Wistron | 1 | ThinkPad X1 | LCD*45 | 5,800 | 120 | 20,690 |

### Sheet 5 Detail明细

字段与 RA Model 页 Detail Sheet 相同（15列，无delivery_month），筛选逻辑：
- `claim_month` 在时间范围内
- ODM → Plant 映射（通过 `map_odm_to_plant`, kpi_type="RA"）
- segments → segment/segment2 兼容
- models 直接过滤

### Sheet 6 多ODM对比

| ODM | RA(DPPM) | Share(%) | RA_CLAIM | RA_MM |
|-----|---------|----------|----------|-------|
| Wistron | 5,678 | 52.3% | 120 | 21,132 |

## 三、后端新增接口

```
POST /ra/report/odm
```

**请求体**:
```python
class RaOdmReportRequest(BaseModel):
    time_range: TimeRange
    filters: RaOdmFilters         # odms(必选) + segments + models
    view: Optional[RaOdmViewConfig] = None
    tgt: Optional[int] = 1500
```

## 四、ODM→Plant 映射注意

RA 的 ODM→Plant 映射需要使用 `kpi_type="RA"`（而非"IFIR"）：

```python
plant_list = db.query(MapOdmToPlant.plant).filter(
    MapOdmToPlant.kpi_type == "RA",       # 注意这里
    MapOdmToPlant.supplier_new.in_(odms)
).distinct().all()
```

RA Service 中已有 `_resolve_detail_plants` 方法封装此逻辑。
