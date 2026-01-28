# API 文档

本目录包含 KPI 可视化系统的 API 接口契约文档。

## 文档结构

- `api-contract.md` - 完整的 API 契约定义
- `error-codes.md` - 错误码定义

## 快速链接

### 公共接口
- `GET /api/health` - 健康检查

### 上传接口
- `POST /api/upload/excel` - Excel文件上传
- `GET /api/upload/status/{task_id}` - 上传任务状态

### IFIR 接口
- `GET /api/ifir/options` - 获取筛选选项
- `POST /api/ifir/odm-analysis/analyze` - ODM分析
- `POST /api/ifir/segment-analysis/analyze` - Segment分析
- `POST /api/ifir/model-analysis/analyze` - Model分析

### RA 接口
- `GET /api/ra/options` - 获取筛选选项
- `POST /api/ra/odm-analysis/analyze` - ODM分析
- `POST /api/ra/segment-analysis/analyze` - Segment分析
- `POST /api/ra/model-analysis/analyze` - Model分析

## 版本

- **当前版本**: v1.0
- **基础路径**: `/api`
