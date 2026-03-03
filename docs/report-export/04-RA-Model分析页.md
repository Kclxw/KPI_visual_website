# RA Model分析页 - 报告导出设计

## 一、页面现状

**路径**: `frontend/src/pages/ra/ModelAnalysisPage.vue`
**组件**: `frontend/src/components/kpi/ra/model/RaModelCard.vue`
**API**: `POST /ra/model-analysis/analyze`

### 与 IFIR Model 页的差异

| 差异项 | IFIR Model | RA Model |
|--------|-----------|----------|
| KPI指标 | ifir = box_claim / box_mm | ra = ra_claim / ra_mm |
| 时间主轴 | delivery_month（出货月） | claim_month（索赔月） |
| Detail表 | fact_ifir_detail | fact_ra_detail |
| Issue Detail接口 | 无month过滤 | 支持 `month` 精确过滤 |
| 趋势图颜色 | 橙色 #e6a23c | 对应RA配色 |

### 筛选参数
与 IFIR Model 页完全相同结构，仅KPI类型不同。

### 页面内容结构
与 IFIR Model 页完全相同：Block D(多Model对比) + 每个Model卡片(趋势图 + Top Issue + AI总结)

## 二、Excel报告结构

### Sheet结构与 IFIR Model 页完全对应，共6个Sheet：

| Sheet | 内容 | 差异点 |
|-------|------|--------|
| 1. 报告信息 | 报告元数据 | 标题改为 "RA Model分析报告" |
| 2. 趋势数据 | Month × Model RA(DPPM) | 值 = ra × 1,000,000 |
| 3. Top Issue汇总 | Model × Top Issue | 数据来源改为 fact_ra_detail |
| 4. 月度Top Issue | Month × Model × Issue | 同上 |
| 5. Detail明细数据 | 全量claim明细 | 来自 fact_ra_detail，字段有差异 |
| 6. 多Model对比 | 饼图数据 | 指标改为 ra/ra_claim/ra_mm |

### Sheet 5 Detail字段差异

RA Detail 表与 IFIR Detail 表的主要字段差异：

| 列名 | 数据库字段 | 说明 |
|------|-----------|------|
| Claim_Nbr | claim_nbr | 索赔单号 |
| Claim_Month | claim_month | 索赔月份（RA时间轴） |
| Model | model | 机型 |
| Segment | segment | 产品线段 |
| Plant | plant | 工厂 |
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

**注意**: RA Detail 表 **没有** `delivery_month` 字段，时间轴为 `claim_month`。

### Sheet 2 趋势数据表头

| Month | {Model1} RA(DPPM) | {Model2} RA(DPPM) |
|-------|-------------------|-------------------|
| 2024-07 | 5,678 | 3,456 |

### Sheet 6 多Model对比

| Model | RA(DPPM) | Share(%) | RA_CLAIM | RA_MM |
|-------|---------|----------|----------|-------|
| ThinkPad X1 | 5,678 | 52.3% | 120 | 21,132 |

## 三、后端新增接口

```
POST /ra/report/model
```

**请求体**:
```python
class RaModelReportRequest(BaseModel):
    time_range: TimeRange
    filters: RaModelFilters      # models(必选) + segments + odms
    tgt: Optional[int] = 1500
```

**处理流程**:
1. 复用 `RaService.analyze_model()` 获取分析数据
2. 新增 `RaService.get_model_details_for_report()` 获取全量Detail
   - 按 `claim_month`（非 delivery_month）过滤
   - segments → segment/segment2 兼容
   - odms → plant 映射
3. 生成图表 + Excel → 返回文件

## 四、Detail查询特殊逻辑

RA 的时间过滤基于 `claim_month` 而非 `delivery_month`：

```python
query = db.query(FactRaDetail).filter(
    FactRaDetail.claim_month >= start_date,
    FactRaDetail.claim_month <= end_date,
    FactRaDetail.model.in_(models),
)
# segment / plant 过滤逻辑与 IFIR 相同
```
