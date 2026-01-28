# RA Segment Analysis 完整工程任务书

## 0. 模块范围与目标

**模块名称**：RA Segment Analysis
**核心分析对象**：Segment（必选，多选，页面突出显示）
**默认趋势窗口**：最近 6 个月
**结果展示方式**：按 Segment 生成卡片，外层横向拖动切换
**卡片与区块结构**：Block A / Block B / Block C / Block D

* **Block A**：该 Segment 近月短期 RA 趋势（默认 6 个月）
* **Block B**：Top 结构（Top ODM 与 Top Model，在 Block B 内部左右拖动切换）
* **Block C**：AI Summary
* **Block D**：多 Segment 汇总饼图 + 数据表（仅多选 Segment 时显示）

> 仅基于你已定义的 IFIR Segment 模式“等价迁移”到 RA，不新增其他维度或功能。

---

## 1. 数据与数据库映射（基于你项目的 RA row / RA detail）

### 1.1 主数据表（用于趋势、Top 结构、饼图）

来源：`RA row.xlsx` → Sheet `Export`（聚合事实表）

字段映射（必须用到）：

* `Claim_month`：月份（时间轴）
* `Segment`：Segment 维度
* `Supplier_NEW`：ODM 维度（你项目中 ODM=Supplier_NEW）
* `Model`：Mode/Model 维度
* `RA CLAIM`：分子
* `RA MM`：分母

> 前端不计算 RA 公式，只展示后端计算后的 ra 数值。后端计算依据 RA CLAIM / RA MM。

### 1.2 明细表（当前模块不强制使用）

来源：`RA DETAIL.xlsx`（包含 Problem / Part / Fault 等字段）
本模块当前需求仅需 Top ODM / Top Model，不要求 Top issue 下钻，因此明细表不作为必用数据源。

---

## 2. RA 指标口径（后端统一）

### 2.1 基础公式

[
\boxed{
RA = \frac{\sum RA_CLAIM}{\sum RA_MM}
}
]

* 对任意筛选条件、任意聚合维度一致
* RA 展示形式由前端决定（ratio 或百分比），但数值计算由后端固定

---

## 3. 页面路由与入口

* Path：`/kpi/ra/segment-analysis`
* Name：`RaSegmentAnalysis`
* Page：`RaSegmentAnalysisPage.vue`

---

## 4. 页面布局结构

页面从上到下：

1. **Filter Panel（筛选区）**
2. **Analyze 按钮**
3. **Result Area（结果区）**

Result Area 结构：

* **Row 1：同级并列**

  * Block A（Trend，跟随当前 active Segment）
  * Block B（Top 结构，跟随当前 active Segment，内部可拖动切换）
  * Block D（多 Segment 汇总饼图 + 表格，仅在多选 Segment 时显示，不随 active Segment 变化）
* **Row 2**

  * Block C（AI Summary，跟随当前 active Segment）

> 只选 1 个 Segment 时：隐藏 Block D，Row1 只显示 Block A + Block B。

---

## 5. 前端组件拆分

### 5.1 页面容器

`RaSegmentAnalysisPage.vue`
职责：

* onMounted 拉 options
* 绑定 store
* 触发 analyze
* 渲染四个 block（A/B/C 取 activeCard，D 取 summary）

### 5.2 筛选区（突出 Segment）

`RaSegmentFilterPanel.vue`

控件：

* MonthRangePicker：startMonth, endMonth（默认最近 6 个月）
* SegmentMultiSelect：必选，多选（视觉层级最高）
* OdmMultiSelect：可选，多选（辅助筛选）
* ModelMultiSelect：可选，多选（辅助筛选）
* Analyze Button

交互规则：

* Segment 未选择：Analyze 禁用
* Analyze 成功后：筛选区进入只读变灰态（lockedFilters=true）展示已选项，避免“筛选与结果不一致”
* 需要修改筛选时：触发 unlockFilters（状态机，不新增复杂功能）

### 5.3 外层 Segment Carousel（切换 Segment 卡片）

`RaSegmentResultCarousel.vue`

* 输入：cards, activeIndex
* 输出：indexChange(newIndex)
* 暴露：scrollToIndex(index)
* 实现：Swiper 或 scroll-snap（要求稳定同步 activeIndex）

### 5.4 Block A（趋势图）

`RaTrendChart.vue`

* 输入：trend[]（[{month, ra}]）
* 输出：无

### 5.5 Block B（Top ODM / Top Model 内部拖动切换）

`RaSegmentTopSwitcher.vue`

* 内部两页：

  * Page1：`TopOdmTable.vue`
  * Page2：`TopModelTable.vue`
* 支持左右拖动切换 Top ODM ↔ Top Model
* 视图指示器：两段 tab 或两个 dot（显示当前页）
* 默认页：Top ODM
* 外层切换 segment 时：BlockB 重置为 Top ODM

输入：

* topOdms[]
* topModels[]
* activeView（可选）

输出：

* viewChange("odm" | "model")

实现约束：

* Block B 内部 swipe 不得触发外层 Segment Carousel 切换（需隔离事件 / 使用独立 swiper 容器）

### 5.6 Block C（AI Summary）

`RaAiSummaryPanel.vue`

* 输入：ai_summary string

### 5.7 Block D（多 Segment 饼图 + 表格）

`RaSegmentPieSummary.vue`

* 展示条件：selectedSegments.length > 1 && summary.segment_pie 有数据
* 内容：

  * 饼图：每个 segment 的 share
  * 表格：segment / ra / share / ra_claim / ra_mm（或后端返回的聚合分子分母）

输入：

* pieRows[]（后端返回）
* timeRange 摘要（可选）
* dataAsOf（可选）

---

## 6. 状态管理（Pinia）

Store：`useRaSegmentAnalysisStore`

### 6.1 State

options

* monthMin, monthMax, dataAsOf
* segments: string[]
* odms: string[]
* models: string[]

filtersDraft

* startMonth: string
* endMonth: string
* segments: string[]（必选）
* odms: string[] | null（null 表示 All）
* models: string[] | null（null 表示 All）
* trendMonths: number（默认 6）

ui

* loadingOptions: boolean
* analyzing: boolean
* lockedFilters: boolean
* error: string | null

result

* cards: RaSegmentCardData[]
* activeIndex: number
* lastRequest: object | null

blockBView

* activeTopView: "odm" | "model"（默认 "odm"）

summary

* segmentPie: SegmentPieRow[]（用于 Block D）

### 6.2 Getters

* isAnalyzeEnabled：segments 非空 && 时间合法
* activeCard：cards[activeIndex] || null
* segmentList：cards.map(c => c.segment)
* showBlockD：filtersDraft.segments.length > 1

### 6.3 Actions

* initOptions()
* setFiltersDraft(partial)
* analyze()
* setActiveIndex(index)
* setTopView(view)
* lockFilters()/unlockFilters()

切换 segment 时规则：

* setActiveIndex 后：activeTopView 重置为 "odm"

---

## 7. API 设计与数据交互

### 7.1 Options API

**GET** `/api/ra/segment-analysis/options`

返回：

```json
{
  "month_min": "2023-01",
  "month_max": "2025-12",
  "data_as_of": "2025-12",
  "segments": ["SEG_A"],
  "odms": ["ODM_X"],
  "models": ["MODEL_1"]
}
```

用途：

* 初始化筛选项候选
* 计算默认时间范围（end=month_max，start=end-5）

### 7.2 Analyze API（返回 cards + summary，用于 Block D）

**POST** `/api/ra/segment-analysis/analyze`

Request：

```json
{
  "time_range": { "start_month": "2025-07", "end_month": "2025-12" },
  "filters": {
    "segments": ["SEG_A", "SEG_B"],
    "odms": ["ODM_X"],
    "models": ["MODEL_1"]
  },
  "view": {
    "trend_months": 6,
    "top_n": 1
  }
}
```

Response：

```json
{
  "meta": { "data_as_of": "2025-12" },
  "summary": {
    "segment_pie": [
      { "segment": "SEG_A", "ra": 0.018, "share": 0.55, "ra_claim": 20, "ra_mm": 1100 },
      { "segment": "SEG_B", "ra": 0.015, "share": 0.45, "ra_claim": 16, "ra_mm": 1050 }
    ]
  },
  "cards": [
    {
      "segment": "SEG_A",
      "trend": [
        { "month": "2025-07", "ra": 0.012 },
        { "month": "2025-08", "ra": 0.010 }
      ],
      "top_odms": [
        { "rank": 1, "odm": "ODM_X", "ra": 0.030, "ra_claim": 12, "ra_mm": 400 }
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

* `share` 的口径由后端固定返回，前端不自行推导
* trend / top 表中的 ra 也由后端计算返回

---

## 8. 后端查询与计算逻辑（SQL 伪代码）

数据源：`fact_ra_row_monthly`（由 RA row 落库）

字段建议映射：

* month_date ← Claim_month（建议落库为 DATE 或 YYYY-MM）
* segment ← Segment
* odm ← Supplier_NEW
* model ← Model
* ra_claim ← RA CLAIM
* ra_mm ← RA MM

### 8.1 基础过滤条件

* month_date between :start and :end
* segment in :segments
* 若 odms 非 All：odm in :odms
* 若 models 非 All：model in :models

### 8.2 Block A：Segment 月度趋势

```sql
SELECT
  segment,
  month_date,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment, month_date
ORDER BY segment, month_date;
```

服务层：

* ra_m = ra_claim_sum / ra_mm_sum
* 截取最近 trend_months（默认 6），以 end_month 为终点

### 8.3 Block B：Top ODM（segment 内）

```sql
SELECT
  segment,
  odm,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment, odm;
```

服务层：

* ra_odm = ra_claim_sum / ra_mm_sum
* 对每个 segment 内排序取 TopN（默认 1）

### 8.4 Block B：Top Model（segment 内）

```sql
SELECT
  segment,
  model,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment, model;
```

服务层：

* ra_model = ra_claim_sum / ra_mm_sum
* 对每个 segment 内排序取 TopN

### 8.5 Block D：多 Segment 汇总（饼图与表格）

```sql
SELECT
  segment,
  SUM(ra_claim) AS ra_claim_sum,
  SUM(ra_mm) AS ra_mm_sum
FROM fact_ra_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment;
```

服务层：

* ra_seg = ra_claim_sum / ra_mm_sum
* share 由后端计算并返回（口径固定）：

  * 方案必须二选一并固化在后端配置
  * 前端不参与 share 计算

---

## 9. 前端渲染与交互逻辑

### 9.1 Analyze 数据流

1. 校验：segments 非空、时间合法
2. 调用 Analyze API
3. 成功：

* result.cards = resp.cards
* summary.segmentPie = resp.summary.segment_pie（当 segments>1）
* result.activeIndex = 0
* ui.lockedFilters = true
* blockBView.activeTopView = "odm"

4. 失败：

* ui.error 写入
* toast 提示
* 是否保留旧结果：默认保留

### 9.2 外层 Segment 切换（Carousel + Selector）

* Carousel 拖动触发 indexChange → store.setActiveIndex
* Selector 点击触发 selectIndex → store.setActiveIndex + carousel.scrollToIndex
* 切换 segment 后：Block B 视图重置为 Top ODM

### 9.3 Block B 内部拖动切换（Top ODM ↔ Top Model）

* 用户在 Block B 内左右滑动
* 触发 viewChange("odm"|"model") → store.setTopView
* 只切换 Block B 内容，不影响外层 Segment carousel

### 9.4 Block D 显示规则

* filtersDraft.segments.length > 1 且 summary.segmentPie 非空 → 显示
* 否则隐藏
* Block D 不跟随 active segment 切换

---

## 10. 交互事件清单

Filter Panel

* changeTimeRange
* changeSegments（主对象）
* changeOdms（可选）
* changeModels（可选）
* clickAnalyze

Result Area（外层）

* segmentCarouselIndexChange
* segmentSelectorClickIndex

Block B（内层）

* topViewSwipe（触发 viewChange）
* topViewChange

Lock 状态

* analyzeSuccess → lockedFilters=true
* unlockFilters → lockedFilters=false

---

## 11. 目录结构建议

```
src/
  pages/
    kpi/ra/segment-analysis/
      RaSegmentAnalysisPage.vue

  components/
    kpi/ra/segment-analysis/
      RaSegmentFilterPanel.vue
      RaSegmentResultCarousel.vue
      SegmentSelector.vue

      RaTrendChart.vue
      RaSegmentTopSwitcher.vue
      TopOdmTable.vue
      TopModelTable.vue
      RaSegmentPieSummary.vue
      RaAiSummaryPanel.vue
      EmptyState.vue

  stores/
    kpi/ra/
      useRaSegmentAnalysisStore.ts

  api/
    kpi/ra/
      raSegmentAnalysisApi.ts

  types/
    kpi/ra/
      raSegmentAnalysis.ts

  utils/
    date/
      month.ts
```

---

## 12. TypeScript 类型定义

```ts
export type RaTrendPoint = { month: string; ra: number };

export type TopOdmRow = {
  rank: number;
  odm: string;
  ra: number;
  ra_claim?: number;
  ra_mm?: number;
};

export type TopModelRow = {
  rank: number;
  model: string;
  ra: number;
  ra_claim?: number;
  ra_mm?: number;
};

export type SegmentPieRow = {
  segment: string;
  ra: number;
  share: number;
  ra_claim?: number;
  ra_mm?: number;
};

export type RaSegmentCardData = {
  segment: string;
  trend: RaTrendPoint[];
  top_odms: TopOdmRow[];
  top_models: TopModelRow[];
  ai_summary: string;
};

export type RaSegmentAnalyzeResponse = {
  meta: { data_as_of: string };
  summary?: { segment_pie?: SegmentPieRow[] };
  cards: RaSegmentCardData[];
};
```

---

## 13. 验收标准

1. 页面初始化拉 options，默认时间范围最近 6 个月
2. Segment 未选择时 Analyze 禁用
3. Analyze 成功后返回 cards，外层 Segment Carousel 可左右拖动切换
4. Block A 显示 active segment 的 RA 趋势（默认 6 点）
5. Block B 支持内部左右拖动切换 Top ODM ↔ Top Model，且不影响外层切换
6. 多选 Segment 时 Block D 展示饼图与表格，数据与筛选一致
7. 切换 segment 后 Block B 重置为 Top ODM
8. Analyze 成功后筛选区进入只读变灰态，保证筛选与结果一致性
9. 前端不硬编码 RA 公式与 share 口径，仅展示后端返回值
