# 后端功能清单与映射表

> 版本: v1.0  
> 日期: 2026-01-26  
> 来源: plan/主要功能/*.md, plan/AI/*.md

---

## 一、功能模块总览

| 模块 | KPI类型 | 分析对象 | 数据来源 | Block结构 |
|------|---------|----------|----------|-----------|
| IFIR-ODM | IFIR | ODM(多选) | ROW | A趋势+B Top Model+C AI+D饼图 |
| IFIR-Segment | IFIR | Segment(多选) | ROW | A趋势+B Top ODM/Model+C AI+D饼图 |
| IFIR-Model | IFIR | Model(多选) | ROW+DETAIL | A趋势+B Top Issue+C AI+D饼图 |
| RA-ODM | RA | ODM(多选) | ROW | A趋势+B Top Model+C AI+D饼图 |
| RA-Segment | RA | Segment(多选) | ROW | A趋势+B Top ODM/Model+C AI+D饼图 |
| RA-Model | RA | Model(多选) | ROW+DETAIL | A趋势+B Top Issue+C AI+D饼图 |

---

## 二、API端点清单

### 2.1 IFIR模块

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/ifir/odm-analysis/options` | GET | 获取ODM分析筛选项 |
| `/api/ifir/odm-analysis/analyze` | POST | 执行ODM分析 |
| `/api/ifir/segment-analysis/options` | GET | 获取Segment分析筛选项 |
| `/api/ifir/segment-analysis/analyze` | POST | 执行Segment分析 |
| `/api/ifir/model-analysis/options` | GET | 获取Model分析筛选项(级联) |
| `/api/ifir/model-analysis/analyze` | POST | 执行Model分析 |

### 2.2 RA模块

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/ra/odm-analysis/options` | GET | 获取ODM分析筛选项 |
| `/api/ra/odm-analysis/analyze` | POST | 执行ODM分析 |
| `/api/ra/segment-analysis/options` | GET | 获取Segment分析筛选项 |
| `/api/ra/segment-analysis/analyze` | POST | 执行Segment分析 |
| `/api/ra/model-analysis/options` | GET | 获取Model分析筛选项(级联) |
| `/api/ra/model-analysis/analyze` | POST | 执行Model分析 |

### 2.3 上传模块

| 端点 | 方法 | 用途 |
|------|------|------|
| `/api/upload` | POST | 上传Excel文件 |
| `/api/upload/{task_id}/status` | GET | 查询上传任务状态 |

---

## 三、数据库表与功能映射

### 3.1 IFIR功能 -> 数据库表映射

| 功能 | 主数据表 | 辅助表 | 关键字段 |
|------|----------|--------|----------|
| IFIR趋势(Block A) | fact_ifir_row | - | delivery_month, supplier_new, box_claim, box_mm |
| IFIR Top Model | fact_ifir_row | - | model, box_claim, box_mm |
| IFIR Top ODM | fact_ifir_row | - | supplier_new, box_claim, box_mm |
| IFIR Top Issue | fact_ifir_detail | - | fault_category, problem_descr |
| IFIR饼图汇总 | fact_ifir_row | - | 按segment/odm聚合 |
| ODM下钻 | map_odm_to_plant | fact_ifir_detail | kpi_type='IFIR' |

**IFIR计算公式**: `IFIR = SUM(box_claim) / SUM(box_mm)`

**IFIR时间主轴**: `delivery_month`

### 3.2 RA功能 -> 数据库表映射

| 功能 | 主数据表 | 辅助表 | 关键字段 |
|------|----------|--------|----------|
| RA趋势(Block A) | fact_ra_row | - | claim_month, supplier_new, ra_claim, ra_mm |
| RA Top Model | fact_ra_row | - | model, ra_claim, ra_mm |
| RA Top ODM | fact_ra_row | - | supplier_new, ra_claim, ra_mm |
| RA Top Issue | fact_ra_detail | - | fault_category, problem_descr |
| RA饼图汇总 | fact_ra_row | - | 按segment/odm/model聚合 |
| ODM下钻 | map_odm_to_plant | fact_ra_detail | kpi_type='RA' |

**RA计算公式**: `RA = SUM(ra_claim) / SUM(ra_mm)`

**RA时间主轴**: `claim_month`

---

## 四、详细功能说明

### 4.1 Options API 通用返回结构

```json
{
  "month_min": "2023-01",
  "month_max": "2025-12",
  "data_as_of": "2025-12",
  "segments": ["SEG_A", "SEG_B"],
  "odms": ["ODM_X", "ODM_Y"],
  "models": ["MODEL_1", "MODEL_2"]
}
```

**SQL查询示例(IFIR)**:
```sql
-- 月份范围
SELECT MIN(delivery_month) AS month_min, MAX(delivery_month) AS month_max
FROM fact_ifir_row;

-- Segment列表
SELECT DISTINCT segment FROM fact_ifir_row WHERE segment IS NOT NULL ORDER BY segment;

-- ODM列表
SELECT DISTINCT supplier_new FROM fact_ifir_row WHERE supplier_new IS NOT NULL ORDER BY supplier_new;

-- Model列表
SELECT DISTINCT model FROM fact_ifir_row WHERE model IS NOT NULL ORDER BY model;
```

---

### 4.2 IFIR-ODM分析

**输入参数**:
```json
{
  "time_range": { "start_month": "2025-07", "end_month": "2025-12" },
  "filters": {
    "segments": ["SEG_A"],
    "models": ["MODEL_1"],
    "odms": ["ODM_A", "ODM_B"]
  },
  "view": { "trend_months": 6, "top_model_n": 1 }
}
```

**后端计算逻辑**:

1. **Block A - ODM趋势**:
```sql
SELECT
  supplier_new AS odm,
  delivery_month,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row
WHERE delivery_month BETWEEN :start AND :end
  AND supplier_new IN (:odm_list)
  AND (:segments_all OR segment IN (:segments))
  AND (:models_all OR model IN (:models))
GROUP BY supplier_new, delivery_month
ORDER BY supplier_new, delivery_month;
```

2. **Block B - Top Model**:
```sql
SELECT
  supplier_new AS odm,
  model,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row
WHERE delivery_month BETWEEN :start AND :end
  AND supplier_new IN (:odm_list)
  AND (:segments_all OR segment IN (:segments))
  AND (:models_all OR model IN (:models))
GROUP BY supplier_new, model;
-- 服务层: 计算ifir = box_claim_sum/box_mm_sum, 按odm分组取TopN
```

3. **Block D - 多ODM汇总饼图** (多选ODM时):
```sql
SELECT
  supplier_new AS odm,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row
WHERE delivery_month BETWEEN :start AND :end
  AND supplier_new IN (:odm_list)
  AND (:segments_all OR segment IN (:segments))
  AND (:models_all OR model IN (:models))
GROUP BY supplier_new;
-- 服务层: 计算每个ODM的ifir和share
```

4. **服务层计算**:
```python
# ifir计算
ifir = box_claim_sum / box_mm_sum if box_mm_sum > 0 else 0

# 截取trend_months个点
trend = sorted(trend_data, key=lambda x: x['month'])[-trend_months:]

# share计算(Block D)
total_claim = sum(row['box_claim_sum'] for row in odm_data)
for row in odm_data:
    row['share'] = row['box_claim_sum'] / total_claim if total_claim > 0 else 0
```

**Response结构** (增加summary):
```json
{
  "meta": { "data_as_of": "2025-12" },
  "summary": {
    "odm_pie": [
      { "odm": "ODM_A", "ifir": 0.12, "share": 0.55, "box_claim": 20, "box_mm": 165 },
      { "odm": "ODM_B", "ifir": 0.10, "share": 0.45, "box_claim": 16, "box_mm": 160 }
    ]
  },
  "cards": [...]
}
```

---

### 4.3 IFIR-Segment分析

**额外功能**: Block D 多Segment饼图

**Block D计算**:
```sql
SELECT
  segment,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row
WHERE delivery_month BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_all OR supplier_new IN (:odms))
  AND (:models_all OR model IN (:models))
GROUP BY segment;
```

**share计算**(后端固化):
```python
# 方案1: 按分子占比
total_claim = sum(row['box_claim_sum'] for row in data)
for row in data:
    row['share'] = row['box_claim_sum'] / total_claim if total_claim > 0 else 0
```

---

### 4.4 IFIR-Model分析 (需要DETAIL表)

**特点**: Block B来自DETAIL表的Top Issue

**Block B - Top Issue**:
```sql
SELECT
  model,
  fault_category AS issue,
  COUNT(*) AS issue_count
FROM fact_ifir_detail
WHERE delivery_month BETWEEN :start AND :end
  AND model IN (:model_list)
  AND (:segments_all OR segment IN (:segments))
  AND plant IN (
    SELECT plant FROM map_odm_to_plant 
    WHERE kpi_type = 'IFIR' AND supplier_new IN (:odms)
  )
GROUP BY model, fault_category
ORDER BY model, issue_count DESC;
-- 服务层: 按model分组取TopN
```

**注意**: ODM过滤需要通过map_odm_to_plant映射到plant再过滤DETAIL表

---

### 4.5 RA-ODM分析

与IFIR-ODM逻辑相同，差异:
- 数据表: `fact_ra_row`
- 时间字段: `claim_month`
- KPI字段: `ra_claim`, `ra_mm`
- 计算公式: `ra = ra_claim / ra_mm`

---

### 4.6 RA-Segment分析

与IFIR-Segment逻辑相同，差异同上

---

### 4.7 RA-Model分析

与IFIR-Model逻辑相同，差异:
- ROW表: `fact_ra_row`
- DETAIL表: `fact_ra_detail`
- 时间字段: `claim_month`
- KPI字段: `ra_claim`, `ra_mm`

---

## 五、AI分析功能

### 5.1 AI输入数据结构

```json
{
  "meta": {
    "kpi": "RA|IFIR",
    "layer": "SEGMENT|ODM|MODEL",
    "time_range": { "start_month": "2025-07", "end_month": "2025-12" },
    "data_as_of": "2025-12"
  },
  "entity": {
    "type": "MODEL",
    "id": "MODEL_1"
  },
  "series": {
    "monthly_trend": [
      { "month": "2025-07", "kpi": 0.018, "numerator": 18, "denominator": 1000 }
    ],
    "overall": { "kpi": 0.020, "numerator": 120, "denominator": 6000 }
  },
  "top_tables": {
    "top_models": [],
    "top_odms": []
  },
  "issues": {
    "source": "RA_DETAIL",
    "items": [
      { "rank": 1, "issue": "Power", "count": 42, "share": 0.28 }
    ]
  }
}
```

### 5.2 AI输出数据结构

```json
{
  "summary_text": "...",
  "summary_struct": {
    "overview": "...",
    "trend_insights": [],
    "top_drivers": [],
    "patterns_clues": [],
    "evidence": []
  }
}
```

---

## 六、关键约束

### 6.1 前端不计算KPI

- 所有 `ifir`, `ra`, `share` 值由后端计算返回
- 前端只负责渲染

### 6.2 ODM下钻链路

```
ROW表(计算KPI) -> 选择ODM -> map_odm_to_plant(获取plant列表) -> DETAIL表(按plant过滤)
```

### 6.3 时间主轴差异

| KPI | 时间主轴 | ROW表字段 | DETAIL表字段 |
|-----|----------|-----------|--------------|
| IFIR | 出货月 | delivery_month | delivery_month |
| RA | 索赔月 | claim_month | claim_month |

---

## 七、数据库字段验证清单

### 7.1 fact_ifir_row 必需字段

- [x] delivery_month (时间主轴)
- [x] supplier_new (ODM)
- [x] segment
- [x] model
- [x] box_claim (分子)
- [x] box_mm (分母)

### 7.2 fact_ifir_detail 必需字段

- [x] claim_nbr (主键)
- [x] delivery_month (下钻时间)
- [x] plant (ODM下钻关键)
- [x] segment
- [x] model
- [x] fault_category (Top Issue)

### 7.3 fact_ra_row 必需字段

- [x] claim_month (时间主轴)
- [x] supplier_new (ODM)
- [x] segment
- [x] model
- [x] ra_claim (分子)
- [x] ra_mm (分母)

### 7.4 fact_ra_detail 必需字段

- [x] claim_nbr (主键)
- [x] claim_month (下钻时间)
- [x] plant (ODM下钻关键)
- [x] segment
- [x] model
- [x] fault_category (Top Issue)

### 7.5 map_odm_to_plant 必需字段

- [x] kpi_type (区分IFIR/RA)
- [x] supplier_new (ODM)
- [x] plant (工厂)

---

## 八、前端API对应关系

| 前端页面 | 路由 | Options API | Analyze API |
|----------|------|-------------|-------------|
| IFIR-ODM | /kpi/ifir/odm-analysis | GET /api/ifir/odm-analysis/options | POST /api/ifir/odm-analysis/analyze |
| IFIR-Segment | /kpi/ifir/segment-analysis | GET /api/ifir/segment-analysis/options | POST /api/ifir/segment-analysis/analyze |
| IFIR-Model | /kpi/ifir/model-analysis | GET /api/ifir/model-analysis/options | POST /api/ifir/model-analysis/analyze |
| RA-ODM | /kpi/ra/odm-analysis | GET /api/ra/odm-analysis/options | POST /api/ra/odm-analysis/analyze |
| RA-Segment | /kpi/ra/segment-analysis | GET /api/ra/segment-analysis/options | POST /api/ra/segment-analysis/analyze |
| RA-Model | /kpi/ra/model-analysis | GET /api/ra/model-analysis/options | POST /api/ra/model-analysis/analyze |

---

## 九、实现优先级

根据IMPLEMENTATION_PLAN.md:

1. **Phase 4.1**: IFIR Options + Analyze (ODM/Segment/Model)
2. **Phase 4.2**: 文件上传 + ETL
3. **Phase 5**: 前后端联调
4. **Phase 6**: RA模块 (复用IFIR逻辑)
5. **Phase 7**: AI模块
