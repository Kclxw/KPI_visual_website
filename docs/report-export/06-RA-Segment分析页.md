# RA Segment分析页 - 报告导出设计

## 一、页面现状

**路径**: `frontend/src/pages/ra/SegmentAnalysisPage.vue`
**组件**: `frontend/src/components/kpi/ra/segment/RaSegmentCard.vue`
**API**: `POST /ra/segment-analysis/analyze`

### 与 IFIR Segment 页的差异

| 差异项 | IFIR Segment | RA Segment |
|--------|-------------|------------|
| KPI指标 | ifir / box_claim / box_mm | ra / ra_claim / ra_mm |
| 时间主轴 | delivery_month | claim_month |
| Detail表 | fact_ifir_detail | fact_ra_detail |
| 排序选项 | "claim" \| "ifir" | "claim" \| "ra" |
| ODM→Plant映射 | kpi_type="IFIR" | kpi_type="RA" |

### 筛选参数
| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| time_range | {start_month, end_month} | 是 | 时间范围 |
| segments | string[] | 是 | 选中的Segment列表 |
| odms | string[] | 否 | 可选ODM过滤 |
| models | string[] | 否 | 可选Model过滤 |
| top_odm_sort | "claim" \| "ra" | 否 | Top ODM排序方式 |
| top_model_sort | "claim" \| "ra" | 否 | Top Model排序方式 |
| tgt | number | 否 | TGT目标值(DPPM) |

### 页面内容结构（与IFIR Segment结构一致，最复杂）
- **Block D** (多Segment时): 多Segment趋势对比 + 数据矩阵 + 饼图
- **每个Segment卡片**:
  - Block A: RA趋势折线图
  - Block B: Top ODM表格 (Rank / ODM / RA DPPM / RA_CLAIM / RA_MM)
  - Block C: Top Model表格 (Rank / Model / Top Issue / RA DPPM / RA_CLAIM / RA_MM)
  - Block D: AI分析总结

## 二、Excel报告结构

### 共8个Sheet（与IFIR Segment对应）：

| Sheet | 内容 | 与IFIR Segment的差异 |
|-------|------|---------------------|
| 1. 报告信息 | 元数据 | 标题 "RA Segment分析报告" |
| 2. 趋势数据 | Month × Segment RA(DPPM) | 值 = ra × 1,000,000 |
| 3. Top ODM汇总 | Segment × Top ODM | IFIR→RA指标 |
| 4. 月度Top ODM | Month × Segment × ODM | 同上 |
| 5. Top Model汇总 | Segment × Top Model(含Issue) | RA指标 |
| 6. 月度Top Model | Month × Segment × Model | 同上 |
| 7. Detail明细数据 | 全量claim明细 | 来自 fact_ra_detail |
| 8. 多Segment对比 | 饼图数据 | RA指标 |

### Sheet 3: Top ODM汇总

| Segment | Rank | ODM | RA(DPPM) | RA_CLAIM | RA_MM |
|---------|------|-----|---------|----------|-------|
| Consumer | 1 | Wistron | 5,800 | 200 | 34,483 |
| Consumer | 2 | Compal | 4,200 | 150 | 35,714 |
| Commercial | 1 | Foxconn | 6,100 | 180 | 29,508 |

### Sheet 5: Top Model汇总

| Segment | Rank | Model | Top Issues | RA(DPPM) | RA_CLAIM | RA_MM |
|---------|------|-------|-----------|---------|----------|-------|
| Consumer | 1 | ThinkPad X1 | LCD*45, Battery*30 | 5,800 | 56 | 9,655 |

### Sheet 7: Detail明细数据

字段与 RA Model 页 Detail Sheet 相同（15列），筛选逻辑：
- `claim_month` 在时间范围内
- `segment` 或 `segment2` 匹配所选Segment（兼容逻辑）
- 如有 odms → plant 映射过滤（kpi_type="RA"）
- 如有 models 直接过滤

### Sheet 8: 多Segment对比

| Segment | RA(DPPM) | Share(%) | RA_CLAIM | RA_MM |
|---------|---------|----------|----------|-------|
| Consumer | 5,678 | 58.3% | 350 | 61,629 |
| Commercial | 4,100 | 41.7% | 250 | 60,976 |

**嵌入图表**: Segment占比饼图

## 三、后端新增接口

```
POST /ra/report/segment
```

**请求体**:
```python
class RaSegmentReportRequest(BaseModel):
    time_range: TimeRange
    filters: RaSegmentFilters       # segments(必选) + odms + models
    view: Optional[RaSegmentViewConfig] = None  # top_odm_sort + top_model_sort
    tgt: Optional[int] = 1500
```

**处理流程**:
1. 复用 `RaService.analyze_segment()` 获取分析数据
2. 新增 `RaService.get_segment_details_for_report()` 获取全量Detail
3. 生成图表（趋势图 + 饼图）
4. 构建 Excel（8个Sheet）
5. 返回文件流

## 四、数据量预警

RA Segment 页面是所有6个页面中潜在数据量最大的：
- Segment 维度覆盖范围广，Detail 记录可能非常多
- 建议设置导出上限（如 200,000 行），超出时截断并在Sheet末尾提示
- 后端生成Excel时需注意内存使用（openpyxl 的 write_only 模式）
