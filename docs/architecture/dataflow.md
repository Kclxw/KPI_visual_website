# 数据流转设计

本文档详细描述 KPI 可视化分析平台的核心数据流转链路。

## 1. 看板查询流程

### 1.1 流程图

```
用户打开看板
    ↓
前端发起请求：GET /api/v1/kpi?date_range=...&filters=...
    ↓
后端 API 层：参数校验 + 权限检查
    ↓
后端 Service 层：判断使用聚合表还是明细表
    ↓
后端 Repository 层：构造 SQL 查询
    ↓
MySQL：执行查询（聚合表命中索引，速度快）
    ↓
后端 Service 层：计算同比/环比/达成率
    ↓
后端 API 层：封装响应（统一格式）
    ↓
前端：渲染卡片 + 趋势图
```

### 1.2 关键设计

**聚合表优化**：
- 明细表（`kpi_detail`）：百万级数据，查询慢
- 聚合表（`kpi_agg`）：按天/周/月预聚合，查询快
- Service 层根据查询粒度自动选择表

**缓存策略**：
- 当日数据不缓存（实时变化）
- 历史数据缓存 1 小时（Redis）
- 聚合数据缓存 24 小时

### 1.3 SQL 示例

```sql
-- 查询区域销售额（使用聚合表）
SELECT 
    region,
    SUM(sales_amount) as total_sales,
    AVG(sales_amount) as avg_sales
FROM kpi_agg
WHERE 
    date >= '2026-01-01' 
    AND date <= '2026-01-20'
    AND metric_code = 'sales_amount'
GROUP BY region;
```

## 2. 下钻分析流程

### 2.1 流程图

```
用户点击"销售额"卡片（异常：↓15%）
    ↓
前端：携带上下文（指标、时间、维度）发起下钻请求
    ↓
后端：查询明细表，找出 Top 异常项
    ↓
Service 层：计算贡献度（该项占比 × 变化幅度）
    ↓
前端：展示异常列表（门店/SKU/区域排序）
    ↓
用户继续下钻（点击某门店）
    ↓
后端：按新维度再次查询（门店 → SKU 或品类）
    ↓
前端：展示二级下钻结果
```

### 2.2 关键算法

**贡献度计算**：

```
贡献度 = (当期占比 - 上期占比) × 100

例：
- 门店 A 当期占比 30%，上期占比 40%
- 贡献度 = (30% - 40%) × 100 = -10%
- 解读：门店 A 导致总体下降 10 个百分点
```

**异常判定**：

```
异常 = abs(变化率) > 阈值 AND abs(贡献度) > 3%

优先级 = abs(贡献度) （排序依据）
```

### 2.3 接口示例

```http
POST /api/v1/drilldown/analyze
Content-Type: application/json

{
  "metric_code": "sales_amount",
  "date_range": {
    "current_start": "2026-01-13",
    "current_end": "2026-01-19",
    "compare_start": "2026-01-06",
    "compare_end": "2026-01-12"
  },
  "dimensions": ["region", "store"],
  "filters": {
    "region": "华东"
  }
}
```

响应：

```json
{
  "code": 0,
  "data": {
    "total_change_rate": -15.2,
    "abnormal_items": [
      {
        "dimension": "store",
        "dimension_value": "杭州店",
        "current_value": 850000,
        "compare_value": 1200000,
        "change_rate": -29.2,
        "contribution": -8.5,
        "rank": 1
      }
    ]
  }
}
```

## 3. AI 分析流程

### 3.1 流程图

```
用户点击"AI 分析"
    ↓
前端：发起异步任务请求
    ↓
后端 API：创建任务记录 → 返回 task_id
    ↓
后端：任务入队（Celery）
    ↓
Worker：取任务开始执行
    ↓
① 证据构建器（evidence_builder）：查询数据库，生成证据包
    ↓
② AI 编排器（orchestrator）：调用大模型
    ↓
③ 防护栏（guardrails）：校验输出结构 + 证据引用
    ↓
④ 结果落库（ai_result 表）
    ↓
⑤ 更新任务状态为"已完成"
    ↓
前端：轮询任务状态 → 获取结果 → 展示洞察面板
```

### 3.2 证据包结构

```json
{
  "metric": {
    "code": "sales_amount",
    "name": "销售额",
    "current_value": 5200000,
    "compare_value": 6100000,
    "change_rate": -14.8
  },
  "top_contributors": [
    {
      "dimension": "store",
      "value": "杭州店",
      "contribution": -8.5,
      "change_rate": -29.2
    }
  ],
  "trend": [
    {"date": "2026-01-13", "value": 750000},
    {"date": "2026-01-14", "value": 820000}
  ],
  "context": {
    "season": "淡季",
    "events": ["春节前夕"]
  }
}
```

### 3.3 Prompt 模板（简化版）

```markdown
# 任务
你是一名数据分析师，基于以下证据包，生成业务洞察报告。

# 证据包
{{ evidence_json }}

# 要求
1. 必须引用证据包中的具体数字
2. 分析变化原因（从数据推导，不要臆测）
3. 提出可执行的改进建议
4. 输出 JSON 格式：
{
  "summary": "一句话总结",
  "root_cause": ["原因1", "原因2"],
  "suggestions": ["建议1", "建议2"],
  "evidence_refs": ["证据包中的字段路径"]
}
```

### 3.4 防护栏校验

```python
# guardrails.py 伪代码
def validate_ai_result(result, evidence):
    # 1. 结构校验
    assert "summary" in result
    assert "root_cause" in result
    
    # 2. 证据引用校验
    for ref in result.get("evidence_refs", []):
        assert ref_exists_in_evidence(ref, evidence)
    
    # 3. 数字一致性校验
    extracted_numbers = extract_numbers(result["summary"])
    for num in extracted_numbers:
        assert num in evidence_numbers(evidence)
    
    return True
```

## 4. 报表导出流程

### 4.1 流程图

```
用户选择时间范围 + 点击"导出周报"
    ↓
前端：发起导出任务请求
    ↓
后端 API：创建任务 → 返回 task_id
    ↓
Worker：取任务执行
    ↓
① 查询数据（KPI 汇总 + AI 洞察 + 图表数据）
    ↓
② 加载模板（weekly_report.pptx）
    ↓
③ 填充数据（python-pptx 库）
    ↓
④ 生成文件 → 保存到文件系统
    ↓
⑤ 更新任务状态 + 文件路径
    ↓
前端：轮询成功 → 调用下载接口
    ↓
后端：返回文件流（Content-Disposition: attachment）
```

### 4.2 模板设计

**PPT 模板占位符**：

```
Slide 1: 封面
- {{report_title}}
- {{date_range}}

Slide 2: 核心指标
- {{sales_amount}} (销售额)
- {{sales_growth}} (增长率)

Slide 3: AI 洞察
- {{ai_summary}}
- {{ai_suggestions}}

Slide 4: 趋势图
- {{chart_image}} (预生成的 ECharts 图片)
```

### 4.3 接口示例

```http
POST /api/v1/export/report
{
  "report_type": "weekly",
  "format": "pptx",
  "date_range": {
    "start": "2026-01-13",
    "end": "2026-01-19"
  },
  "sections": ["kpi_summary", "ai_insight", "trend_chart"]
}

响应：
{
  "code": 0,
  "data": {
    "task_id": "abc123",
    "status": "pending"
  }
}
```

查询任务：

```http
GET /api/v1/export/task/abc123

响应：
{
  "code": 0,
  "data": {
    "task_id": "abc123",
    "status": "completed",
    "download_url": "/api/v1/export/download/abc123",
    "file_name": "周报_2026W03.pptx"
  }
}
```

## 5. 数据导入流程

### 5.1 流程图

```
用户上传 CSV 文件
    ↓
前端：文件上传（multipart/form-data）
    ↓
后端：保存文件 → 返回文件 ID
    ↓
用户点击"开始导入"
    ↓
后端：创建导入任务
    ↓
Worker：读取 CSV → 校验 → 批量插入
    ↓
更新任务状态（成功/失败/部分成功）
    ↓
前端：展示导入结果（成功X条，失败Y条）
```

### 5.2 校验规则

- 必填字段检查（门店、SKU、日期、金额）
- 数据类型检查（日期格式、数字范围）
- 业务规则检查（金额不能为负、日期不能未来）
- 重复数据检查（门店+SKU+日期唯一）

## 6. 性能优化策略

### 6.1 查询优化

- 聚合表预计算（减少实时计算）
- 索引优化（date + metric_code + dimensions）
- 分页查询（避免大结果集）
- 查询超时设置（3 秒超时）

### 6.2 缓存策略

- Redis 缓存热点数据（历史数据、配置）
- 缓存 Key 设计：`kpi:{metric}:{date_range}:{filters_hash}`
- 缓存失效：数据更新时主动清除

### 6.3 异步优化

- 耗时操作全部异步化（AI、导出、聚合）
- 任务优先级队列（紧急任务优先）
- 并发控制（AI 任务限制并发数）

## 7. 数据一致性保证

### 7.1 事务控制

- 导入数据时使用事务（全部成功或全部回滚）
- 聚合计算时加行锁（避免并发重复计算）

### 7.2 幂等性设计

- 任务 ID 唯一（重复提交不会重复执行）
- 导入记录去重（根据业务主键判断）

### 7.3 审计追踪

- 所有写操作记录 audit_log（谁、何时、做了什么）
- AI 结果保留原始证据包（可追溯）

---

**更新记录**
- 2026-01-20：初始版本
