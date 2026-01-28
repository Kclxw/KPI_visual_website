# RA – ODM Analysis 完整工程任务书（含 Block D）

## 0. 模块范围与目标

**模块名称**：RA ODM Analysis
**核心分析对象**：ODM（必选，多选，筛选区突出展示）
**默认趋势窗口**：最近 6 个月
**结果展示方式**：按 ODM 生成卡片，外层横向拖动切换
**卡片与区块结构**：Block A / Block B / Block C / Block D

* **Block A**：当前 active ODM 的近月短期 RA 趋势（默认 6 个月）
* **Block B**：当前 active ODM 的 Top Model（机型驱动，默认 Top1）
* **Block C**：当前 active ODM 的 AI Summary
* **Block D**：多 ODM 汇总饼图 + 数据表（仅当多选 ODM 时显示，不随 active ODM 切换）

> 本任务书只基于你已有 IFIR/RA 模块设计模式迁移，口径与交互不额外扩展。

---

## 1. 数据与数据库映射（基于你项目的 RA row）

### 1.1 主数据表（用于趋势、Top Model、饼图）

来源：`RA row.xlsx` → Sheet `Export`

字段映射（本模块必须使用）：

* `Claim_month`：月份（时间轴）
* `Supplier_NEW`：ODM（你项目里 ODM = Supplier_NEW）
* `Segment`：可选筛选维度
* `Model`：机型维度（Model = Mode）
* `RA CLAIM`：分子
* `RA MM`：分母

> RA DETAIL 不是本模块必需数据源（不做 issue 下钻）。

### 1.2 建议落库字段命名（便于后端实现）

表名示例：`fact_ra_row_monthly`

* month_date（YYYY-MM 或 DATE）← Claim_month
* odm（VARCHAR）← Supplier_NEW
* segment（VARCHAR）← Segment
* model（VARCHAR）← Model
* ra_claim（INT）← RA CLAIM
* ra_mm（INT）← RA MM

索引建议：

* idx_odm_month (odm, month_date)
* idx_month_date (month_date)
* idx_segment_month (segment, month_date)
* idx_model_month (model, month_date)

---

## 2. RA 指标口径（后端统一）

[
\boxed{
RA = \frac{\sum RA_CLAIM}{\sum RA_MM}
}
]

约束：

* 所有 ra 数值、share 占比由后端计算返回
* 前端不写死公式，不自行推导 share

---

## 3. 页面路由与入口

* Path：`/kpi/ra/odm-analysis`
* Name：`RaOdmAnalysis`
* Page：`RaOdmAnalysisPage.vue`

---

## 4. 页面布局结构

页面从上到下：

1. **Filter Panel（筛选区）**
2. **Analyze 按钮**
3. **Result Area（结果区）**

Result Area 推荐布局：

* **Row 1（同级并列）**

  * Block A（Trend，跟随 active ODM）
  * Block B（Top Model，跟随 active ODM）
  * Block D（多 ODM 汇总饼图 + 表格，仅多选 ODM 时显示，不随 active ODM 变化）
* **Row 2**

  * Block C（AI Summary，跟随 active ODM）

> 仅选 1 个 ODM：隐藏 Block D，Row1 只显示 A + B（并列或撑满宽度）。

---

## 5. 前端组件拆分

### 5.1 页面容器

`RaOdmAnalysisPage.vue`
职责：

* onMounted 拉 options
* 绑定 store
* 点击 Analyze 触发 store.analyze()
* 渲染 Block A/B/C（基于 activeCard）与 Block D（基于 summary）

### 5.2 筛选区（突出 ODM）

`RaOdmFilterPanel.vue`

控件：

* MonthRangePicker：startMonth, endMonth（默认最近 6 个月）
* OdmMultiSelect：必选，多选（主对象，视觉层级最高）
* SegmentMultiSelect：可选，多选
* ModelMultiSelect：可选，多选（Model=Mode）
* Analyze Button

交互规则：

* ODM 未选择：Analyze 禁用
* Analyze 成功后：筛选区进入 lockedFilters 只读态（变灰展示），保证“结果与筛选一致”
* 允许通过 unlockFilters 状态机解锁后重新编辑（不新增复杂交互）

### 5.3 外层 ODM Carousel（切换 ODM）

`RaOdmResultCarousel.vue`

* 输入：cards, activeIndex
* 输出：indexChange(newIndex)
* 暴露：scrollToIndex(index)
* 实现：Swiper 或 scroll-snap（需稳定同步 activeIndex）

### 5.4 Block A（趋势图）

`RaTrendChart.vue`

* 输入：trend[]（[{month, ra}]）
* 输出：无

### 5.5 Block B（Top Model 表格）

`RaTopModelTable.vue`

* 输入：topModels[]
* 输出：无

> 注意：ODM 模块的 Block B 不需要像 segment 模块那样在 ODM/Model 间切换，仅展示 Top Model。

### 5.6 Block C（AI Summary）

`RaAiSummaryPanel.vue`

* 输入：ai_summary string

### 5.7 Block D（多 ODM 饼图 + 数据表）

`RaOdmPieSummary.vue`

* 展示条件：selectedOdms.length > 1 && summary.odm_pie 有数据
* 内容：

  * 饼图：odm share
  * 表格：odm / ra / share / ra_claim / ra_mm
* 输入：

  * pieRows[]
  * timeRange / dataAsOf（可选）

---

## 6. 状态管理（Pinia）

Store：`useRaOdmAnalysisStore`

### 6.1 State

options

* monthMin, monthMax, dataAsOf
* odms: string[]
* segments: string[]
* models: string[]

filtersDraft

* startMonth: string
* endMonth: string
* odms: string[]（必选）
* segments: string[] | null（null 表示 All）
* models: string[] | null（null 表示 All）
* trendMonths: number（默认 6）
* topN: number（默认 1）

ui

* loadingOptions: boolean
* analyzing: boolean
* lockedFilters: boolean
* error: string | null

result

* cards: RaOdmCardData[]
* activeIndex: number
* lastRequest: object | null

summary

* odmPie: OdmPieRow[]（用于 Block D）

### 6.2 Getters

* isAnalyzeEnabled：odms 非空 && 时间合法
* activeCard：cards[activeIndex] || null
* odmList：cards.map(c => c.odm)
* showBlockD：filtersDraft.odms.length > 1

### 6.3 Actions

* initOptions()
* setFiltersDraft(partial)
* analyze()
* setActiveIndex(index)
* lockFilters()/unlockFilters()

切换 ODM 规则：

* setActiveIndex 做边界保护（0 ~ cards.length-1）

---

## 7. API 设计与数据交互

### 7.1 Options API

**GET** `/api/ra/odm-analysis/options`

返回：

```json
{
  "month_min": "2023-01",
  "month_max": "2025-12",
  "data_as_of": "2025-12",
  "odms": ["ODM_A", "ODM_B"],
  "segments": ["SEG_A", "SEG_B"],
  "models": ["MODEL_1", "MODEL_2"]
}
```

用途：

* 初始化筛选候选
* 默认时间范围计算：end=month_max，start=end-5

### 7.2 Analyze API（返回 cards + summary（BlockD））

**POST** `/api/ra/odm-analysis/analyze`

Request：

```json
{
  "time_range": { "start_month": "2025-07", "end_month": "2025-12" },
  "filters": {
    "odms": ["ODM_A", "ODM_B"],
    "segments": ["SEG_A"],
    "models": ["MODEL_1"]
  },
  "view": {
    "trend_months": 6,
    "top_model_n": 1
  }
}
```

Response：

```json
{
  "meta": { "data_as_of": "2025-12" },
  "summary": {
    "odm_pie": [
      { "odm": "ODM_A", "ra": 0.018, "share": 0.55, "ra_claim": 20, "ra_mm": 1100 },
      { "odm": "ODM_B", "ra": 0.015, "share": 0.45, "ra_claim": 16, "ra_mm": 1050 }
    ]
  },
  "cards": [
    {
      "odm": "ODM_A",
      "trend": [
        { "month": "2025-07", "ra": 0.012 },
        { "month": "2025-08", "ra": 0.010 }
      ],
      "top_models": [
        { "rank": 1, "model": "MODEL_1", "ra": 0.028, "ra_claim": 9, "ra_mm": 320 }
      ],
      "ai_summary": "..."
    }
  ]
}
```

约束：

* `share` 的计算口径后端固化并返回
* trend/top_models 的 ra 与分子分母均由后端聚合计算后返回
* 前端只渲染

---

## 8. 后端查询与计算逻辑（SQL 伪代码）

数据源：`fact_ra_row_monthly`

### 8.1 基础过滤条件

* month_date BETWEEN :start AND :end
* odm IN (:odm_list)
* 若 segments 非 All：segment IN (:segment_list)
* 若 models 非 All：model IN (:model_list)

### 8.2 Block A：ODM 月度趋势

```sql
SELECT
  odm,
  month_date,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND odm IN (:odm_list)
  AND (:segments_is_all = 1 OR segment IN (:segments))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY odm, month_date
ORDER BY odm, month_date;
```

服务层：

* ra_m = ra_claim_sum / ra_mm_sum
* 截取最近 trend_months（默认 6，以 end_month 为终点）

### 8.3 Block B：Top Model（ODM 内）

```sql
SELECT
  odm,
  model,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND odm IN (:odm_list)
  AND (:segments_is_all = 1 OR segment IN (:segments))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY odm, model;
```

服务层：

* ra_model = ra_claim_sum / ra_mm_sum
* 对每个 odm 内部排序取 TopN（默认 1）

### 8.4 Block D：多 ODM 汇总（饼图与表格）

```sql
SELECT
  odm,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND odm IN (:odm_list)
  AND (:segments_is_all = 1 OR segment IN (:segments))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY odm;
```

服务层：

* ra_odm = ra_claim_sum / ra_mm_sum
* share 由后端固化口径计算并返回（不由前端推导）

---

## 9. 前端渲染与交互逻辑

### 9.1 Analyze 数据流

1. 校验：odms 非空、时间合法
2. 调用 Analyze API
3. 成功：

* result.cards = resp.cards
* summary.odmPie = resp.summary.odm_pie（当 odms>1）
* result.activeIndex = 0
* ui.lockedFilters = true

4. 失败：

* ui.error 更新
* toast 提示
* 默认保留旧结果

### 9.2 外层 ODM 切换（Carousel + Selector）

* Carousel 拖动触发 indexChange → store.setActiveIndex
* Selector 点击触发 selectIndex → store.setActiveIndex + carousel.scrollToIndex

### 9.3 Block D 显示规则

* filtersDraft.odms.length > 1 且 summary.odmPie 非空 → 显示
* 否则隐藏
* Block D 不随 active ODM 切换

### 9.4 筛选锁定（变灰）状态机

* Analyze 成功后 lockedFilters=true：筛选区控件只读，展示已选项
* unlockFilters：允许修改后重新 Analyze

---

## 10. 交互事件清单

Filter Panel

* changeTimeRange
* changeOdms（主对象）
* changeSegments（可选）
* changeModels（可选）
* clickAnalyze
* clickUnlockFilters（若实现）

Result Area

* odmCarouselIndexChange
* odmSelectorClickIndex

---

## 11. 目录结构建议

```
src/
  pages/
    kpi/ra/odm-analysis/
      RaOdmAnalysisPage.vue

  components/
    kpi/ra/odm-analysis/
      RaOdmFilterPanel.vue
      RaOdmResultCarousel.vue
      OdmSelector.vue

      RaTrendChart.vue
      RaTopModelTable.vue
      RaOdmPieSummary.vue
      RaAiSummaryPanel.vue
      EmptyState.vue

  stores/
    kpi/ra/
      useRaOdmAnalysisStore.ts

  api/
    kpi/ra/
      raOdmAnalysisApi.ts

  types/
    kpi/ra/
      raOdmAnalysis.ts

  utils/
    date/
      month.ts
```

---

## 12. TypeScript 类型定义

```ts
export type RaTrendPoint = { month: string; ra: number };

export type TopModelRow = {
  rank: number;
  model: string;
  ra: number;
  ra_claim?: number;
  ra_mm?: number;
};

export type OdmPieRow = {
  odm: string;
  ra: number;
  share: number;
  ra_claim?: number;
  ra_mm?: number;
};

export type RaOdmCardData = {
  odm: string;
  trend: RaTrendPoint[];
  top_models: TopModelRow[];
  ai_summary: string;
};

export type RaOdmAnalyzeResponse = {
  meta: { data_as_of: string };
  summary?: { odm_pie?: OdmPieRow[] };
  cards: RaOdmCardData[];
};
```

---

## 13. 验收标准

1. 页面初始化拉 options，默认时间范围最近 6 个月
2. ODM 未选择时 Analyze 禁用
3. Analyze 成功后返回 cards，外层 ODM Carousel 可左右拖动切换
4. Block A 显示 active ODM 的 RA 趋势（默认 6 点）
5. Block B 显示 active ODM 的 Top Model 表格（默认 Top1）
6. 多选 ODM 时 Block D 展示饼图与表格，数据与筛选条件一致
7. Analyze 成功后筛选区进入只读变灰态，保证筛选与结果一致性
8. 前端不硬编码 RA 公式与 share 口径，仅展示后端返回值
