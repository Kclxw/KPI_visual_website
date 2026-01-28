# IFIR Segment Analysis 模块分析过程与工程任务书

## 0. 模块范围

**模块名称**：IFIR Segment Analysis
**核心分析对象**：Segment（支持多选，筛选区突出 Segment）
**默认趋势窗口**：最近 6 个月
**结果展示方式**：按 Segment 生成卡片，横向拖动切换
**卡片结构**：Block A / Block B / Block C / Block D

* **Block A**：该 Segment 近月短期 IFIR 趋势（默认 6 个月）
* **Block B**：该 Segment 的 Top 结构展示（Top ODM 与 Top Model，支持内部拖动切换）
* **Block C**：AI Summary
* **Block D**：多 Segment 汇总饼图（仅在选中多个 Segment 时展示），用于展示各 Segment 的 IFIR（或占比）与对应数据表

> Block D 与 Block A、Block B **同级并列排布**（例如 A/B/D 三块同一行或同一层级的并列布局），Block C 放在下方或右侧独立区域，保持总结不干扰图表阅读。

---

## 1. 数据与数据库映射

### 1.1 数据源（与 IFIR ROW 一致）

使用月度聚合数据（IFIR ROW / Export）即可满足当前需求。

字段映射：

* month：`Delivery_month`
* segment：`Segment`
* odm：`Supplier_NEW`
* model：`Model`
* IFIR 计算基础：`BOX CLAIM`、`BOX MM`

> IFIR 的具体计算口径由后端固定，前端仅展示后端返回的 ifir 数值与占比结果。

### 1.2 落库建议（同 ODM 模块一致）

表名示例：`fact_ifir_row_monthly`
关键字段：

* month_date (DATE) ← Delivery_month
* segment (VARCHAR) ← Segment
* odm (VARCHAR) ← Supplier_NEW
* model (VARCHAR) ← Model
* box_claim (INT) ← BOX CLAIM
* box_mm (INT) ← BOX MM

索引建议：

* idx_segment_month (segment, month_date)
* idx_month_date (month_date)
* idx_odm_month (odm, month_date)
* idx_model_month (model, month_date)

---

## 2. 分析过程（系统内部逻辑）

### 2.1 输入（用户筛选条件）

* 时间范围：start_month, end_month（默认最近 6 个月）
* Segment：必选，多选（主对象）
* 可选：ODM（多选）、Model（多选）

### 2.2 分析单元与输出结构

系统输出两类数据：

**(1) Segment 卡片数据（cards）**：每个 Segment 一张卡片

* Block A：该 Segment 的月度 IFIR trend（默认 6 点）
* Block B：该 Segment 的 Top ODM、Top Model（Top1）
* Block C：该 Segment 的 AI Summary

**(2) 多 Segment 汇总数据（summary）**：对应 Block D

* 当选择多个 Segment 时，提供：

  * 各 Segment 的 IFIR 值（在同一时间范围内的聚合值）
  * 各 Segment 的占比（用于饼图）
  * 对应明细表（segment、ifir、share、box_claim、box_mm 等）

> Block D 是“多 Segment 汇总视图”，不跟随单张卡片切换而变化（它反映的是当前筛选下所有选中 Segment 的整体对比）。

---

## 3. 页面路由与入口

* Path：`/kpi/ifir/segment-analysis`
* Name：`IfirSegmentAnalysis`
* Page：`IfirSegmentAnalysisPage.vue`

---

## 4. 页面布局结构

### 4.1 总体布局（自上而下）

1. Filter Panel（筛选区）
2. Analyze 按钮
3. Result Area（结果区）

### 4.2 Result Area 布局（关键：A/B/D 同级并列）

推荐区域结构（不引入额外功能，只定义布局关系）：

* **Row 1（同级并列）**

  * Block A：Trend（当前 active Segment）
  * Block B：Top（当前 active Segment，内部拖动切换 Top ODM / Top Model）
  * Block D：Pie（全选 Segment 汇总，仅多 Segment 时出现）
* **Row 2**

  * Block C：AI Summary（当前 active Segment）

> 当仅选择 1 个 Segment：Block D 不展示，Row 1 只保留 A + B 并列，或 A/B 撑满宽度。

---

## 5. 前端组件拆分

### 5.1 页面容器

`IfirSegmentAnalysisPage.vue`

* 初始化拉 options
* 维护/绑定 store
* 触发 analyze
* 渲染 A/B/C（来自 active card）与 D（来自 summary）

### 5.2 筛选区

`IfirSegmentFilterPanel.vue`
控件：

* MonthRangePicker（默认近 6 个月）
* SegmentMultiSelect（必选，多选，视觉层级最高）
* OdmMultiSelect（可选）
* ModelMultiSelect（可选）
* Analyze Button

交互规则：

* Segment 未选：Analyze 禁用
* Analyze 成功后筛选区进入只读态（变灰展示已选项），保证“结果与筛选一致”
* 允许通过解锁操作（如 store.unlockFilters）重新编辑筛选（仅状态机，不扩展新功能）

### 5.3 Segment 卡片 Carousel（切换 segment）

`IfirSegmentResultCarousel.vue`

* 输入：cards, activeIndex
* 输出：indexChange
* 暴露：scrollToIndex

### 5.4 单张 Segment 卡片拆分

`IfirSegmentCardShell.vue`（可选：只负责 header 与布局槽位）

* 但为了减少复杂度，页面可以直接渲染 activeCard 的各个 block，无需把 A/B/C 包在单独 Card 组件里
* 若需要卡片化样式，则用 `IfirSegmentCard.vue` 统一 header 与边框

### 5.5 Block A

`IfirTrendChart.vue`

* 输入：trend[]
* 输出：无（纯展示）

### 5.6 Block B（关键：内部拖动切换）

`IfirSegmentTopSwitcher.vue`

* 内部包含两页：

  * Page 1：Top ODM 表 `TopOdmTable.vue`
  * Page 2：Top Model 表 `TopModelTable.vue`
* 支持 **左右拖动切换**（类似小型 carousel）
* 同时提供一个轻量指示器（例如两个小点或 tab，显示当前在 ODM 页还是 Model 页）

输入 props：

* topOdms[]
* topModels[]
* activeView（"odm" | "model"）可选（由 store 管控或组件内部自控）

输出 events：

* viewChange("odm"|"model")

行为规则：

* 默认展示 Top ODM（进入卡片先看 ODM）
* 用户在 Block B 内部左右拖动：

  * 向左/右滑动切换到另一个视图
  * 切换时不影响外层 Segment Carousel 的 activeIndex
  * 外层切换 segment 时，Block B 视图重置为默认（Top ODM）

### 5.7 Block C

`AiSummaryPanel.vue`

* 输入：ai_summary string

### 5.8 Block D（多 Segment 饼图 + 数据表）

`IfirSegmentPieSummary.vue`

* 展示条件：selectedSegments.length > 1 且 summary.pie 有数据
* 内容：

  * 饼图：各 Segment 占比
  * 表格：与饼图一致的结构化数据（segment、ifir、share、box_claim、box_mm）
* 输入：

  * pieSeries[]（用于饼图）
  * tableRows[]（用于表格）
  * dataAsOf、timeRange 摘要（可选）

---

## 6. 状态管理（Pinia）

Store：`useIfirSegmentAnalysisStore`

### 6.1 State

options

* monthMin, monthMax, dataAsOf
* segments[], odms[], models[]

filtersDraft

* startMonth, endMonth
* segments: string[]（必选）
* odms: string[] | null（null 表示 All）
* models: string[] | null（null 表示 All）
* trendMonths: number（默认 6）

ui

* loadingOptions
* analyzing
* lockedFilters
* error

result

* cards: IfirSegmentCardData[]
* activeIndex: number
* lastRequest

blockBView

* topViewBySegment: Record<string, "odm"|"model">（可选）

  * 若不想做 per-segment 记忆，则只存一个 `activeTopView` 并在切换 segment 时重置为 "odm"

summary

* segmentPie: Array<{ segment: string; ifir: number; share: number; box_claim?: number; box_mm?: number }>
* hasMultiSegment: boolean

### 6.2 Getters

* isAnalyzeEnabled：segments 非空 + 时间合法
* activeCard：cards[activeIndex]
* segmentList：cards.map(c => c.segment)
* showBlockD：filtersDraft.segments.length > 1

### 6.3 Actions

* initOptions()
* setFiltersDraft(partial)
* analyze()
* setActiveIndex(index)（切换 segment）
* setTopView(view)（Block B 内部切换）
* lockFilters()/unlockFilters()

切换 segment 时的规则：

* setActiveIndex 后，将 Block B 视图重置为 "odm"（符合你说的默认看更清晰的层级，不在 B 内保持上一个 segment 的 view）

---

## 7. API 设计与数据交互

### 7.1 Options API

**GET** `/api/ifir/segment-analysis/options`

返回：

* monthMin, monthMax, dataAsOf
* segments[], odms[], models[]

### 7.2 Analyze API（返回 cards + summary，用于 Block D）

**POST** `/api/ifir/segment-analysis/analyze`

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
      { "segment": "SEG_A", "ifir": 0.18, "share": 0.55, "box_claim": 20, "box_mm": 110 },
      { "segment": "SEG_B", "ifir": 0.15, "share": 0.45, "box_claim": 16, "box_mm": 95 }
    ]
  },
  "cards": [
    {
      "segment": "SEG_A",
      "trend": [
        { "month": "2025-07", "ifir": 0.12 },
        { "month": "2025-08", "ifir": 0.10 }
      ],
      "top_odms": [
        { "rank": 1, "odm": "ODM_X", "ifir": 0.30, "box_claim": 12, "box_mm": 40 }
      ],
      "top_models": [
        { "rank": 1, "model": "MODEL_1", "ifir": 0.28, "box_claim": 9, "box_mm": 32 }
      ],
      "ai_summary": "..."
    }
  ]
}
```

约束：

* Block D 的饼图与表格来自 `summary.segment_pie`
* Block A/B/C 来自 `cards[]`
* 前端不计算 ifir，仅展示

---

## 8. 后端查询逻辑（SQL 伪代码）

数据源：`fact_ifir_row_monthly`

### 8.1 基础过滤

* month_date between start and end
* segment in selected_segments
* 若 odms 非 All：odm in selected_odms
* 若 models 非 All：model in selected_models

### 8.2 Block A：Segment 趋势

```sql
SELECT
  segment,
  month_date,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment, month_date
ORDER BY segment, month_date;
```

服务层计算 ifir，截取最近 trend_months（默认 6）

### 8.3 Block B：Top ODM

```sql
SELECT
  segment,
  odm,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment, odm;
```

服务层按 segment 分组计算 ifir/贡献，排序取 TopN（默认 1）

### 8.4 Block B：Top Model

```sql
SELECT
  segment,
  model,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment, model;
```

服务层按 segment 分组计算 ifir/贡献，排序取 TopN

### 8.5 Block D：多 Segment 饼图汇总（segment 级聚合）

```sql
SELECT
  segment,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row_monthly
WHERE month_date BETWEEN :start AND :end
  AND segment IN (:segments)
  AND (:odms_is_all = 1 OR odm IN (:odms))
  AND (:models_is_all = 1 OR model IN (:models))
GROUP BY segment;
```

服务层：

* 计算每个 segment 的 ifir
* 计算 share（例如 share = segment_ifir / sum(segment_ifir) 或按你们定义的“占比口径”）
* 返回 `segment_pie[]` 给前端

> share 的计算口径必须由后端固定一致，前端只用来画饼图与表格展示。

---

## 9. 前端渲染与交互逻辑

### 9.1 Analyze 数据流

1. 校验：segments 非空、时间合法
2. 请求 Analyze API
3. 成功：

* result.cards = resp.cards
* summary.segmentPie = resp.summary.segment_pie（若 segments>1）
* result.activeIndex = 0
* ui.lockedFilters = true
* blockBView 重置为 "odm"

4. 失败：toast + error（是否清空旧结果按你们策略，默认保留更稳）

### 9.2 外层 Segment 切换（Carousel + Selector）

* 拖动外层 carousel：更新 activeIndex
* 点击 segment selector：跳转到对应卡片
* 切换 segment 时：

  * Block B 视图重置为 Top ODM（"odm"）

### 9.3 Block B 内部拖动切换（Top ODM ↔ Top Model）

* Block B 自己是一个“小型可拖动卡片”
* 用户左右拖动 Block B：

  * viewChange("odm" | "model")
  * 渲染对应表格
* Block B 的拖动不触发外层 Segment Carousel 的切换

  * 实现上需要在 Block B 的 swipe 组件中阻止事件向外层传递，或使用独立 swiper 容器

### 9.4 Block D 显示规则

* 若 filtersDraft.segments.length > 1 且 summary.segmentPie 有数据：显示 Block D
* 否则隐藏 Block D
* Block D 与当前 active segment 无关（它反映多 segment 的整体对比）

---

## 10. 交互事件清单

Filter Panel

* changeTimeRange
* changeSegments（主维度）
* changeOdms（可选）
* changeModels（可选）
* clickAnalyze

Result Area（外层）

* segmentCarouselIndexChange
* segmentSelectorClickIndex

Block B（内层）

* topSwitcherViewChange（odm/model）
* topSwitcherSwipeLeftRight（触发 viewChange）

Lock 状态

* analyzeSuccess → lockedFilters = true
* unlockFilters → lockedFilters = false

---

## 11. 目录结构建议

```
src/
  pages/
    kpi/ifir/segment-analysis/
      IfirSegmentAnalysisPage.vue

  components/
    kpi/ifir/segment-analysis/
      IfirSegmentFilterPanel.vue
      IfirSegmentResultCarousel.vue
      SegmentSelector.vue

      IfirTrendChart.vue
      IfirSegmentTopSwitcher.vue
      TopOdmTable.vue
      TopModelTable.vue
      IfirSegmentPieSummary.vue
      AiSummaryPanel.vue
      EmptyState.vue

  stores/
    kpi/ifir/
      useIfirSegmentAnalysisStore.ts

  api/
    kpi/ifir/
      ifirSegmentAnalysisApi.ts

  types/
    kpi/ifir/
      ifirSegmentAnalysis.ts

  utils/
    date/
      month.ts
```

---

## 12. TypeScript 类型定义

```ts
export type IfirTrendPoint = { month: string; ifir: number };

export type TopOdmRow = {
  rank: number;
  odm: string;
  ifir: number;
  box_claim?: number;
  box_mm?: number;
};

export type TopModelRow = {
  rank: number;
  model: string;
  ifir: number;
  box_claim?: number;
  box_mm?: number;
};

export type SegmentPieRow = {
  segment: string;
  ifir: number;
  share: number;
  box_claim?: number;
  box_mm?: number;
};

export type IfirSegmentCardData = {
  segment: string;
  trend: IfirTrendPoint[];
  top_odms: TopOdmRow[];
  top_models: TopModelRow[];
  ai_summary: string;
};

export type IfirSegmentAnalyzeResponse = {
  meta: { data_as_of: string };
  summary?: { segment_pie?: SegmentPieRow[] };
  cards: IfirSegmentCardData[];
};
```

---

## 13. 验收标准

1. 页面初始化拉取 options，默认时间范围最近 6 个月
2. Segment 未选择时 Analyze 禁用
3. Analyze 成功返回 cards 后，外层 Segment Carousel 可左右拖动切换
4. Block A 显示 active segment 的 IFIR 趋势（默认 6 点）
5. Block B 支持内部左右拖动切换：

   * 初始为 Top ODM
   * 拖动后切到 Top Model
   * 不影响外层 segment 切换
6. Block D 在多 segment 选择时展示饼图与数据表，数据与筛选条件一致
7. 切换 segment 后，Block B 视图重置为 Top ODM
8. Analyze 成功后筛选区进入只读变灰态，保证筛选与结果一致性
9. 前端不写死 IFIR 计算公式，仅展示后端返回 ifir 与 share

---
