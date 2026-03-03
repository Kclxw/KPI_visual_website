# IFIR ODM分析页 - 报告导出设计

## 一、页面现状

**路径**: `frontend/src/pages/ifir/OdmAnalysisPage.vue`
**组件**: `frontend/src/components/kpi/ifir/odm/OdmCard.vue`
**API**: `POST /ifir/odm-analysis/analyze`

### 筛选参数
| 参数 | 类型 | 必选 | 说明 |
|------|------|------|------|
| time_range | {start_month, end_month} | 是 | 时间范围 |
| odms | string[] | 是 | 选中的ODM列表 |
| segments | string[] | 否 | 可选Segment过滤 |
| models | string[] | 否 | 可选Model过滤 |
| top_model_sort | "claim" \| "ifir" | 否 | Top Model排序方式 |
| tgt | number | 否 | TGT目标值(DPPM) |

### 页面内容结构
- **Block D** (多ODM时): 多ODM趋势对比图 + 数据矩阵 + 饼图
- **每个ODM卡片**:
  - Block A: IFIR趋势折线图 (年度对比/完整趋势)
  - Block B: Top Model表格 (Rank / Model / Top Issue / IFIR DPPM / BOX CLAIM / BOX MM)
  - Block C: AI分析总结

### 与Model分析页的关键差异
- 主维度从 Model → ODM
- Top 排名从 Issue → Model（每个Model附带其Top Issue）
- Top Model有双排序模式（按CLAIM或按IFIR）

## 二、Excel报告结构

### Sheet 1: `报告信息`

| 单元格 | 内容 |
|--------|------|
| A1 | **IFIR ODM分析报告** |
| A3 | 数据截至: {data_as_of} |
| A4 | 分析时间范围: {start_month} ~ {end_month} |
| A5 | 分析ODM: {odm1, odm2, ...} |
| A6 | 筛选Segment: {全部 或 具体值} |
| A7 | 筛选Model: {全部 或 具体值} |
| A8 | TGT目标: {tgt} DPPM |
| A9 | Top Model排序: {CLAIM 或 IFIR} |
| A10 | 报告生成时间: {now} |

### Sheet 2: `趋势数据`

**表头**: Month | {ODM1} IFIR(DPPM) | {ODM2} IFIR(DPPM) | ...

| Month | Wistron (DPPM) | Compal (DPPM) |
|-------|---------------|---------------|
| 2024-07 | 1,234 | 2,345 |
| ... | ... | ... |

**嵌入图表**: 多ODM趋势对比折线图 + TGT目标线

### Sheet 3: `Top Model汇总`

**每个ODM一个子表**（ODM标题行 + 数据行 + 空行分隔）：

| ODM | Rank | Model | Top Issues | IFIR(DPPM) | BOX_CLAIM | BOX_MM |
|-----|------|-------|-----------|-----------|-----------|--------|
| Wistron | 1 | ThinkPad X1 | LCD*45, Battery*30 | 1,800 | 56 | 31,111 |
| Wistron | 2 | ThinkPad T14 | Keyboard*20 | 1,500 | 40 | 26,667 |
| ... | ... | ... | ... | ... | ... | ... |

**Top Issues列**: 将每个Model的 `top_issues` 合并为字符串，格式: `{issue}*{count}`，多个用 `, ` 分隔

### Sheet 4: `月度Top Model`

| Month | ODM | Rank | Model | Top Issues | IFIR(DPPM) | BOX_CLAIM | BOX_MM |
|-------|-----|------|-------|-----------|-----------|-----------|--------|
| 2025-06 | Wistron | 1 | ThinkPad X1 | LCD*12 | 2,100 | 15 | 7,143 |
| ... | ... | ... | ... | ... | ... | ... | ... |

展开所有ODM × 所有月份的 monthly_top_models 数据。

### Sheet 5: `Detail明细数据`

**数据来源**: `fact_ifir_detail` 表
**筛选逻辑**:
- `delivery_month` 在 time_range 内
- `plant` 通过 `map_odm_to_plant` 映射所选ODM得到（已有逻辑）
- 如有 segments 过滤，则 `segment` 或 `segment2` 匹配
- 如有 models 过滤，则 `model` 匹配

| 列名 | 数据库字段 | 说明 |
|------|-----------|------|
| Claim_Nbr | claim_nbr | 索赔单号 |
| Claim_Month | claim_month | 索赔月份 |
| Delivery_Month | delivery_month | 出货月份 |
| Model | model | 机型 |
| Segment | segment | 产品线段 |
| Plant | plant | 工厂（可反映ODM归属） |
| Fault_Category | fault_category | 故障大类 |
| Problem_Descr_by_Tech | problem_descr_by_tech | 技术员问题描述 |
| Failure_Code | failure_code | 故障代码 |
| MTM | mtm | 机器类型号 |
| Serial_Nbr | serial_nbr | 序列号 |
| Geo | geo_2012 | 地理区域 |
| Commodity | commodity | 零件大类 |
| Part_Nbr | part_nbr | 零件号 |
| Part_Desc | part_desc | 零件描述 |
| Part_Supplier | part_supplier | 零件供应商 |

### Sheet 6: `多ODM对比` (仅多ODM时)

| ODM | IFIR(DPPM) | Share(%) | BOX_CLAIM | BOX_MM |
|-----|-----------|----------|-----------|--------|
| Wistron | 1,234 | 45.2% | 56 | 45,000 |
| Compal | 890 | 32.6% | 40 | 45,000 |

**嵌入图表**: ODM占比饼图

## 三、matplotlib 图表规格

### 3.1 趋势对比图
与 IFIR Model 页相同规格，线条标签改为 ODM 名称，主色调改为蓝色系（与前端 `#409eff` 一致）。

### 3.2 饼图 (多ODM时)
与 IFIR Model 页相同规格，标签改为 ODM 名称。

## 四、后端新增接口

```
POST /ifir/report/odm
```

**请求体**:
```python
class IfirOdmReportRequest(BaseModel):
    time_range: TimeRange
    filters: IfirOdmFilters       # odms(必选) + segments + models
    view: Optional[IfirOdmViewConfig] = None   # top_model_sort
    tgt: Optional[int] = 1500
```

**后端处理流程**:
1. 复用 `IfirService.analyze_odm()` 获取趋势 + Top Model + 月度数据
2. 新增 `IfirService.get_odm_details_for_report()` 查询全量Detail
   - 通过 `map_odm_to_plant` 将ODM列表 → plant列表
   - 按 plant + time_range + segments + models 过滤 `fact_ifir_detail`
3. 生成图表 + Excel + 返回文件

## 五、Detail数据查询的关键逻辑

ODM分析页的Detail数据获取比Model页更复杂，因为：
- ODM 在 Detail 表中 **没有直接字段**，需要通过 `map_odm_to_plant` 中间表映射
- 已有的 `get_model_issue_details` 方法中已实现此映射逻辑，可以复用
- 报告导出时 **不做 issue 过滤**，导出满足条件的所有Detail行

```python
# 伪代码
plant_list = (
    db.query(MapOdmToPlant.plant)
    .filter(MapOdmToPlant.kpi_type == "IFIR", MapOdmToPlant.supplier_new.in_(odms))
    .distinct()
)

query = db.query(FactIfirDetail).filter(
    FactIfirDetail.delivery_month.between(start_date, end_date),
    FactIfirDetail.plant.in_(plant_list),
)
if segments:
    query = query.filter(or_(
        FactIfirDetail.segment.in_(segments),
        FactIfirDetail.segment2.in_(segments)
    ))
if models:
    query = query.filter(FactIfirDetail.model.in_(models))
```
