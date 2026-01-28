下面是**IFIR ODM 分析模块**的功能板块说明稿，已统一命名为 **IFIR**，按专业产品/数据分析人员的口径撰写，仅包含功能与行为描述，不包含过程性说明或建议。

---

# IFIR ODM Analysis 功能模块说明

## 一、模块定位与目标

**模块名称**：IFIR ODM Analysis
**模块目标**：
在指定时间范围内，对选定的一个或多个 ODM 进行 IFIR 表现分析，通过趋势、结构化数据表与智能总结，支持快速识别 ODM 层级的质量表现差异及潜在风险集中点。

该模块以 **ODM 为核心分析对象**，辅以 Segment 与 Model（Mode）等条件筛选，输出标准化、可对比的分析结果。

---

## 二、页面结构与整体布局

页面整体由三部分构成，自上而下依次为：

1. **筛选区（Filter Panel）**
2. **分析触发区（Analyze Action）**
3. **分析结果区（Result Area）**

---

## 三、筛选区功能说明

### 3.1 可选筛选维度

筛选区支持以下条件组合：

* **时间范围（Time Range）**

  * 月粒度选择
  * 默认时间窗口：最近 **6 个月**

* **ODM（必选，多选）**

  * 作为本模块的核心分析对象
  * 支持同时选择多个 ODM
  * 选中后在界面中以更高层级进行展示与强调

* **Segment（可选，多选）**

  * 用于进一步限定分析范围
  * 不影响 ODM 作为主分析对象的地位

* **Model / Mode（可选，多选）**

  * 用于限定某些特定机型
  * 作为 ODM 分析的下钻条件，而非主分析维度

### 3.2 交互特性

* ODM 被选定后，其选中状态在界面中保持清晰、稳定的展示
* 非核心筛选项（如 Model）在 ODM 确认后可呈现弱化或只读状态，用于减少分析对象混淆
* 当未选择 ODM 时，不允许触发分析

---

## 四、分析触发逻辑

* 用户完成筛选条件配置后，通过 **Analyze** 按钮触发分析
* 分析请求以以下条件为输入：

  * 时间范围
  * 选定的 ODM 列表
  * 可选的 Segment 与 Model 约束
* 每一个 ODM 作为一个独立的分析单元参与后续结果生成

---

## 五、分析结果区设计

分析结果区采用 **横向滑动（Carousel）结构**，用于展示多个 ODM 的分析结果。

### 5.1 ODM 结果卡片（ODM Result Card）

每一个被选中的 ODM 对应一张独立的结果卡片，卡片内部包含以下三个分析板块：

---

### Block A：IFIR 趋势分析（Trend）

* 展示该 ODM 在所选时间范围内的 **IFIR 月度趋势**
* 默认展示最近 **6 个月**
* 以折线图形式呈现
* 用于快速判断：

  * IFIR 整体走势（上升、下降、波动）
  * 是否存在异常波动或持续恶化趋势

---

### Block B：Top Model（Mode）分布表

* 在当前 ODM 与筛选条件下，对 Model（Mode）进行聚合分析
* 输出 **IFIR 表现最突出的 Top Model（默认 Top1）**
* 以结构化数据表形式展示，用于识别：

  * 主要 IFIR 贡献来源的机型
  * ODM 内部风险是否集中于少数 Model

---

### Block C：AI 分析总结

* 基于 Block A 的趋势特征与 Block B 的结构化结果生成文本总结
* 总结内容聚焦于：

  * IFIR 走势的定性判断
  * Top Model 的集中性或持续性特征
  * 对 ODM 当前质量状态的整体解读
* 不涉及具体执行动作，仅提供分析层面的判断与解释

---

### 5.2 多 ODM 切换方式

* 当用户选择多个 ODM 时：

  * 每个 ODM 对应一张结果卡片
  * 用户可通过 **左右拖动** 在不同 ODM 卡片之间切换
* 当前显示的 ODM 与其分析结果始终保持一一对应关系，避免跨 ODM 信息混杂

---

## 六、当前版本范围说明

* 本模块当前版本聚焦于：

  * IFIR 趋势
  * ODM 内部 Model 结构
  * 分析总结
* 关于 **不同 ODM 之间的整体占比或对比大图**，不包含在本阶段功能范围内

---

## 七、模块输出价值

通过 IFIR ODM Analysis 模块，用户可以在 ODM 层级上实现：

* 快速对比不同 ODM 的 IFIR 表现
* 识别 IFIR 问题是否集中在特定 ODM 或其内部的少数 Model
* 以统一结构化视图支持质量分析、评审与决策讨论

---
# IFIR ODM Analysis 工程任务书

## 0. 模块范围

**模块名称**：IFIR ODM Analysis
**核心分析对象**：ODM（支持多选）
**默认趋势窗口**：最近 6 个月
**结果展示方式**：按 ODM 生成卡片，横向拖动切换，每张卡片包含 3 个区块

* Block A：该 ODM 的 IFIR 趋势图
* Block B：该 ODM 下 Top Model（Mode）分布表
* Block C：AI 总结

**筛选维度**

* 时间范围：必选
* ODM：必选，多选
* Segment：可选
* Model（Mode）：可选，多选
* 本版本不做：不同 ODM 占比大图

---

## 1. 数据与数据库映射

### 1.1 数据表来源

本模块主要用到聚合口径表（来自你上传的 IFIR ROW 文件 Export 工作表）：

**IFIR_ROW（聚合表）字段（文件列名）**

* Delivery_month
* BRAND
* GEO
* Product_line
* Segment
* SERIES
* Model
* PLANT
* Mach_type
* Supplier_NEW
* BOX CLAIM
* BOX MM
* YEAR
* MONTH

> 其中 ODM 字段映射：**ODM = Supplier_NEW**
> 时间字段映射：**month = Delivery_month（YYYY-MM-01）**
> IFIR 计算依赖 BOX CLAIM 与 BOX MM（按你们内部口径计算，前端不写死口径）

（注：IFIR DETAIL 文件是明细表，本模块当前需求不要求用明细钻取，因此不作为必选数据源。）

### 1.2 建议落库字段命名（便于后端开发）

如果你们要把 IFIR ROW 落到 MySQL，建议统一成下列字段名，减少前端歧义：

表名示例：`fact_ifir_row_monthly`

* month_date (DATE) 对应 Delivery_month
* brand (VARCHAR) 对应 BRAND
* geo (VARCHAR) 对应 GEO
* product_line (VARCHAR) 对应 Product_line
* segment (VARCHAR) 对应 Segment
* series (VARCHAR) 对应 SERIES
* model (VARCHAR) 对应 Model
* plant (VARCHAR) 对应 PLANT
* mach_type (VARCHAR) 对应 Mach_type
* odm (VARCHAR) 对应 Supplier_NEW
* box_claim (INT) 对应 BOX CLAIM
* box_mm (INT) 对应 BOX MM
* year (INT) 对应 YEAR
* month (INT) 对应 MONTH

索引建议（用于查询性能）

* idx_month_date
* idx_odm_month (odm, month_date)
* idx_segment_month (segment, month_date)
* idx_model_month (model, month_date)

---

## 2. 页面路由与入口

### 2.1 路由

* Path：`/kpi/ifir/odm-analysis`
* Name：`IfirOdmAnalysis`
* Page：`IfirOdmAnalysisPage.vue`

---

## 3. 页面布局结构

页面分三段，从上到下：

1. Filter Panel（筛选区）
2. Analyze Button（分析触发）
3. Result Area（结果区，ODM Carousel 卡片）

结果区内部结构

* 上部：ODM Result Carousel（横向滑动容器）
* 下部：ODM Selector（ODM 切换条，用于点击跳转与当前高亮同步）

---

## 4. 前端组件拆分

### 4.1 页面容器

`IfirOdmAnalysisPage.vue`

* 负责布局与组件编排
* mounted 时拉取 options
* 绑定 store 状态，透传数据到子组件
* 接收子组件事件，调用 store actions

### 4.2 筛选区

`IfirOdmFilterPanel.vue`
控件清单

* MonthRangePicker：startMonth, endMonth（默认最近 6 个月）
* SegmentMultiSelect：可选，多选，默认 All
* ModelMultiSelect：可选，多选，默认 All
* OdmMultiSelect：必选，多选
* Analyze Button（也可放页面层，视你们 UI 习惯）

交互规则

* 未选择 ODM 时，Analyze 禁用
* 选择 ODM 后，筛选区要清晰展示当前 ODM 选择结果
* “多选变灰”规则按如下实现（不扩展新功能，只表达你描述的行为）

  * 当用户点击 Analyze 且结果返回后，筛选区进入只读态展示（控件变灰，仍展示已选项）
  * 若用户需要修改筛选条件，则必须触发一次显式的“编辑筛选”动作（可以是页面已有的 Modify Filters 按钮，或重新点击筛选区解锁，具体实现由前端选型决定，但必须体现：分析中的筛选状态与结果是一致且稳定的）

> 这条的关键目的是：分析对象 ODM 要更突出，避免用户在看结果时误改筛选导致混淆。

### 4.3 结果区容器

`IfirOdmResultCarousel.vue`

* 输入：cards 数组，activeIndex
* 输出：indexChange(newIndex)
* 支持外部方法：scrollToIndex(index)

实现可选

* Swiper
* 原生 scroll snap
  只要能稳定提供 activeIndex 同步即可

### 4.4 单张 ODM 卡片

`IfirOdmCard.vue`
每张卡片固定结构

Header

* odm 名称
* 时间范围摘要
* segment 与 model 筛选摘要
* dataAsOf

Block A：`IfirTrendChart.vue`

* 展示该 odm 的 month 序列与 ifir 序列，默认 6 个月
* 折线图即可

Block B：`TopModelTable.vue`

* 展示该 odm 下 top model 结果
* 默认 Top1，也允许后端返回 TopN，前端按返回渲染，不强制增加交互

Block C：`AiSummaryPanel.vue`

* 展示 aiSummary 文本
* 若为空，展示占位文案

### 4.5 ODM Selector

`OdmSelector.vue`

* 横向滚动 chip 或 tab
* 输入：odmList，activeIndex
* 点击：selectIndex(index)
* 与 carousel 双向联动

---

## 5. 状态管理设计（Pinia）

Store：`useIfirOdmAnalysisStore`

### 5.1 State

options

* monthMin
* monthMax
* segments: string[]
* models: string[]
* odms: string[]
* dataAsOf

filtersDraft

* startMonth: string
* endMonth: string
* segments: string[] | null（null 表示 All）
* models: string[] | null（null 表示 All）
* odms: string[]（必选）

ui

* loadingOptions: boolean
* analyzing: boolean
* lockedFilters: boolean（分析结果对应的筛选是否锁定展示）
* error: string | null

result

* cards: IfirOdmCardData[]
* activeIndex: number
* lastRequest: object | null

### 5.2 Getters

* isAnalyzeEnabled：odms 非空 且 时间合法
* activeCard：cards[activeIndex]
* odmList：cards.map(card => card.odm)

### 5.3 Actions

* initOptions()
* setFiltersDraft(partial)
* analyze()
* setActiveIndex(index)
* lockFilters() / unlockFilters()（用于实现变灰只读态）

---

## 6. 接口设计与数据交互

### 6.1 Options API

**GET** `/api/ifir/odm-analysis/options`

返回

* monthMin, monthMax, dataAsOf
* segments[]
* models[]
* odms[]

用途

* 初始化筛选项候选
* 让前端默认时间范围可计算为最近 6 个月

### 6.2 Analyze API

**POST** `/api/ifir/odm-analysis/analyze`

Request body

```json
{
  "time_range": { "start_month": "2025-07", "end_month": "2025-12" },
  "filters": {
    "segments": ["CONSUMER"],
    "models": ["XQ22E", "XQ24E"],
    "odms": ["ODM_A", "ODM_B"]
  },
  "view": {
    "trend_months": 6,
    "top_model_n": 1
  }
}
```

说明

* segments, models 允许为空数组或缺省，表示 All
* odms 必须有值
* trend_months 默认 6，本模块固定默认值为 6

Response body

```json
{
  "meta": { "data_as_of": "2025-12" },
  "cards": [
    {
      "odm": "ODM_A",
      "trend": [
        { "month": "2025-07", "ifir": 0.12 },
        { "month": "2025-08", "ifir": 0.10 }
      ],
      "top_models": [
        {
          "rank": 1,
          "model": "XQ24E",
          "ifir": 0.30,
          "box_claim": 12,
          "box_mm": 40
        }
      ],
      "ai_summary": "..."
    }
  ]
}
```

约束

* 前端仅渲染后端给出的 ifir 数值与 top_models，不在前端硬编码 ifir 公式
* 后端负责口径一致性，前端负责展示与交互

---

## 7. 后端查询逻辑（SQL 伪代码）

数据源：`fact_ifir_row_monthly`

### 7.1 基础过滤条件

* month_date between start and end
* odm in selected_odms
* if segments provided: segment in segments
* if models provided: model in models

### 7.2 ODM 趋势查询

目标：为每个 odm 返回按月聚合的 ifir 序列，长度为 trend_months（默认 6）

伪代码

```sql
SELECT
  odm,
  month_date,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row_monthly
WHERE month_date BETWEEN :start_month AND :end_month
  AND odm IN (:odm_list)
  AND (:segments_is_all = 1 OR segment IN (:segment_list))
  AND (:models_is_all = 1 OR model IN (:model_list))
GROUP BY odm, month_date
ORDER BY odm, month_date;
```

后端在服务层计算 ifir

* ifir = f(box_claim_sum, box_mm_sum) 按你们内部口径
* 再截取最近 trend_months 个点（以 end_month 为终点）

### 7.3 Top Model 查询

目标：在同一筛选条件下，对每个 odm 聚合 model，按 ifir 或贡献排序取 TopN（默认 1）

伪代码

```sql
SELECT
  odm,
  model,
  SUM(box_claim) AS box_claim_sum,
  SUM(box_mm) AS box_mm_sum
FROM fact_ifir_row_monthly
WHERE month_date BETWEEN :start_month AND :end_month
  AND odm IN (:odm_list)
  AND (:segments_is_all = 1 OR segment IN (:segment_list))
  AND (:models_is_all = 1 OR model IN (:model_list))
GROUP BY odm, model;
```

后端计算每行 model 的 ifir 后

* 对每个 odm 内部排序
* 取 top_model_n 条返回给前端

---

## 8. 前端渲染逻辑

### 8.1 Analyze 点击后的数据流

1. 校验

* odms 必须非空
* startMonth endMonth 合法

2. 请求

* store.analyze() 调用 Analyze API

3. 成功

* result.cards = resp.cards
* result.activeIndex = 0
* ui.lockedFilters = true（筛选区变灰只读展示）

4. 失败

* ui.error 写入
* toast 提示
* 不强制清空上一次结果（按你们产品策略决定，默认保留上次结果更稳）

### 8.2 Carousel 与 Selector 联动

单一数据源：store.result.activeIndex

* 用户拖动 carousel

  * carousel emit indexChange(newIndex)
  * store.setActiveIndex(newIndex)
  * selector 高亮同步

* 用户点击 selector 某个 odm

  * selector emit selectIndex(index)
  * store.setActiveIndex(index)
  * carousel.scrollToIndex(index)

### 8.3 卡片内部渲染规则

Block A

* trend 有数据：渲染折线
* trend 为空：渲染 empty state

Block B

* top_models 有数据：渲染表格
* top_models 为空：渲染 empty state

Block C

* ai_summary 有文本：渲染
* 为空：渲染占位文案

---

## 9. 交互事件清单

### 9.1 Filter Panel 事件

* changeTimeRange
* changeSegments
* changeModels
* changeOdms
* clickAnalyze

### 9.2 Result 区事件

* carouselIndexChange
* selectorClickIndex

### 9.3 锁定态事件

* analyzeSuccess 后 lockedFilters = true
* 若允许修改筛选

  * unlockFilters 触发后 lockedFilters = false
  * 修改条件并再次 Analyze 才生成新 cards
    （实现方式由前端 UI 决定，但锁定与解锁是必需的状态机）

---

## 10. 文件目录结构建议

```
src/
  pages/
    kpi/ifir/odm-analysis/
      IfirOdmAnalysisPage.vue

  components/
    kpi/ifir/odm-analysis/
      IfirOdmFilterPanel.vue
      IfirOdmResultCarousel.vue
      IfirOdmCard.vue
      IfirTrendChart.vue
      TopModelTable.vue
      AiSummaryPanel.vue
      OdmSelector.vue
      EmptyState.vue

  stores/
    kpi/ifir/
      useIfirOdmAnalysisStore.ts

  api/
    kpi/ifir/
      ifirOdmAnalysisApi.ts

  types/
    kpi/ifir/
      ifirOdmAnalysis.ts

  utils/
    date/
      month.ts
```

---

## 11. TypeScript 类型定义

`IfirOdmCardData`

```ts
export type IfirTrendPoint = {
  month: string;   // YYYY-MM
  ifir: number;
};

export type TopModelRow = {
  rank: number;
  model: string;
  ifir: number;
  box_claim?: number;
  box_mm?: number;
};

export type IfirOdmCardData = {
  odm: string;
  trend: IfirTrendPoint[];
  top_models: TopModelRow[];
  ai_summary: string;
};
```

---

## 12. 验收标准

1. 页面加载后自动拉 options，并默认时间范围为最近 6 个月
2. ODM 未选择时 Analyze 不可点击
3. 选择多个 ODM 后 Analyze 成功返回 cards，结果区出现 carousel
4. 每个 odm 对应一张卡片，卡片内按 A B C 结构展示
5. 左右拖动切换 odm 卡片，底部 selector 高亮同步
6. 点击 selector 可跳转到对应 odm 卡片
7. Analyze 成功后筛选区进入只读变灰展示，确保结果与筛选一致性
8. 某个 odm 无数据时，该卡片展示空态，不影响其他 odm 卡片
9. 不在前端硬编码 IFIR 计算口径，前端仅渲染后端返回的 ifir 值


