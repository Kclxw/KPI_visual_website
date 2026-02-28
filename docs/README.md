# 文档中心

本目录包含 KPI 可视化分析平台的所有技术文档。

## 目录结构

- **architecture/** - 系统架构设计文档
- **api/** - API 接口契约与规范
- **db/** - 数据库设计与迁移文档
- **runbook/** - 运维与开发手册
  - startup.md - 项目启动指南（本地）

## 文档维护原则

1. **及时更新**：代码变更时同步更新文档
2. **结构清晰**：使用统一的文档模板
3. **易于检索**：使用清晰的标题和目录
4. **版本控制**：重大变更记录版本号和日期

## 阅读建议

### 新人入职
1. 先读 `architecture/overview.md` 了解系统全貌
2. 再读 `runbook/local-dev.md` 搭建开发环境
3. 查阅 `api/api-contract.md` 了解接口规范

### 日常开发
- 开发接口时参考 `api/api-contract.md`
- 数据库变更参考 `db/schema.md`
- 遇到问题查阅 `runbook/troubleshooting.md`

### 部署运维
- 部署时参考 `runbook/deploy.md`
- 问题排查参考 `runbook/troubleshooting.md`
