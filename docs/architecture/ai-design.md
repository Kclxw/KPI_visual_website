# AI 子系统设计

## 1. 设计目标

AI 模块的核心目标是**生成可信、可追溯、有价值的业务洞察**，而非简单的数据总结。

### 关键原则
- **证据驱动**：所有结论必须基于真实数据
- **防幻觉**：结构化校验，禁止编造数据
- **可追溯**：结果可回溯到具体数据点
- **可审计**：Prompt、证据、结果全程记录

---

## 2. 整体架构

```
用户触发 → Orchestrator → Evidence Builder → AI Provider → Guardrails → 结构化结果 → 落库
```

### 核心组件

| 组件 | 职责 |
|------|------|
| **Orchestrator** | 任务编排：接收任务 → 构建证据 → 调用模型 → 校验 → 存储 |
| **Evidence Builder** | 证据包构建：TopN明细、贡献度、环比同比、阈值告警 |
| **AI Provider** | 模型适配层：统一接口，支持 OpenAI/本地模型 |
| **Guardrails** | 防护层：结构校验、引用校验、敏感词过滤 |
| **Prompt Templates** | Prompt 版本化管理，支持回滚 |

---

## 3. 证据包设计

AI 不直接访问数据库，而是由后端提前构建**证据包**（Evidence Package）。

### 证据包内容

```json
{
  "time_range": "2024-W01",
  "metric": "销售额",
  "dimensions": ["区域", "产品线"],
  "top_abnormal": [
    {"region": "华东", "value": 1200, "threshold": 1000, "deviation": "+20%"}
  ],
  "contribution": [
    {"region": "华东", "contribution": 0.45},
    {"region": "华北", "contribution": 0.30}
  ],
  "trend": {
    "current": 5000,
    "last_period": 4500,
    "yoy": "+11.1%"
  },
  "context": {
    "business_rules": ["促销活动", "季节性因素"],
    "related_metrics": ["订单量", "客单价"]
  }
}
```

### 构建逻辑

1. **TopN 异常**：按阈值偏差排序，取前 10
2. **贡献度**：计算各维度对总量的贡献占比
3. **趋势对比**：环比、同比、多周期对比
4. **关联指标**：拉取相关指标的变化趋势

---

## 4. Prompt 设计

### Prompt 模板示例

```markdown
# 角色
你是一位资深的 KPI 分析师，擅长从数据中发现业务问题。

# 任务
基于以下证据包，生成一份简洁的业务洞察报告。

# 证据包
{evidence_json}

# 输出要求
1. 必须基于证据包中的数据，不得编造
2. 每个结论必须标注数据来源（使用 [证据ID] 格式）
3. 输出 JSON 格式：
{
  "summary": "一句话总结",
  "insights": [
    {"finding": "发现内容", "evidence_id": "top_abnormal[0]", "severity": "high"}
  ],
  "recommendations": ["建议1", "建议2"]
}
```

### Prompt 版本管理

- 文件路径：`backend/app/ai/prompts/insight_v1.md`
- 版本号：在文件名中体现（v1, v2...）
- 变更记录：Git commit 记录 + changelog

---

## 5. 防幻觉机制（Guardrails）

### 5.1 输入校验

- **证据完整性**：必须包含 TopN、趋势、贡献度
- **数据范围检查**：时间范围、维度合法性
- **大小限制**：证据包不超过 10KB（防止超 token）

### 5.2 输出校验

```python
# 伪代码
def validate_ai_result(result, evidence):
    # 1. 结构校验
    assert "summary" in result
    assert "insights" in result
    
    # 2. 引用校验
    for insight in result["insights"]:
        evidence_id = insight["evidence_id"]
        assert evidence_id in evidence  # 必须引用真实证据
    
    # 3. 数值范围校验
    for insight in result["insights"]:
        if "value" in insight:
            assert value_in_evidence_range(insight["value"], evidence)
    
    # 4. 敏感词过滤
    assert not contains_sensitive_words(result["summary"])
```

### 5.3 人工复核

- **高风险场景**：触发 severity=critical 的洞察需人工复核
- **随机抽查**：10% 的 AI 结果进入人工审核队列
- **反馈闭环**：人工标注错误案例，用于优化 Prompt

---

## 6. 模型适配层

支持多种 AI Provider，便于切换和对比。

### 统一接口

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_insight(self, prompt: str, evidence: dict) -> dict:
        pass
```

### 实现类

- **OpenAIProvider**：调用 OpenAI API
- **LocalProvider**：调用本地部署模型（Ollama、LLaMA）
- **MockProvider**：测试用，返回固定结果

### 配置切换

```env
AI_PROVIDER=openai  # 环境变量控制
```

---

## 7. 任务流程

### 7.1 用户触发

```
POST /api/v1/ai/tasks
{
  "type": "insight",
  "metric": "销售额",
  "time_range": "2024-W01",
  "dimensions": ["区域"]
}
```

返回：`task_id`

### 7.2 后台执行

1. **入队**：任务写入 Celery 队列
2. **构建证据**：EvidenceBuilder 查询 DB，生成证据包
3. **调用模型**：AIProvider 发送 Prompt + 证据
4. **校验结果**：Guardrails 校验结构和引用
5. **落库**：结果写入 `ai_result` 表

### 7.3 结果查询

```
GET /api/v1/ai/tasks/{task_id}
{
  "status": "completed",
  "result": {
    "summary": "...",
    "insights": [...]
  }
}
```

---

## 8. 数据库设计

### ai_result 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | bigint | 主键 |
| task_id | varchar | 任务ID |
| prompt_version | varchar | Prompt 版本 |
| evidence | json | 证据包（可回溯） |
| raw_output | text | 模型原始输出 |
| parsed_result | json | 结构化结果 |
| status | enum | pending/completed/failed |
| created_at | timestamp | 创建时间 |

---

## 9. 监控与优化

### 关键指标

- **成功率**：AI 任务完成率（目标 >95%）
- **校验通过率**：Guardrails 通过率（目标 >90%）
- **响应时间**：P95 < 10s
- **成本**：Token 消耗 / 单次分析

### 优化方向

1. **Prompt 工程**：A/B 测试不同 Prompt
2. **证据精简**：只传最相关的数据
3. **缓存策略**：相似任务复用结果
4. **模型选择**：对比 GPT-4 vs GPT-3.5 性价比

---

## 10. 安全与合规

- **数据脱敏**：证据包中不包含用户隐私字段
- **访问控制**：AI 结果继承原数据权限
- **审计日志**：所有 AI 调用记录到 audit_log
- **模型隔离**：生产/测试环境使用不同 API Key
