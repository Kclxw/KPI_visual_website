# KPI可视化系统 API 契约文档

> **版本**: v1.0  
> **基础路径**: `/api`  
> **更新日期**: 2026-01-26

---

## 一、通用规范

### 1.1 请求格式

- **Content-Type**: `application/json`（POST请求）
- **字符编码**: UTF-8
- **时间格式**: `YYYY-MM`（月份）、`YYYY-MM-DD`（日期）

### 1.2 响应格式

所有API响应均遵循以下结构：

```json
{
  "code": 0,
  "message": "success",
  "data": { ... }
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| code | number | 状态码，0表示成功，非0表示错误 |
| message | string | 状态描述 |
| data | object/array/null | 响应数据 |

### 1.3 分页格式（如需要）

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
  }
}
```

---

## 二、公共接口

### 2.1 健康检查

**GET** `/api/health`

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "timestamp": "2026-01-26T10:30:00Z"
  }
}
```

---

## 三、数据上传接口

### 3.1 上传Excel文件

**POST** `/api/upload/excel`

**Content-Type**: `multipart/form-data`

**请求参数**:

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| ifir_detail | file | 否 | IFIR Detail Excel文件 |
| ifir_row | file | 否 | IFIR Row Excel文件 |
| ra_detail | file | 否 | RA Detail Excel文件 |
| ra_row | file | 否 | RA Row Excel文件 |

> 注：至少上传一个文件

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "upload_20260126_103000_abc123",
    "status": "processing",
    "files": [
      { "name": "ifir_detail", "status": "queued", "rows": null },
      { "name": "ifir_row", "status": "queued", "rows": null }
    ]
  }
}
```

### 3.2 查询上传任务状态

**GET** `/api/upload/status/{task_id}`

**路径参数**:

| 参数 | 类型 | 说明 |
|------|------|------|
| task_id | string | 上传任务ID |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "task_id": "upload_20260126_103000_abc123",
    "status": "completed",
    "progress": 100,
    "files": [
      { "name": "ifir_detail", "status": "success", "rows": 15234 },
      { "name": "ifir_row", "status": "success", "rows": 892 }
    ],
    "created_at": "2026-01-26T10:30:00Z",
    "completed_at": "2026-01-26T10:32:15Z"
  }
}
```

**status 枚举值**:
- `queued` - 排队中
- `processing` - 处理中
- `completed` - 已完成
- `failed` - 失败

---

## 四、IFIR 分析接口

### 4.1 获取筛选选项

**GET** `/api/ifir/options`

**查询参数**（可选，用于级联筛选）:

| 参数 | 类型 | 说明 |
|------|------|------|
| segments | string | 逗号分隔的Segment列表 |
| odms | string | 逗号分隔的ODM列表 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "month_min": "2024-01",
    "month_max": "2025-12",
    "data_as_of": "2025-12",
    "segments": ["CONSUMER", "COMMERCIAL", "WORKSTATION"],
    "odms": ["FOXCONN", "HUNTKEY", "WISTRON", "COMPAL", "PEGATRON"],
    "models": ["T24A-20", "Y27QF-30", "G27C-10", "P27H-30", "L24E-40"]
  }
}
```

### 4.2 ODM分析

**POST** `/api/ifir/odm-analysis/analyze`

**请求体**:
```json
{
  "time_range": {
    "start_month": "2025-07",
    "end_month": "2025-12"
  },
  "filters": {
    "odms": ["FOXCONN", "HUNTKEY"],
    "segments": null,
    "models": null
  },
  "view": {
    "trend_months": 6,
    "top_model_n": 3
  }
}
```

**请求参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| time_range.start_month | string | 是 | 开始月份 YYYY-MM |
| time_range.end_month | string | 是 | 结束月份 YYYY-MM |
| filters.odms | string[] | 是 | ODM列表（必选） |
| filters.segments | string[]|null | 否 | Segment列表，null表示全部 |
| filters.models | string[]|null | 否 | Model列表，null表示全部 |
| view.trend_months | number | 否 | 趋势月数，默认6 |
| view.top_model_n | number | 否 | Top Model数量，默认3 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "meta": {
      "data_as_of": "2025-12",
      "time_range": { "start_month": "2025-07", "end_month": "2025-12" }
    },
    "summary": {
      "odm_pie": [
        { "odm": "FOXCONN", "ifir": 0.00011, "share": 0.55, "box_claim": 30, "box_mm": 280000 },
        { "odm": "HUNTKEY", "ifir": 0.00009, "share": 0.45, "box_claim": 25, "box_mm": 275000 }
      ]
    },
    "cards": [
      {
        "odm": "FOXCONN",
        "trend": [
          { "month": "2025-07", "ifir": 0.00012 },
          { "month": "2025-08", "ifir": 0.00010 },
          { "month": "2025-09", "ifir": 0.00015 },
          { "month": "2025-10", "ifir": 0.00011 },
          { "month": "2025-11", "ifir": 0.00009 },
          { "month": "2025-12", "ifir": 0.00008 }
        ],
        "top_models": [
          {
            "rank": 1,
            "model": "T24A-20",
            "ifir": 0.00030,
            "box_claim": 12,
            "box_mm": 40000
          },
          {
            "rank": 2,
            "model": "Y27QF-30",
            "ifir": 0.00025,
            "box_claim": 10,
            "box_mm": 40000
          },
          {
            "rank": 3,
            "model": "G27C-10",
            "ifir": 0.00020,
            "box_claim": 8,
            "box_mm": 40000
          }
        ],
        "ai_summary": "该ODM在过去6个月IFIR呈下降趋势，从0.012%降至0.008%，整体表现改善。Top Model为T24A-20，贡献了约32%的IFIR，建议重点关注该机型的质量改进措施。"
      },
      {
        "odm": "HUNTKEY",
        "trend": [...],
        "top_models": [...],
        "ai_summary": "..."
      }
    ]
  }
}
```

**响应字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| summary | object | 多ODM汇总数据（Block D，多选ODM时返回） |
| summary.odm_pie | array | ODM饼图数据 |
| summary.odm_pie[].odm | string | ODM名称 |
| summary.odm_pie[].ifir | number | 该ODM的聚合IFIR |
| summary.odm_pie[].share | number | 占比（0-1） |
| summary.odm_pie[].box_claim | number | BOX CLAIM总数 |
| summary.odm_pie[].box_mm | number | BOX MM总数 |
| cards | array | ODM分析卡片数组 |
| cards[].odm | string | ODM名称 |
| cards[].trend | array | IFIR趋势数据 |
| cards[].trend[].month | string | 月份 YYYY-MM |
| cards[].trend[].ifir | number | IFIR值（小数形式，如0.00012表示0.012%） |
| cards[].top_models | array | Top Model列表 |
| cards[].top_models[].rank | number | 排名 |
| cards[].top_models[].model | string | Model名称 |
| cards[].top_models[].ifir | number | 该Model的IFIR |
| cards[].top_models[].box_claim | number | BOX CLAIM数量 |
| cards[].top_models[].box_mm | number | BOX MM数量 |
| cards[].ai_summary | string | AI分析总结 |

### 4.3 Segment分析

**POST** `/api/ifir/segment-analysis/analyze`

**请求体**:
```json
{
  "time_range": {
    "start_month": "2025-07",
    "end_month": "2025-12"
  },
  "filters": {
    "segments": ["CONSUMER", "COMMERCIAL"],
    "odms": null,
    "models": null
  },
  "view": {
    "trend_months": 6,
    "top_contributor_n": 3,
    "top_issue_n": 3
  }
}
```

**请求参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filters.segments | string[] | 是 | Segment列表（必选） |
| filters.odms | string[]|null | 否 | ODM列表，null表示全部 |
| filters.models | string[]|null | 否 | Model列表，null表示全部 |
| view.trend_months | number | 否 | 趋势月数，默认6 |
| view.top_contributor_n | number | 否 | Top贡献者数量，默认3 |
| view.top_issue_n | number | 否 | Top Issue数量，默认3 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "meta": {
      "data_as_of": "2025-12",
      "time_range": { "start_month": "2025-07", "end_month": "2025-12" }
    },
    "cards": [
      {
        "segment": "CONSUMER",
        "trend": [
          { "month": "2025-07", "ifir": 0.00012 },
          { "month": "2025-08", "ifir": 0.00010 }
        ],
        "top_contributors": [
          {
            "rank": 1,
            "model": "T24A-20",
            "contribution": 0.32,
            "box_claim": 45,
            "box_mm": 150000
          }
        ],
        "top_issues": [
          {
            "rank": 1,
            "issue": "显示屏闪烁",
            "count": 23,
            "share": 0.28
          },
          {
            "rank": 2,
            "issue": "电源故障",
            "count": 18,
            "share": 0.22
          }
        ],
        "ai_summary": "CONSUMER segment整体IFIR稳定..."
      }
    ]
  }
}
```

### 4.4 Model分析

**POST** `/api/ifir/model-analysis/analyze`

**请求体**:
```json
{
  "time_range": {
    "start_month": "2025-07",
    "end_month": "2025-12"
  },
  "filters": {
    "models": ["T24A-20", "Y27QF-30"],
    "segments": null,
    "odms": null
  },
  "view": {
    "trend_months": 6,
    "top_issue_n": 5
  }
}
```

**请求参数说明**:

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| filters.models | string[] | 是 | Model列表（必选） |
| filters.segments | string[]|null | 否 | Segment列表，null表示全部 |
| filters.odms | string[]|null | 否 | ODM列表，null表示全部 |
| view.trend_months | number | 否 | 趋势月数，默认6 |
| view.top_issue_n | number | 否 | Top Issue数量，默认5 |

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "meta": {
      "data_as_of": "2025-12",
      "time_range": { "start_month": "2025-07", "end_month": "2025-12" }
    },
    "cards": [
      {
        "model": "T24A-20",
        "trend": [
          { "month": "2025-07", "ifir": 0.00030 },
          { "month": "2025-08", "ifir": 0.00028 }
        ],
        "top_issues": [
          {
            "rank": 1,
            "issue": "显示屏闪烁",
            "count": 12,
            "share": 0.35,
            "first_seen": "2025-07",
            "last_seen": "2025-12"
          },
          {
            "rank": 2,
            "issue": "亮度异常",
            "count": 8,
            "share": 0.24,
            "first_seen": "2025-08",
            "last_seen": "2025-11"
          }
        ],
        "ai_summary": "T24A-20在过去6个月IFIR呈下降趋势，主要问题集中在显示屏相关故障..."
      }
    ]
  }
}
```

---

## 五、RA 分析接口

> RA接口与IFIR接口结构类似，主要区别：
> - 时间口径：RA使用 `claim_month`（索赔月），IFIR使用 `delivery_month`（出货月）
> - 指标字段：RA使用 `ra_claim/ra_mm`，IFIR使用 `box_claim/box_mm`

### 5.1 获取筛选选项

**GET** `/api/ra/options`

响应结构同 IFIR Options API。

### 5.2 ODM分析

**POST** `/api/ra/odm-analysis/analyze`

**请求体**:
```json
{
  "time_range": {
    "start_month": "2025-07",
    "end_month": "2025-12"
  },
  "filters": {
    "odms": ["FOXCONN"],
    "segments": null,
    "models": null
  },
  "view": {
    "trend_months": 6,
    "top_model_n": 3
  }
}
```

**响应示例**:
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "meta": {
      "data_as_of": "2025-12",
      "time_range": { "start_month": "2025-07", "end_month": "2025-12" }
    },
    "cards": [
      {
        "odm": "FOXCONN",
        "trend": [
          { "month": "2025-07", "ra": 0.0025 },
          { "month": "2025-08", "ra": 0.0023 }
        ],
        "top_models": [
          {
            "rank": 1,
            "model": "T24A-20",
            "ra": 0.0045,
            "ra_claim": 120,
            "ra_mm": 26667
          }
        ],
        "ai_summary": "..."
      }
    ]
  }
}
```

### 5.3 Segment分析

**POST** `/api/ra/segment-analysis/analyze`

请求和响应结构同 IFIR Segment分析，字段从 `ifir` 改为 `ra`。

### 5.4 Model分析

**POST** `/api/ra/model-analysis/analyze`

请求和响应结构同 IFIR Model分析，字段从 `ifir` 改为 `ra`。

---

## 六、数据类型定义

### 6.1 时间范围 TimeRange

```typescript
interface TimeRange {
  start_month: string;  // YYYY-MM
  end_month: string;    // YYYY-MM
}
```

### 6.2 趋势数据点 TrendPoint

```typescript
// IFIR
interface IfirTrendPoint {
  month: string;  // YYYY-MM
  ifir: number;   // 小数形式
}

// RA
interface RaTrendPoint {
  month: string;  // YYYY-MM
  ra: number;     // 小数形式
}
```

### 6.3 Top Model/Contributor

```typescript
interface TopModelRow {
  rank: number;
  model: string;
  ifir?: number;      // IFIR分析
  ra?: number;        // RA分析
  box_claim?: number; // IFIR
  box_mm?: number;    // IFIR
  ra_claim?: number;  // RA
  ra_mm?: number;     // RA
  contribution?: number; // 贡献度（0-1）
}
```

### 6.4 Top Issue

```typescript
interface TopIssueRow {
  rank: number;
  issue: string;
  count: number;
  share: number;       // 占比（0-1）
  first_seen?: string; // YYYY-MM
  last_seen?: string;  // YYYY-MM
}
```

### 6.5 分析卡片

```typescript
// ODM卡片
interface OdmCard {
  odm: string;
  trend: TrendPoint[];
  top_models: TopModelRow[];
  ai_summary: string;
}

// Segment卡片
interface SegmentCard {
  segment: string;
  trend: TrendPoint[];
  top_contributors: TopModelRow[];
  top_issues: TopIssueRow[];
  ai_summary: string;
}

// Model卡片
interface ModelCard {
  model: string;
  trend: TrendPoint[];
  top_issues: TopIssueRow[];
  ai_summary: string;
}
```

---

## 七、注意事项

### 7.1 IFIR vs RA 的关键差异

| 项目 | IFIR | RA |
|------|------|-----|
| 时间口径 | 出货月 (delivery_month) | 索赔月 (claim_month) |
| 分子 | BOX CLAIM | RA CLAIM |
| 分母 | BOX MM (出货量) | RA MM (保修期内机器数) |
| 计算公式 | (BOX CLAIM / BOX MM) × 1,000,000 | sum(RA CLAIM) / sum(RA MM) |

### 7.2 前端展示约定

- **IFIR/RA值显示**：后端返回小数（如0.00012），前端显示为百分比（0.012%）或PPM
- **趋势窗口**：默认6个月，可选6/12/18/24
- **空数据处理**：卡片仍返回，trend/top_models为空数组，ai_summary给出提示

### 7.3 AI总结生成

- 后端生成AI总结，前端直接显示
- 若AI服务不可用，返回固定提示文案
- AI总结不包含具体行动建议，仅提供分析判断
