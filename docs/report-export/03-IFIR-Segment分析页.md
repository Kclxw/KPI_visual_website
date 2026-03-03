# IFIR Segment分析页 - 报告导出设计

## 一、页面现状

**路径**: `frontend/src/pages/ifir/SegmentAnalysisPage.vue`
**组件**: `frontend/src/components/kpi/ifir/segment/SegmentCard.vue`
**API**: `POST /ifir/segment-analysis/analyze`

### 筛选参数
| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| time_range | {start_month, end_month} | 是 | 时间范围 |
| segments | string[] | 是 | 选中的Segment列表 |
| odms | string[] | 否 | 可选ODM过滤 |
| models | string[] | 否 | 可选Model过滤 |
| top_odm_sort | "claim" \| "ifir" | 否 | Top ODM排序方式 |
| top_model_sort | "claim" \| "ifir" | 否 | Top Model排序方式 |
| tgt | number | 否 | TGT目标值(DPPM) |

### 页面内容结构（最复杂的页面）
- **Block D** (多Segment时): 多Segment趋势对比 + 数据矩阵 + 饼图
- **每个Segment卡片**:
  - Block A: IFIR趋势折线图
  - Block B: **Top ODM表格** (Rank / ODM / IFIR DPPM / BOX CLAIM / BOX MM)
  - Block C: **Top Model表格** (Rank / Model / Top Issue / IFIR DPPM / BOX CLAIM / BOX MM)
  - Block D: AI分析总结

### 与其他页面的关键差异
- 有 **两个** Top N表格（Top ODM + Top Model），是最复杂的页面
- 两个排序控件（topOdmSort + topModelSort）
- Top Model表格中嵌套了 Top Issue 链接

## 二、Excel报告结构

### Sheet 1: `报告信息`

| 单元格 | 内容 |
|--------|------|
| A1 | **IFIR Segment分析报告** |
| A3 | 数据截至: {data_as_of} |
| A4 | 分析时间范围: {start_month} ~ {end_month} |
| A5 | 分析Segment: {segment1, segment2, ...} |
| A6 | 筛选ODM: {全部 或 具体值} |
| A7 | 筛选Model: {全部 或 具体值} |
| A8 | TGT目标: {tgt} DPPM |
| A9 | Top ODM排序: {CLAIM 或 IFIR} |
| A10 | Top Model排序: {CLAIM 或 IFIR} |
| A11 | 报告生成时间: {now} |

### Sheet 2: `趋势数据`

**表头**: Month | {Segment1} IFIR(DPPM) | {Segment2} IFIR(DPPM) | ...

| Month | Consumer (DPPM) | Commercial (DPPM) |
|-------|----------------|-------------------|
| 2024-07 | 1,234 | 890 |
| ... | ... | ... |

**嵌入图表**: 多Segment趋势对比折线图 + TGT目标线（绿色系配色，与前端 `#67c23a` 一致）

### Sheet 3: `Top ODM汇总`

**每个Segment一个子表**:

| Segment | Rank | ODM | IFIR(DPPM) | BOX_CLAIM | BOX_MM |
|---------|------|-----|-----------|-----------|--------|
| Consumer | 1 | Wistron | 1,800 | 120 | 66,667 |
| Consumer | 2 | Compal | 1,500 | 90 | 60,000 |
| ... | ... | ... | ... | ... | ... |
| Commercial | 1 | Foxconn | 2,100 | 80 | 38,095 |
| ... | ... | ... | ... | ... | ... |

### Sheet 4: `月度Top ODM`

| Month | Segment | Rank | ODM | IFIR(DPPM) | BOX_CLAIM | BOX_MM |
|-------|---------|------|-----|-----------|-----------|--------|
| 2025-06 | Consumer | 1 | Wistron | 2,200 | 20 | 9,091 |
| ... | ... | ... | ... | ... | ... | ... |

### Sheet 5: `Top Model汇总`

**每个Segment一个子表**:

| Segment | Rank | Model | Top Issues | IFIR(DPPM) | BOX_CLAIM | BOX_MM |
|---------|------|-------|-----------|-----------|-----------|--------|
| Consumer | 1 | ThinkPad X1 | LCD*45, Battery*30 | 1,800 | 56 | 31,111 |
| Consumer | 2 | ThinkPad T14 | Keyboard*20 | 1,500 | 40 | 26,667 |
| ... | ... | ... | ... | ... | ... | ... |

### Sheet 6: `月度Top Model`

| Month | Segment | Rank | Model | Top Issues | IFIR(DPPM) | BOX_CLAIM | BOX_MM |
|-------|---------|------|-------|-----------|-----------|-----------|--------|
| 2025-06 | Consumer | 1 | ThinkPad X1 | LCD*12 | 2,100 | 15 | 7,143 |
| ... | ... | ... | ... | ... | ... | ... | ... |

### Sheet 7: `Detail明细数据`

**数据来源**: `fact_ifir_detail` 表
**筛选逻辑**:
- `delivery_month` 在 time_range 内
- `segment` 或 `segment2` 匹配所选Segment列表（兼容逻辑）
- 如有 odms 过滤，则通过 `map_odm_to_plant` 映射后按 `plant` 过滤
- 如有 models 过滤，则按 `model` 过滤

**列定义**: 与 IFIR Model 页 Detail Sheet 相同（16列）

### Sheet 8: `多Segment对比` (仅多Segment时)

| Segment | IFIR(DPPM) | Share(%) | BOX_CLAIM | BOX_MM |
|---------|-----------|----------|-----------|--------|
| Consumer | 1,234 | 58.3% | 200 | 162,075 |
| Commercial | 890 | 41.7% | 150 | 168,539 |

**嵌入图表**: Segment占比饼图

## 三、matplotlib 图表规格

### 3.1 趋势对比图
与前两个页面相同结构，主色调绿色系（与前端 `#67c23a` 一致）。

### 3.2 饼图 (多Segment时)
标签为 Segment 名称。

## 四、后端新增接口

```
POST /ifir/report/segment
```

**请求体**:
```python
class IfirSegmentReportRequest(BaseModel):
    time_range: TimeRange
    filters: IfirSegmentFilters     # segments(必选) + odms + models
    view: Optional[IfirSegmentViewConfig] = None  # top_odm_sort + top_model_sort
    tgt: Optional[int] = 1500
```

**后端处理流程**:
1. 复用 `IfirService.analyze_segment()` 获取全量分析数据
2. 新增 `IfirService.get_segment_details_for_report()` 获取Detail数据
3. 生成图表（趋势图 + 饼图）
4. 构建 Excel（8个Sheet）
5. 返回文件流

## 五、Detail数据查询的关键逻辑

Segment 页面的 Detail 查询需要注意 **segment/segment2 双字段兼容**：

```python
# 已有的 _apply_detail_segment_filter 方法
def _apply_detail_segment_filter(self, query, segments):
    if segments:
        query = query.filter(or_(
            FactIfirDetail.segment.in_(segments),
            FactIfirDetail.segment2.in_(segments)
        ))
    return query
```

ODM 过滤仍需通过 `map_odm_to_plant` 映射。

## 六、特殊注意事项

1. **Sheet数量最多**: 8个Sheet（其他页面6个），因为有 Top ODM 和 Top Model 两套排名
2. **数据量可能较大**: Segment 维度的 Detail 数据通常比 Model 维度多很多，需注意内存和响应时间
3. **建议**: 如果Detail行数超过 100,000 行，可在Sheet末尾添加提示："数据量过大，仅导出前100,000行，完整数据请联系管理员"
