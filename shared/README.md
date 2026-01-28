# 共享资源

前后端共享的契约、配置和定义文件。

## 目录结构

```
shared/
├── api_contract/              # API 契约
│   ├── openapi.yaml          # OpenAPI 规范
│   └── error_codes.md        # 错误码说明
└── domain/                    # 领域定义
    ├── metric_definitions.json
    └── thresholds.json
```

## API 契约

### openapi.yaml
由后端 FastAPI 自动生成的 OpenAPI 规范文档。

**生成方式**：
```bash
# 访问 /openapi.json 端点
curl http://localhost:8000/openapi.json > shared/api_contract/openapi.yaml
```

**用途**：
- 前端 API 客户端生成
- API 文档生成
- 接口测试用例生成
- 第三方集成参考

### error_codes.md
统一的错误码定义（与 docs/api/error-codes.md 同步）。

## 领域定义

### metric_definitions.json
指标和维度的标准定义，确保前后端使用相同的字段名和枚举值。

```json
{
  "metrics": [
    {
      "code": "sales_amount",
      "name": "销售额",
      "name_en": "Sales Amount",
      "unit": "元",
      "category": "销售",
      "data_type": "decimal"
    }
  ],
  "dimensions": [
    {
      "code": "region",
      "name": "区域",
      "name_en": "Region",
      "type": "string",
      "values": ["华东", "华北", "华南", "西南"]
    }
  ]
}
```

### thresholds.json
默认阈值配置，用于初始化或重置。

```json
{
  "thresholds": [
    {
      "metric_code": "sales_amount",
      "threshold_type": "lower",
      "threshold_value": 10000,
      "severity": "high"
    }
  ]
}
```

## 使用方式

### 前端使用

```typescript
import metricDefinitions from '@shared/domain/metric_definitions.json'

// 获取指标定义
const metric = metricDefinitions.metrics.find(m => m.code === 'sales_amount')
```

### 后端使用

```python
import json
from pathlib import Path

# 读取指标定义
with open('shared/domain/metric_definitions.json') as f:
    definitions = json.load(f)
```

## 维护规范

1. **版本管理**：重大变更时更新版本号
2. **向后兼容**：新增字段不影响旧版本
3. **文档同步**：修改后同步更新文档
4. **校验规范**：使用 JSON Schema 校验格式

## 注意事项

1. 共享文件的修改影响前后端，需谨慎
2. 变更前通知相关开发人员
3. 测试环境先验证再同步到生产
4. 保持文件精简，避免冗余数据
