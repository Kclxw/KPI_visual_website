# 领域定义

## metric_definitions.json
指标和维度的标准定义字典。

### 结构说明

```json
{
  "version": "1.0.0",
  "updated_at": "2024-01-20",
  "metrics": [
    {
      "code": "唯一编码",
      "name": "中文名称",
      "name_en": "英文名称",
      "unit": "单位",
      "category": "分类",
      "data_type": "数据类型",
      "formula": "计算公式（可选）",
      "description": "说明"
    }
  ],
  "dimensions": [
    {
      "code": "维度编码",
      "name": "维度名称",
      "type": "数据类型",
      "values": ["枚举值列表（可选）"],
      "hierarchical": false
    }
  ],
  "time_types": ["day", "week", "month", "quarter", "year"]
}
```

### 用途

1. **前端展示**：指标名称、单位显示
2. **参数校验**：验证指标和维度是否合法
3. **多语言支持**：根据语言选择对应字段
4. **文档生成**：自动生成数据字典

## thresholds.json
默认阈值配置。

### 结构说明

```json
{
  "version": "1.0.0",
  "thresholds": [
    {
      "metric_code": "指标编码",
      "threshold_type": "upper 或 lower",
      "threshold_value": 数值,
      "comparison_type": "absolute 或 percentage",
      "severity": "low/medium/high/critical",
      "description": "说明"
    }
  ]
}
```

### 用途

1. **系统初始化**：默认阈值配置
2. **批量导入**：阈值配置的导入模板
3. **配置重置**：恢复默认设置

## 维护流程

1. 修改 JSON 文件
2. 运行校验脚本
3. 提交代码审查
4. 通知前后端团队
5. 更新文档说明

## 注意事项

1. 修改前备份原文件
2. 保持向后兼容
3. 新增字段提供默认值
4. 删除字段需评估影响
5. 定期审查和清理
