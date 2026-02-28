# KPI 可视化系统 — 功能汇总文档

> 系统名称：联想售后数据分析系统（KPI Visual）  
> 文档生成日期：2026-02-25  
> 技术栈：Vue 3 + TypeScript + Element Plus（前端）/ FastAPI + SQLAlchemy + MySQL（后端）

---

## 目录

1. [系统概览](#1-系统概览)
2. [后端功能详解](#2-后端功能详解)
   - 2.1 [应用入口与基础设施](#21-应用入口与基础设施)
   - 2.2 [数据库表结构](#22-数据库表结构)
   - 2.3 [文件上传与 ETL 模块](#23-文件上传与-etl-模块)
   - 2.4 [IFIR 分析模块](#24-ifir-分析模块)
   - 2.5 [RA 分析模块](#25-ra-分析模块)
3. [前端功能详解](#3-前端功能详解)
   - 3.1 [整体布局与导航](#31-整体布局与导航)
   - 3.2 [数据上传页面](#32-数据上传页面)
   - 3.3 [IFIR 分析页面群](#33-ifir-分析页面群)
   - 3.4 [RA 分析页面群](#34-ra-分析页面群)
   - 3.5 [通用组件](#35-通用组件)
4. [API 接口汇总](#4-api-接口汇总)
5. [数据流说明](#5-数据流说明)

---

## 1. 系统概览

本系统是联想售后数据可视化分析平台，核心功能是对两类 KPI 指标（**IFIR** 和 **RA**）进行多维度可视化分析。

| KPI 指标 | 全称 | 计算公式 | 时间主轴 | 单位 |
|----------|------|----------|----------|------|
| **IFIR** | In Field Incident Rate（现场故障率） | BOX CLAIM / BOX MM | 出货月（delivery_month） | DPPM（百万分之一） |
| **RA** | Return Authorization（退货授权率） | RA CLAIM / RA MM | 索赔月（claim_month） | DPPM |

**分析维度（两个 KPI 共用）：**
- **ODM 维度**：按代工厂（Supplier/ODM）分析
- **Segment 维度**：按产品线细分（Consumer/Commercial/Gaming 等）
- **Model 维度**：按具体产品型号分析

---

## 2. 后端功能详解

### 2.1 应用入口与基础设施

**文件：** `backend/app/main.py`

| 功能 | 路由 | 说明 |
|------|------|------|
| 根路由 | `GET /` | 返回应用名称、版本、运行状态 |
| 健康检查 | `GET /health` | 返回 `{"status": "healthy"}` |

**基础配置（`backend/app/core/config.py`）：**
- 应用名称：`KPI Visual API`，版本 `1.0.0`
- 数据库：MySQL，默认连接 `localhost:3306/kpi_visual`，字符集 `utf8mb4`
- CORS：允许 `localhost:5173/3000/3001/3002` 等本地开发端口
- 支持通过 `.env` 文件覆盖所有配置项（DB_HOST、DB_PORT、DB_USER、DB_PASSWORD、DB_NAME）

**路由注册：**
- `/api/ifir/*` → IFIR 分析路由
- `/api/ra/*` → RA 分析路由
- `/api/upload/*` → 文件上传路由

---

### 2.2 数据库表结构

#### 表 1：`fact_ifir_row`（IFIR ROW 月度聚合事实表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger(PK) | 自增主键 |
| content_hash | String(32), UNIQUE | 行内容 MD5 哈希，用于去重 |
| delivery_month | Date | 出货月（IFIR 时间主轴） |
| brand | String(32) | 品牌 |
| geo | String(16) | 地理区域 |
| product_line | String(32) | 产品线 |
| segment | String(64) | 产品细分 |
| series | String(128) | 产品系列 |
| model | String(128) | 产品型号 |
| plant | String(64) | 工厂 |
| mach_type | String(64) | 机器类型 |
| supplier_new | String(128) | ODM 供应商 |
| box_claim | Integer | IFIR 分子（索赔箱数） |
| box_mm | Integer | IFIR 分母（出货百万台） |
| year_ignore | SmallInteger | 年份（溯源用） |
| month_ignore | SmallInteger | 月份（溯源用） |
| src_file | String(255) | 来源文件路径 |
| etl_batch_id | String(64) | ETL 批次 ID |
| load_ts | DateTime | 加载时间戳 |

#### 表 2：`fact_ifir_detail`（IFIR DETAIL 事件级明细表）

| 字段 | 类型 | 说明 |
|------|------|------|
| claim_nbr | String(64)(PK) | 索赔单号（主键） |
| claim_month | Date | 索赔归属月 |
| claim_date | Date | 索赔日期 |
| delivery_month | Date | IFIR 下钻主时间轴 |
| delivery_day | SmallInteger | 出货日 |
| geo_2012 | String(32) | 区域代码 |
| financial_region | String(64) | 财务区域 |
| plant | String(64) | 工厂 |
| brand | String(64) | 品牌 |
| segment | String(64) | 产品细分 |
| segment2 | String(64) | 产品细分2 |
| style | String(64) | 款式 |
| series | String(128) | 系列 |
| model | String(128) | 型号 |
| mtm | String(64) | MTM 编码 |
| serial_nbr | String(64) | 序列号 |
| stationname | String(255) | 服务站名称 |
| station_id | Integer | 服务站 ID |
| data_source | String(32) | 数据来源 |
| lastsln | Text | 最后解决方案 |
| failure_code | String(32) | 故障代码 |
| fault_category | String(128) | **故障大类（Top Issue 来源）** |
| mach_desc | String(255) | 机器描述 |
| problem_descr | String(255) | 问题描述 |
| problem_descr_by_tech | String(255) | 技术人员描述 |
| commodity | String(64) | 商品类别 |
| down_part_code | String(64) | 故障零件代码 |
| part_nbr | String(64) | 零件编号 |
| part_desc | String(255) | 零件描述 |
| part_supplier | String(128) | 零件供应商 |
| part_barcode | String(64) | 零件条形码 |
| packing_lot_no | String(64) | 包装批次号 |
| claim_item_nbr | String(64) | 索赔项目编号 |
| claim_status | String(32) | 索赔状态 |
| channel | String(32) | 销售渠道 |
| cust_nbr | String(64) | 客户编号 |
| load_ts | DateTime | 加载时间戳 |

#### 表 3：`fact_ra_row`（RA ROW 月度聚合事实表）

结构与 `fact_ifir_row` 类似，差异点：
- 时间主轴：`claim_month`（索赔归属月）
- KPI 字段：`ra_claim`（RA 分子）、`ra_mm`（RA 分母）

#### 表 4：`fact_ra_detail`（RA DETAIL 事件级明细表）

结构与 `fact_ifir_detail` 类似，差异点：
- 时间主轴：`claim_month`
- 无 `delivery_month`/`delivery_day` 字段

#### 表 5：`map_odm_to_plant`（ODM 到工厂映射表）

| 字段 | 类型 | 说明 |
|------|------|------|
| kpi_type | String(16)(PK) | IFIR 或 RA |
| supplier_new | String(128)(PK) | ODM 名称 |
| plant | String(64)(PK) | 工厂代码 |
| load_ts | DateTime | 加载时间戳 |

> 用于将 DETAIL 表（以 plant 过滤）与 ROW 表（以 supplier_new 过滤）关联，在 Model 分析中联表查询 Top Issue 时使用。

#### 表 6：`upload_task`（上传任务表）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BigInteger(PK) | 自增主键 |
| task_id | String(100), UNIQUE | 任务 UUID |
| status | Enum | queued / processing / completed / failed |
| progress | Integer | 进度百分比 0-100 |
| ifir_detail_file | String(500) | IFIR Detail 文件路径 |
| ifir_detail_status | String(20) | 该文件处理状态 |
| ifir_detail_rows | Integer | 处理行数 |
| ifir_row_file | String(500) | IFIR Row 文件路径 |
| ifir_row_status | String(20) | 该文件处理状态 |
| ifir_row_rows | Integer | 处理行数 |
| ra_detail_file | String(500) | RA Detail 文件路径 |
| ra_detail_status | String(20) | 该文件处理状态 |
| ra_detail_rows | Integer | 处理行数 |
| ra_row_file | String(500) | RA Row 文件路径 |
| ra_row_status | String(20) | 该文件处理状态 |
| ra_row_rows | Integer | 处理行数 |
| error_message | Text | 错误信息 |
| created_at | DateTime | 创建时间 |
| started_at | DateTime | 开始处理时间 |
| completed_at | DateTime | 完成时间 |

---

### 2.3 文件上传与 ETL 模块

**文件：** `backend/app/api/upload.py` + `backend/app/services/etl_service.py`

#### 2.3.1 上传 API

| 接口 | 方法 | 路由 | 说明 |
|------|------|------|------|
| 上传文件 | POST | `/api/upload` | 支持同时上传最多 4 个 Excel 文件 |
| 查询任务状态 | GET | `/api/upload/{task_id}/status` | 轮询任务处理进度 |

**上传接口详情：**
- 接收文件字段：`ifir_detail`（IFIR Detail Excel）、`ifir_row`（IFIR Row Excel）、`ra_detail`（RA Detail Excel）、`ra_row`（RA Row Excel）
- 至少需要上传 1 个文件，否则返回 400 错误
- 文件保存路径：`backend/uploads/{task_id}_{file_type}_{filename}`
- 创建 `UploadTask` 数据库记录，状态初始化为 `queued`
- 使用 `daemon=True` 后台线程异步处理 ETL，避免阻塞 HTTP 响应
- 立即返回 `task_id` 供前端轮询

**查询状态接口详情：**
- 根据 `task_id` 查询 `upload_task` 表
- 返回每个文件的处理状态（pending/processing/completed/failed）及处理行数
- 任务不存在时返回 404

#### 2.3.2 ETL 服务（`EtlService`）

ETL 服务负责将 Excel 文件解析、清洗并写入数据库。

**处理顺序：**  
IFIR ROW → IFIR DETAIL → RA ROW → RA DETAIL → ODM 映射表刷新

**IFIR ROW 文件处理（`_process_ifir_row`）：**
- 字段映射：`Delivery_month` → `delivery_month`，`Supplier_NEW` → `supplier_new`，`BOX CLAIM` → `box_claim`，`BOX MM` → `box_mm` 等 14 个字段
- 数据清洗：
  - 过滤 `delivery_month` 无法解析为日期的行（汇总行、筛选条件行等）
  - `supplier_new` 填充空值为 "None" 并 strip
  - `box_claim`/`box_mm` 转换为整数，空值填 0
- 去重机制：计算每行 14 个维度字段的 **MD5 哈希**（`content_hash`），使用 MySQL `INSERT ... ON DUPLICATE KEY UPDATE` 实现幂等写入（相同内容的行不会重复插入，字段值会被更新）
- 批量写入：每批 500 行

**IFIR DETAIL 文件处理（`_process_ifir_detail`）：**
- 字段映射：约 35 个字段（从 `Claim_Nbr` 到 `Cust_Nbr`）
- 主键：`claim_nbr`（索赔单号）
- 去重：若同一 `claim_nbr` 有多条记录，按 `claim_date` 降序保留最新一条
- 使用 `INSERT ... ON DUPLICATE KEY UPDATE` 写入（以 `claim_nbr` 为唯一键）
- 批量写入：每批 500 行

**RA ROW 文件处理（`_process_ra_row`）：**
- 与 IFIR ROW 处理逻辑相同，字段差异：`Claim_month`（而非 `Delivery_month`），`RA CLAIM`/`RA MM`（而非 `BOX CLAIM`/`BOX MM`），`PLANT_OLD` → `plant`

**RA DETAIL 文件处理（`_process_ra_detail`）：**
- 与 IFIR DETAIL 处理逻辑相同，去重：按 `claim_month` 降序保留最新记录

**ODM 映射表刷新（`_refresh_odm_mapping`）：**
- 在所有文件处理完成后自动执行
- 从 `fact_ifir_row` 中提取所有不重复的 `(supplier_new, plant)` 组合，写入 `map_odm_to_plant`（kpi_type='IFIR'）
- 从 `fact_ra_row` 中提取所有不重复的 `(supplier_new, plant)` 组合，写入 `map_odm_to_plant`（kpi_type='RA'）
- 使用 SQLAlchemy `merge()` 实现幂等更新

---

### 2.4 IFIR 分析模块

**文件：** `backend/app/api/ifir.py` + `backend/app/services/ifir_service.py`

#### 2.4.1 筛选项 API

| 接口 | 方法 | 路由 | 说明 |
|------|------|------|------|
| 统一筛选项 | GET | `/api/ifir/options` | 主接口，支持任意组合联动过滤 |
| ODM 页筛选项（兼容） | GET | `/api/ifir/odm-analysis/options` | 转发至上面的统一接口 |
| Segment 页筛选项（兼容） | GET | `/api/ifir/segment-analysis/options` | 转发至上面的统一接口 |
| Model 页筛选项（兼容） | GET | `/api/ifir/model-analysis/options` | 转发至上面的统一接口 |

**筛选项接口参数：**
- `segments`（可选）：逗号分隔的 Segment 列表
- `odms`（可选）：逗号分隔的 ODM 列表
- `models`（可选）：逗号分隔的 Model 列表

**筛选项接口返回内容（`IfirOptionsData`）：**
- `month_min`：数据库中最早的出货月
- `month_max`：数据库中最新的出货月
- `data_as_of`：数据截至时间（同 month_max）
- `time_range`：`{min_month, max_month}`
- `segments`：当前过滤条件下可选的 Segment 列表（已排序）
- `odms`：当前过滤条件下可选的 ODM 列表（已排序）
- `models`：当前过滤条件下可选的 Model 列表（已排序）

**联动过滤逻辑：**
- 选择 Segment → ODM 和 Model 列表会缩小为该 Segment 下有数据的范围
- 选择 ODM → Segment 和 Model 列表会缩小为该 ODM 下有数据的范围
- 三个维度任意组合均支持

#### 2.4.2 ODM 分析 API

**接口：** `POST /api/ifir/odm-analysis/analyze`

**请求参数：**
```json
{
  "time_range": { "start_month": "YYYY-MM", "end_month": "YYYY-MM" },
  "filters": {
    "odms": ["ODM1", "ODM2"],  // 必选
    "segments": ["Segment1"],   // 可选
    "models": ["ModelA"]        // 可选
  },
  "view": {
    "trend_months": 6,          // 默认6
    "top_model_n": 10           // 默认10
  }
}
```

**后端处理逻辑（`IfirService.analyze_odm`）：**

1. **Block D（多 ODM 汇总）**：当选择 ≥2 个 ODM 时，计算各 ODM 的 box_claim 合计、box_mm 合计、IFIR 值及占比，生成 `odm_pie` 饼图数据

2. **为每个 ODM 生成分析卡片（`IfirOdmCard`）：**
   - **Block A — IFIR 趋势**：按月份聚合该 ODM 的 box_claim、box_mm，计算每月 IFIR，返回完整时间范围内的趋势折线数据
   - **Block B — Top Model（汇总）**：在整个时间范围内，按 Model 聚合 IFIR，从高到低排序，取 Top N（默认 10），每个 Model 附带 Top Issue 信息（从 `fact_ifir_detail` 查询）
   - **Block B — Top Model（月度明细）**：对每个月分别计算 Top N Model，按月份组织为 `MonthlyTopModels` 列表
   - **Block C — AI 总结**：字段预留，当前为空字符串（后续版本支持）

3. **ODM 到 Plant 映射**：从 `map_odm_to_plant` 表获取 ODM 对应的工厂列表，用于在 DETAIL 表中过滤 Top Issue 数据

4. **Top Issue 查询（`_get_top_issue_by_model`）**：
   - 查询 `fact_ifir_detail` 表，按 `fault_category` 统计各 Model 的故障次数
   - 支持按 Segment 和 Plant 进一步过滤
   - 返回每个 Model 排名最高的 N 个故障类别（含 count 和占比）

**返回数据结构：**
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "meta": { "data_as_of": "YYYY-MM", "time_range": {...} },
    "summary": { "odm_pie": [{ "odm": "...", "ifir": 0.001, "share": 0.3, "box_claim": 100, "box_mm": 100000 }] },
    "cards": [{
      "odm": "ODM名称",
      "trend": [{ "month": "YYYY-MM", "ifir": 0.001 }],
      "top_models": [{ "rank": 1, "model": "...", "ifir": 0.002, "box_claim": 50, "box_mm": 25000, "top_issues": [...] }],
      "monthly_top_models": [{ "month": "YYYY-MM", "items": [...] }],
      "ai_summary": ""
    }]
  }
}
```

#### 2.4.3 Segment 分析 API

**接口：** `POST /api/ifir/segment-analysis/analyze`

**请求参数：**
- `filters.segments`：Segment 列表（**必选**）
- `filters.odms`：ODM 列表（可选）
- `filters.models`：Model 列表（可选）
- `view.trend_months`：趋势月数（默认 6）
- `view.top_n`：Top N 数量（默认 10）
- `view.top_odm_sort`：ODM 排序方式（`claim` 或 `ifir`，默认 `claim`）
- `view.top_model_sort`：Model 排序方式（`claim` 或 `ifir`，默认 `claim`）

**后端处理逻辑（`IfirService.analyze_segment`）：**

1. **Block D（多 Segment 汇总）**：当选择 ≥2 个 Segment 时生成 `segment_pie` 饼图数据

2. **为每个 Segment 生成分析卡片（`IfirSegmentCard`）：**
   - **Block A — IFIR 趋势**：该 Segment 的月度 IFIR 趋势
   - **Block B — Top ODM（汇总）**：在整个时间范围内按 ODM 聚合，按 IFIR 排序，取 Top N
   - **Block B — Top Model（汇总）**：在整个时间范围内按 Model 聚合，按 IFIR 排序，取 Top N，附带 Top Issue
   - **Block B — 月度明细（Top ODM）**：每月的 Top ODM 列表
   - **Block B — 月度明细（Top Model）**：每月的 Top Model 列表
   - **Block C — AI 总结**：字段预留

**返回数据结构：**每张卡片含 `segment`、`trend`、`top_odms`、`top_models`、`monthly_top_odms`、`monthly_top_models`、`ai_summary`

#### 2.4.4 Model 分析 API

**接口：** `POST /api/ifir/model-analysis/analyze`

**请求参数：**
- `filters.models`：Model 列表（**必选**）
- `filters.segments`：Segment 列表（可选）
- `filters.odms`：ODM 列表（可选）
- `view.trend_months`：趋势月数（默认 6）
- `view.top_issue_n`：Top Issue 数量（默认 5）

**后端处理逻辑（`IfirService.analyze_model`）：**

1. **Block D（多 Model 汇总）**：当选择 ≥2 个 Model 时生成 `model_pie` 饼图数据

2. **为每个 Model 生成分析卡片（`IfirModelCard`）：**
   - **Block A — IFIR 趋势**：从 `fact_ifir_row` 表按月聚合，返回完整时间范围趋势
   - **Block B — Top Issue（汇总）**：从 `fact_ifir_detail` 表按 `fault_category` 统计，取出现次数最多的 Top N，含 count 及占比；若 ODM 过滤条件存在，通过 `map_odm_to_plant` 转换为 plant 列表进行过滤
   - **Block B — Top Issue（月度明细）**：每月的 Top Issue 列表
   - **Block C — AI 总结**：字段预留

#### 2.4.5 Model Issue 明细 API

**接口：** `POST /api/ifir/model-analysis/issue-details`

**请求参数：**
- `filters.model`：Model（**必选**）
- `filters.issue`：故障类别 fault_category（**必选**）
- `filters.segments`：Segment 列表（可选）
- `filters.odms`：ODM 列表（可选）
- `pagination.page`：页码（默认 1）
- `pagination.page_size`：每页条数（默认 10）

**处理逻辑（`IfirService.get_model_issue_details`）：**
- 查询 `fact_ifir_detail` 表，按 model + fault_category 筛选
- 返回字段：`model`、`fault_category`、`problem_descr_by_tech`、`claim_nbr`、`claim_month`、`plant`
- 支持分页，返回 `total`、`page`、`page_size`、`items` 列表

---

### 2.5 RA 分析模块

**文件：** `backend/app/api/ra.py` + `backend/app/services/ra_service.py`

RA 分析模块与 IFIR 分析模块结构完全对称，差异如下：

| 差异点 | IFIR | RA |
|--------|------|----|
| KPI 值字段 | `ifir`（= box_claim / box_mm） | `ra`（= ra_claim / ra_mm） |
| ROW 表时间轴 | `delivery_month` | `claim_month` |
| DETAIL 表时间轴 | `delivery_month` | `claim_month` |
| 分子/分母字段 | `box_claim` / `box_mm` | `ra_claim` / `ra_mm` |
| RA Model 分析支持 | 无 `segment` 单值筛选 | 额外支持 `filters.segment`（单值） |

**RA 模块接口列表：**

| 接口 | 方法 | 路由 |
|------|------|------|
| 统一筛选项 | GET | `/api/ra/options` |
| ODM 页筛选项（兼容） | GET | `/api/ra/odm-analysis/options` |
| Segment 页筛选项（兼容） | GET | `/api/ra/segment-analysis/options` |
| Model 页筛选项（兼容） | GET | `/api/ra/model-analysis/options` |
| ODM 分析 | POST | `/api/ra/odm-analysis/analyze` |
| Segment 分析 | POST | `/api/ra/segment-analysis/analyze` |
| Model 分析 | POST | `/api/ra/model-analysis/analyze` |

> **注意：** RA 模块没有 Model Issue 明细接口（IFIR 独有）。

---

## 3. 前端功能详解

### 3.1 整体布局与导航

**文件：** `frontend/src/components/layout/MainLayout.vue` + `AppSidebar.vue` + `AppHeader.vue`

**布局结构：**
- 左侧边栏（`AppSidebar`）：可折叠导航菜单，折叠宽度 64px，展开宽度 220px
- 顶部 Header（`AppHeader`）：含侧边栏折叠按钮和页面标题
- 主内容区（`router-view`）：展示当前激活路由的页面

**路由配置（`frontend/src/router/index.ts`）：**

```
/ (Layout)
├── /upload                         → 数据上传页
├── /kpi/ifir
│   ├── /kpi/ifir/odm-analysis      → IFIR ODM 分析页
│   ├── /kpi/ifir/segment-analysis  → IFIR Segment 分析页
│   └── /kpi/ifir/model-analysis    → IFIR Model 分析页
└── /kpi/ra
    ├── /kpi/ra/odm-analysis        → RA ODM 分析页
    ├── /kpi/ra/segment-analysis    → RA Segment 分析页
    └── /kpi/ra/model-analysis      → RA Model 分析页
```

默认重定向到 `/upload`（数据上传页）。所有路由使用 `createWebHistory` 模式（HTML5 History API）。

---

### 3.2 数据上传页面

**文件：** `frontend/src/pages/upload/UploadPage.vue`

**功能详情：**

| 功能 | 说明 |
|------|------|
| 4 个文件上传区 | IFIR Detail、IFIR Row、RA Detail、RA Row，各自独立的拖拽上传区域 |
| 拖拽上传 | 支持将文件拖入上传区，也支持点击弹出文件选择框 |
| 文件类型限制 | 仅接受 `.xlsx` 和 `.xls` 格式 |
| 单文件限制 | 每个类型只能选择 1 个文件（limit=1） |
| 文件移除 | 已选文件可以重新选择（remove 后重新 change） |
| 至少选一个 | 4 个文件至少选择 1 个才能开始上传 |
| 开始上传按钮 | 点击后调用 `uploadFiles` API，触发上传流程 |
| 实时进度条 | 通过 `el-progress` 展示整体处理进度（0-100%），状态为 failed 时显示红色异常状态 |
| 各文件状态标签 | 每个文件下方显示 pending/处理中/完成/失败 的标签及处理行数 |
| 轮询机制 | 上传后每隔 1 秒调用 `getUploadStatus` 轮询任务状态，直到 completed 或 failed |
| 完成提示 | 任务完成后显示绿色 Alert 提示"数据已成功导入数据库，可以进行分析了" |
| 错误提示 | 任务失败后显示红色 Alert 展示错误信息 |

---

### 3.3 IFIR 分析页面群

#### 3.3.1 IFIR ODM 分析页面

**文件：** `frontend/src/pages/ifir/OdmAnalysisPage.vue`

**筛选区功能：**

| 控件 | 类型 | 说明 |
|------|------|------|
| 时间范围 | `el-date-picker monthrange` | 月份范围选择器，禁用数据库范围之外的日期 |
| ODM 多选 | `el-select multiple` | **必选**，支持 collapse-tags 显示（多选后折叠） |
| Segment 多选 | `el-select multiple` | 可选，全不选代表全部 |
| Model 多选 | `el-select multiple` | 可选，全不选代表全部 |
| TGT 目标值 | `el-input-number` | 单位 DPPM，默认 1500，范围 0-100000，步长 100 |
| 分析按钮 | `el-button primary` | 必须选择 ODM 才可点击，分析中显示 loading 状态 |

**级联过滤逻辑：**
- 监听 `selectedSegments`、`selectedOdms`、`selectedModels` 的变化
- 任一变化时调用 `getIfirOptions` 刷新其他维度的可选项
- 自动清除当前选中的无效值（不在新选项列表中的值会被过滤掉）
- 使用 `isRefreshing` 标志位防止循环触发

**首次加载：**
- 调用 `getIfirOptions()` 获取全量选项
- 自动计算默认时间范围：最新月份往前推 6 个月（或到数据最早月份为止）

**结果展示区：**

1. **Block D — 多 ODM 汇总对比**（仅选择 ≥2 个 ODM 时显示）
   - 使用通用 `SummaryBlockD` 组件
   - 展示多 ODM 趋势对比折线图 + 数据矩阵表

2. **ODM 选择条（标签栏）**：每个选中的 ODM 显示为一个可点击标签，点击切换当前展示的卡片

3. **卡片轮播区**：
   - 所有 ODM 卡片横向排列
   - 通过 CSS `translateX` 动画切换，`transition: 0.3s ease`
   - 每次只显示一张卡片（`OdmCard` 组件）

**空态处理：**
- 未分析时显示空态提示"请选择 ODM 并点击分析按钮"
- 若没有数据，额外提示"请先在数据上传页面上传数据"

#### 3.3.2 IFIR ODM 分析卡片组件

**文件：** `frontend/src/components/kpi/ifir/odm/OdmCard.vue`

**Block A — IFIR 趋势图：**

| 功能 | 说明 |
|------|------|
| 切换模式 | 支持"年度对比"和"完整趋势"两种模式（radio-group 切换） |
| 年度对比图 | 按年份分组，将同一月份的不同年份数据并排展示，X 轴为 1-12 月，每年一条折线，不同颜色区分 |
| 完整趋势图 | 时间轴展示所有历史数据，单条带面积渐变的折线，超过 12 个月自动添加 `dataZoom` 滑动条 |
| 鼠标悬停 | Tooltip 显示月份和 IFIR 值（DPPM 格式） |
| 点击数据点 | 弹出小对话框显示该月的 DPPM 值和百分比 |
| 数据格式 | IFIR 原始值（小数）× 1,000,000 = DPPM |
| 图表自适应 | 监听 window.resize 事件自动调整尺寸 |
| 最新月份标签 | 卡片头部显示当前数据截至的最新月份 |

**Block B — Top Model 表格：**

| 功能 | 说明 |
|------|------|
| 视图切换 | "汇总"和"月度"两个 tab |
| 汇总视图 | 展示整个时间范围内 IFIR 最高的 Top N 个 Model |
| 月度视图 | 通过月份下拉选择器切换月份，展示该月的 Top N Model；默认显示最新月份 |
| 排名标签 | 前 3 名红色，4-6 名橙色，7 名以后灰色 |
| Top Issue 链接 | 每个 Model 的 Top Issue 显示为可点击链接（格式：`Issue名称 * 出现次数`） |
| 点击 Issue | 弹出 Issue 明细对话框（见下方） |
| 显示字段 | 排名、Model、Top Issue、IFIR(DPPM)、BOX CLAIM、BOX MM |
| 最大高度 | 400px，超出时显示滚动条 |

**Issue 明细弹窗：**

| 功能 | 说明 |
|------|------|
| 弹窗标题 | `Issue 明细：{issue名称}` |
| 弹窗宽度 | 900px |
| 展示字段 | Model、不良现象（fault_category）、Problem_Descr_by_Tech、Claim_Nbr、Claim_Month、Plant |
| Loading 状态 | 数据加载中显示 el-table 的 loading 遮罩 |
| 分页 | 每页 10/20/50 条可选，展示总条数、页码导航 |
| 翻页自动请求 | 切换页码或每页条数时重新调用 API |
| 过滤透传 | 带入当前页面的时间范围、当前 ODM、当前 Segment 过滤条件 |

**Block C — AI 分析总结：**
- 暂时显示"暂无 AI 分析（后续版本支持）"
- 字段已预留（`ai_summary`），后续版本将接入 AI 服务

#### 3.3.3 IFIR Segment 分析页面

**文件：** `frontend/src/pages/ifir/SegmentAnalysisPage.vue`

与 ODM 分析页面结构相同，差异点：
- **必选维度**改为 Segment
- 结果卡片组件：`SegmentCard`（每张卡片同时展示 Top ODM 和 Top Model 两张表格）

#### 3.3.4 IFIR Segment 分析卡片组件

**文件：** `frontend/src/components/kpi/ifir/segment/SegmentCard.vue`

包含：
- **Block A** — Segment IFIR 趋势图（与 OdmCard 相同逻辑）
- **Block B-1** — Top ODM 表格（汇总 + 月度切换）：展示 IFIR 最高的 Top N ODM，字段：排名、ODM、IFIR(DPPM)、BOX CLAIM、BOX MM
- **Block B-2** — Top Model 表格（汇总 + 月度切换）：与 OdmCard 中相同，含 Top Issue 链接
- **Block C** — AI 总结（预留）

#### 3.3.5 IFIR Model 分析页面

**文件：** `frontend/src/pages/ifir/ModelAnalysisPage.vue`

与 ODM 分析页面结构相同，差异点：
- **必选维度**改为 Model
- 结果卡片组件：`ModelCard`（展示 Top Issue 而非 Top Model）

#### 3.3.6 IFIR Model 分析卡片组件

**文件：** `frontend/src/components/kpi/ifir/model/ModelCard.vue`

包含：
- **Block A** — Model IFIR 趋势图（与 OdmCard 相同逻辑）
- **Block B** — Top Issue 表格（汇总 + 月度切换）：展示故障次数最多的 Top N 故障类别（fault_category），含 count 和占比；每个 Issue 可点击弹出明细
- **Block C** — AI 总结（预留）

---

### 3.4 RA 分析页面群

RA 分析的三个页面（`/frontend/src/pages/ra/`）和三个卡片组件（`/frontend/src/components/kpi/ra/`）与 IFIR 对应组件结构完全对称，主要差异：

| 差异点 | IFIR | RA |
|--------|------|----|
| KPI 指标名称 | IFIR | RA |
| 趋势点字段 | `ifir` | `ra` |
| 数量指标字段 | `box_claim`/`box_mm` | `ra_claim`/`ra_mm` |
| 时间主轴说明 | 出货月 | 索赔月 |
| Issue 明细弹窗 | 有（OdmCard 中有） | 无（RA 无 Issue 明细接口） |

**RA 模块页面文件列表：**
- `pages/ra/OdmAnalysisPage.vue` → `components/kpi/ra/odm/RaOdmCard.vue`
- `pages/ra/SegmentAnalysisPage.vue` → `components/kpi/ra/segment/RaSegmentCard.vue`
- `pages/ra/ModelAnalysisPage.vue` → `components/kpi/ra/model/RaModelCard.vue`

---

### 3.5 通用组件

#### 3.5.1 Block D 汇总对比组件（`SummaryBlockD`）

**文件：** `frontend/src/components/kpi/common/SummaryBlockD.vue`

当选择 ≥2 个分析对象（ODM/Segment/Model）时，在卡片轮播上方显示此汇总区块。

**组件 Props：**
| Prop | 类型 | 说明 |
|------|------|------|
| entityLabel | string | 实体类型标签，如 "ODM"、"Segment"、"Model" |
| entityKey | string | 数据矩阵中的行标识键，如 "odm"、"segment"、"model" |
| entities | EntityTrend[] | 各实体的月度趋势数据数组 |
| pieData | PieItem[] | 饼图占比数据（可选） |
| tgt | number | 目标值（DPPM），默认 1500 |
| valueLabel | string | 指标名称，"IFIR" 或 "RA" |

**视图模式切换：**

**汇总趋势视图（summary）：**
- **多线趋势图**：每个实体一条折线，不同颜色区分；额外叠加 Average（平均）虚线和 TGT 目标线（红色实线）
- **数据矩阵表**：行 = 各实体 + Average 行，列 = 每个月份；单元格超过 TGT 目标显示红色背景（`over-tgt`），达标显示绿色背景（`meet-tgt`）

**单月饼图视图（monthly）：**
- 月份选择器选择某一月份
- 环形饼图展示各实体在该月的 IFIR/RA 值占比
- Tooltip 显示实体名称、DPPM 值和百分比

**响应式支持：**
- 监听 window.resize 自动调整图表尺寸
- 监听 props.entities 变化自动重绘图表
- 监听 props.tgt 变化自动更新 TGT 目标线

---

## 4. API 接口汇总

### 系统接口

| 方法 | 路由 | 功能 |
|------|------|------|
| GET | `/` | 系统状态 |
| GET | `/health` | 健康检查 |

### 文件上传接口

| 方法 | 路由 | 功能 |
|------|------|------|
| POST | `/api/upload` | 上传 Excel 文件（支持同时上传 4 种文件） |
| GET | `/api/upload/{task_id}/status` | 查询上传任务状态 |

### IFIR 分析接口

| 方法 | 路由 | 功能 | 必选参数 |
|------|------|------|----------|
| GET | `/api/ifir/options` | 筛选项（联动） | - |
| GET | `/api/ifir/odm-analysis/options` | ODM 页筛选项（兼容） | - |
| GET | `/api/ifir/segment-analysis/options` | Segment 页筛选项（兼容） | - |
| GET | `/api/ifir/model-analysis/options` | Model 页筛选项（兼容） | - |
| POST | `/api/ifir/odm-analysis/analyze` | ODM 维度分析 | `filters.odms` |
| POST | `/api/ifir/segment-analysis/analyze` | Segment 维度分析 | `filters.segments` |
| POST | `/api/ifir/model-analysis/analyze` | Model 维度分析 | `filters.models` |
| POST | `/api/ifir/model-analysis/issue-details` | Issue 明细（分页） | `filters.model`，`filters.issue` |

### RA 分析接口

| 方法 | 路由 | 功能 | 必选参数 |
|------|------|------|----------|
| GET | `/api/ra/options` | 筛选项（联动） | - |
| GET | `/api/ra/odm-analysis/options` | ODM 页筛选项（兼容） | - |
| GET | `/api/ra/segment-analysis/options` | Segment 页筛选项（兼容） | - |
| GET | `/api/ra/model-analysis/options` | Model 页筛选项（兼容） | - |
| POST | `/api/ra/odm-analysis/analyze` | ODM 维度分析 | `filters.odms` |
| POST | `/api/ra/segment-analysis/analyze` | Segment 维度分析 | `filters.segments` |
| POST | `/api/ra/model-analysis/analyze` | Model 维度分析 | `filters.models` |

### 通用响应格式

所有 API 均使用统一响应格式：

```json
{
  "code": 0,        // 0=成功, 400=参数错误, 404=不存在, 500=服务错误
  "message": "success",
  "data": { ... }   // 业务数据，失败时为 null
}
```

---

## 5. 数据流说明

### 数据导入流程

```
用户在前端上传 Excel 文件
    ↓
POST /api/upload（multipart/form-data）
    ↓
后端保存文件到 uploads/ 目录，创建 UploadTask 记录（status=queued）
    ↓
返回 task_id，同时启动后台线程
    ↓
后台线程：EtlService.process_upload_task()
    ↓
依次处理：IFIR ROW → IFIR DETAIL → RA ROW → RA DETAIL
    ↓ 每处理一个文件更新 progress（25% / 50% / 75% / 100%）
每个文件：read_excel → 字段映射 → 数据清洗 → 计算哈希 → 批量 INSERT ON DUPLICATE KEY UPDATE
    ↓
刷新 map_odm_to_plant 映射表
    ↓
更新 task.status = "completed"
    ↓
前端轮询（每 1 秒）GET /api/upload/{task_id}/status，直到 completed
```

### 分析查询流程

```
用户在前端选择筛选条件（ODM/Segment/Model 维度）
    ↓
加载阶段：GET /api/{kpi}/options（附带当前已选条件）
后端实时联动：根据已选 ODM → 过滤可选 Segment 和 Model 范围
    ↓
用户点击"分析"按钮
    ↓
POST /api/{kpi}/{dimension}-analysis/analyze
    ↓ 后端查询逻辑：
    1. 查 ROW 表 → 计算 KPI 值 + 趋势 + Top 排名
    2. 查 DETAIL 表 → 计算 Top Issue（以 fault_category 统计）
    3. 查 ODM-Plant 映射表 → 在 DETAIL 表中过滤正确范围
    ↓
前端渲染：
  - 多对象 → 显示 Block D 汇总对比（多线趋势 + 矩阵表 + 饼图）
  - 每个对象 → 显示独立分析卡片（趋势图 + Top 排名表格 + AI 总结）
    ↓
用户点击 Top Issue 链接（仅 IFIR Model/ODM 分析）
    ↓
POST /api/ifir/model-analysis/issue-details（分页）
后端查 fact_ifir_detail → 返回索赔单级明细
前端展示 Issue 明细弹窗（含分页）
```

---

*文档由代码自动归纳生成，如有更新请同步修改本文档。*
