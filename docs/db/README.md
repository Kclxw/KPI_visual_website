# 数据库设计文档

本目录包含数据库相关的设计与迁移文档。

## 文档列表

- **schema.md** - 完整的数据库表结构设计与字段说明
- **migrations-notes.md** - 数据库迁移策略与注意事项

## 数据库设计原则

### 1. 命名规范
- 表名：小写 + 下划线，复数形式（如 `kpi_details`）
- 字段名：小写 + 下划线（如 `created_at`）
- 索引名：`idx_表名_字段名`
- 外键名：`fk_表名_字段名`

### 2. 字段规范
- **主键**：统一使用 `id` BIGINT AUTO_INCREMENT
- **时间戳**：统一使用 `created_at`、`updated_at`
- **软删除**：使用 `deleted_at` TIMESTAMP NULL
- **枚举**：优先使用 VARCHAR，便于扩展

### 3. 索引策略
- 所有外键必须建索引
- 常用查询条件建立联合索引
- 时间范围查询建立索引
- 避免过多索引影响写入性能

### 4. 数据类型选择
- 金额：DECIMAL(18,2)
- 百分比：DECIMAL(5,2)
- 日期：DATE
- 时间戳：TIMESTAMP（带时区）
- 长文本：TEXT
- JSON：JSON（MySQL 5.7+）

## 表分类

### 核心业务表
- `kpi_details` - KPI 明细数据（最细粒度）
- `kpi_agg_daily` - 日聚合表
- `kpi_agg_weekly` - 周聚合表
- `kpi_agg_monthly` - 月聚合表

### 配置表
- `metric_configs` - 指标定义
- `dimension_configs` - 维度定义
- `threshold_configs` - 阈值配置
- `user_configs` - 用户配置

### AI 相关表
- `ai_tasks` - AI 任务记录
- `ai_results` - AI 分析结果
- `ai_feedbacks` - AI 结果反馈

### 报表相关表
- `report_templates` - 报表模板
- `report_tasks` - 报表生成任务
- `report_files` - 报表文件记录

### 系统表
- `users` - 用户表
- `roles` - 角色表
- `permissions` - 权限表
- `audit_logs` - 审计日志

## 迁移管理

### 使用 Alembic
```bash
# 创建迁移
alembic revision --autogenerate -m "描述"

# 执行迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

### 迁移规范
1. 每次迁移必须写明注释
2. 生产环境迁移必须经过审批
3. 迁移脚本必须可回滚
4. 大表变更需要在低峰期执行

## 性能优化建议

1. **分表策略**：明细表按月分表（如 `kpi_details_202401`）
2. **归档策略**：超过 1 年的数据归档到历史库
3. **读写分离**：报表查询走只读库
4. **缓存策略**：配置数据使用 Redis 缓存
