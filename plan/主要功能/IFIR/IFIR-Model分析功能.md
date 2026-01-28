
## 0. 你这次新增需求，我的理解

### 0.1 Months 默认值

* 原本“趋势月数”默认 20
* 现在改为：**默认 6 个月**
* 仍允许用户切换到更长窗口（例如 12 / 18 / 24），但默认起步是 6

### 0.2 多 Model 的结果展示方式：横向滑动 Carousel

当用户多选了多个 Model 时：

* 结果展示区不是把多条线叠在一个图里，也不是在表里按 Model 分组
* 而是把 **Block A + Block B + Block C 合成一个“大的结果块”**，作为一个“Model 分析卡片”
* 每一个 Model 对应一张卡片
* 用户通过 **左右拖动（横向滑动）** 在不同 Model 卡片之间切换

  * 滑到下一张卡片就是下一个 Model 的 A/B/C 结果
* 底部有一个 **Mode/Model 的选择条（多项）**，用于：

  * 显示当前多选了哪些 Model
  * 支持点击快速跳转到某个 Model 卡片
  * 支持左右滚动（如果 Model 过多）

> 也就是：结果区以“每个 Model 一套 A+B+C”输出，交互上像手机相册那样横向滑动切换。

---

## 1. 模块定位

**模块名称**：IFIR Abnormal Model Analysis
**目标**：在指定时间范围内，按 Segment / ODM / Model 三层筛选，对命中的每个 Model 输出：

* Block A：6 个月 IFIR 趋势图
* Block B：Top Issue 表格（默认 Top1，可扩展）
* Block C：AI 总结
  并以“横向滑动卡片”方式浏览多个 Model 的结果。

---

## 2. 用户使用流程

1）进入页面
2）选择时间范围
3）选择 Segment（可选）/ ODM（可选）/ Model（必选，多选）
4）点击 Analyze
5）系统生成结果卡片集合（每个 Model 一张）
6）用户：

* 默认停在第一个 Model 卡片
* 左右滑动切换 Model
* 或点击底部 Model 选择条快速切换

---

## 3. 页面布局与交互设计

### 3.1 筛选区 Filter Panel

**控件 1：时间范围 Time Range**

* 类型：Month range picker
* 默认：结束月取数据最新月；开始月 = 结束月往前推 5 个月（共 6 个月）

**控件 2：Trend Months（趋势窗口长度）**

* 类型：下拉单选
* 默认：**6**
* 可选：6 / 12 / 18 / 24（或你们常用档位）
* 行为：

  * 用户改 months 后，重新计算 trend，但时间范围仍受 Time Range 限制
  * 推荐做法：Time Range 作为外层过滤，Trend Months 作为展示窗口（从 end_month 往前截取 N 个月）

**控件 3：Segment**

* 类型：Multi select
* 默认：All

**控件 4：ODM**

* 类型：Multi select
* 默认：All

**控件 5：Model**

* 类型：Multi select（必选）
* 默认：空
* 选项来源：数据库 distinct model
* 级联建议：先选 Segment/ODM 后缩小 Model 列表

**按钮：Analyze**

* 校验：未选 Model 禁止分析并提示
* 点击后：

  * loading
  * 请求后端生成结果卡片数据

---

### 3.2 结果区 Result Area（核心改动：Model 卡片 Carousel）

#### 3.2.1 结果区整体结构

结果区由两部分组成：

**Part 1：Model Result Carousel（大块）**

* 一个横向滑动容器
* 内部是一组 “Model Result Card”
* 每张卡片 = Block A + Block B + Block C 的组合

**Part 2：底部 Model Selector（选择条）**

* 横向滚动的标签条（chip/tabs）
* 展示选中的 Model 列表
* 当前卡片对应的 Model 标签高亮
* 点击标签：跳转到对应卡片
* 滑动卡片：同步更新高亮标签

#### 3.2.2 Model Result Card 的内部结构（每个 Model 一套）

**Card Header**

* Model 名称（必显）
* 当前筛选条件摘要（Segment/ODM/Time Range）
* Data as of（月）

**Block A：IFIR Trend（默认 6 个月）**

* 折线图：x=month，y=ifir
* 标注：

  * 最新月 IFIR
  * 环比变化（如果有至少 2 个点）
  * 最近 3 点趋势（可选）

**Block B：Top Issue Table**

* 默认 Top1（可扩展 TopN）
* 以表格展示：

  * Rank
  * Issue
  * IFIR contribution（或占比）
  * Case count（可选）
  * First seen / Last seen（可选）

**Block C：AI Summary**

* 文本卡片
* 内容结构固定：
  1）趋势一句话结论（上升/下降/波动）
  2）Top issue 解释（是否持续、是否集中某几个月）
  3）分析建议方向（不落具体动作）

---

## 4. 数据需求与计算逻辑

### 4.1 必要字段

* month（YYYY-MM）
* model
* odm
* segment
* ifir_value（或分子分母）
* issue

### 4.2 过滤逻辑

* month ∈ [start_month, end_month]
* segment ∈ selected_segments（如果不是 All）
* odm ∈ selected_odms（如果不是 All）
* model ∈ selected_models（必选）

### 4.3 趋势窗口截取（默认 6）

* 先按 Time Range 过滤
* 再按 Trend Months 从 end_month 往前截取 N 个月用于图表
* 如果 Time Range 小于 N：用 Time Range 实际可用月份

### 4.4 Top issue 逻辑

在同一 model + 时间过滤条件下：

* group by issue
* 按贡献度或数量排序
* 取 top1（或 topN）

---

## 5. 后端接口设计（支持卡片模式）

### 5.1 Options API

**GET** `/api/ifir/options`

* 返回 segments / odms / models / max_month / min_month

支持参数（可选）：

* segments
* odms
  用于联动过滤 models

### 5.2 Analyze API（返回卡片列表）

**POST** `/api/ifir/abnormal-model/analyze`

Request

```json
{
  "time_range": { "start_month": "2025-06", "end_month": "2025-11" },
  "filters": {
    "segments": ["SEG_A"],
    "odms": ["ODM1"],
    "models": ["MODEL_X", "MODEL_Y", "MODEL_Z"]
  },
  "view": {
    "trend_months": 6,
    "top_issue_n": 1
  }
}
```

Response（关键：按 model 返回 cards）

```json
{
  "meta": { "data_as_of": "2025-11" },
  "cards": [
    {
      "model": "MODEL_X",
      "trend": [
        { "month": "2025-06", "ifir": 0.12 },
        { "month": "2025-07", "ifir": 0.10 }
      ],
      "top_issues": [
        { "rank": 1, "issue": "ISSUE_ABC", "ifir_contribution": 0.05, "share": 0.32 }
      ],
      "ai_summary": "..."
    },
    {
      "model": "MODEL_Y",
      "trend": [],
      "top_issues": [],
      "ai_summary": "..."
    }
  ]
}
```

说明：

* 前端 carousel 直接按 cards 渲染
* `ai_summary` 可以后端生成，也可以后端返回结构化 summary_input 让前端调用 LLM

---

## 6. 交互细节与边界

### 6.1 Model 数量多时的体验

* Carousel 支持 swipe
* 底部 selector 支持横向滚动
* 超过阈值（例如 >20）时：

  * 可提示用户缩小选择范围（不强制）

### 6.2 无数据状态

某个 Model 在筛选条件下无数据：

* Card 仍存在，但 Block A/B 显示 empty state
* AI Summary 输出：该时间范围内无有效数据，建议调整筛选条件

### 6.3 性能建议（便于落地）

* Analyze API 支持分页或按需加载（可选）

  * 初次只返回前 5 个 model cards，滑动到后面再请求
  * 或一次性返回全部（取决于数据量）

---

## 7. 交付给“代码模型”的关键点

你要让另一个大模型写代码，这版设计里需要它重点实现：
1）筛选区：Time Range + Trend Months 默认 6 + Segment/ODM/Model 多选
2）Analyze 调用：POST 返回 cards 数组
3）结果区：Carousel（cards 横向滑动）
4）底部 Model Selector：点击跳卡片，滑动同步高亮
5）每张卡片内：A 图 + B 表 + C 文本三块按固定结构渲染

---

下面是一份更像工程任务书的版本，覆盖前端 Vue 拆解，路由，状态管理，交互事件，接口对接，方便直接交给代码生成模型或工程同学落地。

---

# IFIR Abnormal Model Analysis 前端工程任务书

## 1. 页面与路由

### 1.1 路由定义

* 路由路径：`/kpi/ifir/abnormal-model`
* 路由名称：`IfirAbnormalModel`
* 页面标题：`IFIR Abnormal Model Analysis`

### 1.2 权限与入口

* 若有权限系统：该路由挂在 KPI 模块下，按角色控制可见
* 无权限系统：默认可访问

---

## 2. 页面布局结构

页面分为两大区域：

1. Filter Panel（筛选区）
2. Result Area（结果区，Carousel 卡片区 + 底部 Model Selector）

推荐布局：

* 顶部固定筛选区
* 下方结果区自适应高度
* 结果区内部：上面 Carousel，下面 Selector

---

## 3. 组件拆解

### 3.1 页面容器

**组件：`IfirAbnormalModelPage.vue`**
职责：

* 组合筛选区与结果区
* 触发初始化加载 options
* 监听 Analyze 事件并驱动数据流

子组件：

* `IfirFilterPanel.vue`
* `IfirResultCarousel.vue`
* `IfirModelSelector.vue`
* `IfirEmptyState.vue`（可选）
* `IfirErrorToast.vue`（可选，或用全局 toast）

### 3.2 筛选区

**组件：`IfirFilterPanel.vue`**
控件清单：

* MonthRangePicker：startMonth, endMonth
* TrendMonthsSelect：默认 6，选项 6 12 18 24
* SegmentMultiSelect：默认 All
* OdmMultiSelect：默认 All
* ModelMultiSelect：必选，多选，默认空
* AnalyzeButton

输入 props：

* options: { segments, odms, models, monthRange }
* loadingOptions: boolean
* analyzing: boolean

输出 events：

* `changeFilters(filtersDraft)`
* `submitAnalyze(filtersFinal)`

交互要求：

* 时间范围变化后，自动校验 start end
* Segment 或 ODM 变化后，触发 Model 候选项刷新（级联）
* 未选 Model 时禁用 Analyze，并给出提示文案

### 3.3 结果区 Carousel

**组件：`IfirResultCarousel.vue`**
职责：

* 横向滑动展示 cards
* 暴露当前 index
* 支持外部跳转到指定 index
* 同步滑动事件给 selector

输入 props：

* cards: IfirModelCard[]
* activeIndex: number
* analyzing: boolean

输出 events：

* `indexChange(newIndex)`
* `reachEnd()`（可选，用于懒加载）

内部子组件：

* `IfirModelCard.vue`

### 3.4 单张 Model 卡片

**组件：`IfirModelCard.vue`**
结构：

* CardHeader：model 名，筛选摘要，dataAsOf
* BlockA TrendChart：6 个月趋势折线
* BlockB TopIssueTable：Top1 或 TopN
* BlockC AiSummary：文本卡片

输入 props：

* card: IfirModelCard
* view: { trendMonths, topIssueN }

空态规则：

* trend 为空：显示 empty trend
* topIssues 为空：显示 empty table
* aiSummary 为空：显示 placeholder 或 fallback 文案

### 3.5 底部 Model Selector

**组件：`IfirModelSelector.vue`**
形态：

* 横向滚动 chips 或 tabs
* 当前激活项高亮
* 点击跳转

输入 props：

* models: string[]（来自 cards 或用户选择）
* activeIndex: number

输出 events：

* `selectIndex(newIndex)`

规则：

* 当 cards 数量与 models 不一致时，以 cards 为准渲染，避免跳空
* 当 activeIndex 超出范围，自动回到 0

---

## 4. 状态管理设计（Pinia 推荐）

### 4.1 Store 结构

**store 名称：`useIfirAbnormalModelStore`**

state

* options

  * segments: string[]
  * odms: string[]
  * models: string[]
  * monthMin: string
  * monthMax: string
* filtersDraft

  * startMonth: string
  * endMonth: string
  * trendMonths: number (default 6)
  * segments: string[] | null (null 表示 All)
  * odms: string[] | null
  * models: string[] (必选)
* analyzing

  * loadingOptions: boolean
  * analyzing: boolean
  * error: string | null
* result

  * dataAsOf: string
  * cards: IfirModelCard[]
  * activeIndex: number
  * lastRequest: object | null

getters

* isAnalyzeEnabled: boolean（models 非空且时间合法）
* activeCard: IfirModelCard | null
* selectorModels: string[]（从 cards 映射 model）

actions

* initOptions()
* refreshModelsByCascade()（当 segments 或 odms 变化）
* setFiltersDraft(partial)
* analyze()
* setActiveIndex(index)
* jumpToModel(modelName)（可选，内部做 index 查找）

### 4.2 默认值规则

* trendMonths 默认 6
* timeRange 默认 recent 6 months

  * endMonth = options.monthMax
  * startMonth = endMonth 往前推 5 个月
* segments odms 默认 All（用 null 表示 All，避免传空数组歧义）
* models 默认空

---

## 5. API 对接任务

### 5.1 Options API

请求：

* GET `/api/ifir/options`
* 可选参数：segments, odms（用于级联刷新 models）

响应：

* segments, odms, models, monthMin, monthMax, dataAsOf

前端任务：

* 页面加载时调用一次 initOptions
* 当 segments 或 odms 变化时调用 refreshModelsByCascade 更新 models 候选项
* 若更新后 filtersDraft.models 中有值不在候选项里，自动剔除，并提示用户

### 5.2 Analyze API

请求：

* POST `/api/ifir/abnormal-model/analyze`

请求体：

* time_range: startMonth, endMonth
* filters: segments, odms, models
* view: trendMonths (default 6), topIssueN (default 1)

响应：

* meta: dataAsOf
* cards: IfirModelCard[]

前端任务：

* 成功后：

  * store.result.cards 更新
  * store.result.activeIndex 设为 0
* 失败后：

  * toast 错误
  * result 保留上一次或清空，按产品策略决定

---

## 6. 交互事件与联动细节

### 6.1 筛选区事件

* 时间范围变更

  * 更新 filtersDraft
  * 若 start end 非法，禁用 Analyze
* Segment 或 ODM 变更

  * 更新 filtersDraft
  * 调用 refreshModelsByCascade
  * 处理 models 剔除逻辑
* Model 变更

  * 更新 filtersDraft.models
* 点击 Analyze

  * 调用 analyze
  * analyzing 状态为 true
  * 成功后滚动到结果区顶部（可选）

### 6.2 Carousel 与 Selector 同步

* 用户滑动 Carousel

  * 触发 `indexChange`
  * store.setActiveIndex(newIndex)
  * Selector 高亮同步变化
* 用户点击 Selector 某个 model

  * 触发 `selectIndex`
  * store.setActiveIndex(newIndex)
  * Carousel 调用 `scrollToIndex(newIndex)`

实现建议（工程可落地的方式）：

* Carousel 使用以下任一方案

  * 原生 scroll snap + 监听 scroll 计算 index
  * 现成轮播库（例如 swiper），直接用其 activeIndex 事件
* Selector 与 Carousel 通过 activeIndex 单一数据源绑定（store 里维护）

### 6.3 懒加载可选项

当 models 很多，cards 很多时，可做升级：

* Analyze 第一次只取前 N 个 cards
* Carousel 滑到末尾触发 reachEnd 再拉下一页
  如果你们后端短期不做分页，前端先不实现

---

## 7. 类型定义（前端 TypeScript）

### 7.1 IfirModelCard

字段建议：

* model: string
* filterSummary: { segments, odms, startMonth, endMonth }
* dataAsOf: string
* trend: Array<{ month: string; ifir: number }>
* topIssues: Array<{ rank: number; issue: string; ifirContribution?: number; share?: number; caseCount?: number; firstSeen?: string; lastSeen?: string }>
* aiSummary: string

---

## 8. 验收标准（可直接当 Definition of Done）

1. 页面可通过路由访问，加载 options 成功后可正常展示筛选控件
2. trendMonths 默认 6，timeRange 默认最近 6 个月
3. Model 未选择时 Analyze 按钮不可用且提示明确
4. 多选 Model 后点击 Analyze，返回 cards 后出现 Carousel
5. Carousel 每一张卡片包含 BlockA BlockB BlockC
6. 左右滑动卡片时 Selector 高亮同步变化
7. 点击 Selector 任意 model 可跳转到对应卡片
8. 某个 model 无数据时，该卡片展示空态且不影响其他卡片浏览
9. Analyze 过程中有 loading 状态，避免重复提交
10. 接口失败时有错误提示，不出现页面卡死

