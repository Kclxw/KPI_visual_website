# 错误码定义

> **版本**: v1.0  
> **更新日期**: 2026-01-26

---

## 一、错误码规范

### 1.1 错误码格式

错误码为整数，按模块划分区间：

| 区间 | 模块 |
|------|------|
| 0 | 成功 |
| 1000-1999 | 通用错误 |
| 2000-2999 | 上传模块错误 |
| 3000-3999 | IFIR模块错误 |
| 4000-4999 | RA模块错误 |
| 5000-5999 | AI模块错误 |

### 1.2 错误响应格式

```json
{
  "code": 1001,
  "message": "参数校验失败",
  "data": {
    "errors": [
      { "field": "time_range.start_month", "message": "开始月份不能为空" }
    ]
  }
}
```

---

## 二、通用错误码（1000-1999）

| 错误码 | 错误名称 | 说明 | HTTP状态码 |
|--------|----------|------|------------|
| 1000 | INTERNAL_ERROR | 服务器内部错误 | 500 |
| 1001 | PARAM_INVALID | 参数校验失败 | 400 |
| 1002 | PARAM_MISSING | 缺少必要参数 | 400 |
| 1003 | UNAUTHORIZED | 未授权访问 | 401 |
| 1004 | FORBIDDEN | 无权限访问 | 403 |
| 1005 | NOT_FOUND | 资源不存在 | 404 |
| 1006 | METHOD_NOT_ALLOWED | 请求方法不支持 | 405 |
| 1007 | RATE_LIMIT_EXCEEDED | 请求频率超限 | 429 |
| 1008 | SERVICE_UNAVAILABLE | 服务暂不可用 | 503 |

---

## 三、上传模块错误码（2000-2999）

| 错误码 | 错误名称 | 说明 | HTTP状态码 |
|--------|----------|------|------------|
| 2001 | FILE_EMPTY | 上传文件为空 | 400 |
| 2002 | FILE_TYPE_INVALID | 文件类型不支持 | 400 |
| 2003 | FILE_SIZE_EXCEEDED | 文件大小超限 | 400 |
| 2004 | FILE_PARSE_FAILED | 文件解析失败 | 400 |
| 2005 | FILE_FORMAT_INVALID | 文件格式不正确 | 400 |
| 2006 | TASK_NOT_FOUND | 上传任务不存在 | 404 |
| 2007 | TASK_EXPIRED | 上传任务已过期 | 410 |
| 2008 | DATA_VALIDATION_FAILED | 数据校验失败 | 400 |
| 2009 | DUPLICATE_DATA | 数据重复 | 409 |
| 2010 | DB_INSERT_FAILED | 数据入库失败 | 500 |

### 文件解析错误详情

当 `code=2004` 或 `code=2005` 时，data中包含详细错误信息：

```json
{
  "code": 2005,
  "message": "文件格式不正确",
  "data": {
    "file": "ifir_detail",
    "errors": [
      { "row": 1, "message": "缺少必要列: Claim_Nbr" },
      { "row": 15, "message": "Delivery_Month格式错误" }
    ]
  }
}
```

---

## 四、IFIR模块错误码（3000-3999）

| 错误码 | 错误名称 | 说明 | HTTP状态码 |
|--------|----------|------|------------|
| 3001 | IFIR_NO_DATA | 无数据 | 200 |
| 3002 | IFIR_ODM_REQUIRED | ODM参数必填 | 400 |
| 3003 | IFIR_SEGMENT_REQUIRED | Segment参数必填 | 400 |
| 3004 | IFIR_MODEL_REQUIRED | Model参数必填 | 400 |
| 3005 | IFIR_TIME_RANGE_INVALID | 时间范围无效 | 400 |
| 3006 | IFIR_ODM_NOT_FOUND | 指定ODM不存在 | 400 |
| 3007 | IFIR_SEGMENT_NOT_FOUND | 指定Segment不存在 | 400 |
| 3008 | IFIR_MODEL_NOT_FOUND | 指定Model不存在 | 400 |
| 3009 | IFIR_QUERY_TIMEOUT | 查询超时 | 504 |

### 无数据响应

当 `code=3001` 时，仍返回正常结构，但cards为空或card内容为空：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "meta": { ... },
    "cards": [
      {
        "odm": "FOXCONN",
        "trend": [],
        "top_models": [],
        "ai_summary": "在所选时间范围内，该ODM无有效数据。"
      }
    ]
  }
}
```

---

## 五、RA模块错误码（4000-4999）

| 错误码 | 错误名称 | 说明 | HTTP状态码 |
|--------|----------|------|------------|
| 4001 | RA_NO_DATA | 无数据 | 200 |
| 4002 | RA_ODM_REQUIRED | ODM参数必填 | 400 |
| 4003 | RA_SEGMENT_REQUIRED | Segment参数必填 | 400 |
| 4004 | RA_MODEL_REQUIRED | Model参数必填 | 400 |
| 4005 | RA_TIME_RANGE_INVALID | 时间范围无效 | 400 |
| 4006 | RA_ODM_NOT_FOUND | 指定ODM不存在 | 400 |
| 4007 | RA_SEGMENT_NOT_FOUND | 指定Segment不存在 | 400 |
| 4008 | RA_MODEL_NOT_FOUND | 指定Model不存在 | 400 |
| 4009 | RA_QUERY_TIMEOUT | 查询超时 | 504 |

---

## 六、AI模块错误码（5000-5999）

| 错误码 | 错误名称 | 说明 | HTTP状态码 |
|--------|----------|------|------------|
| 5001 | AI_SERVICE_UNAVAILABLE | AI服务不可用 | 503 |
| 5002 | AI_TIMEOUT | AI生成超时 | 504 |
| 5003 | AI_CONTENT_FILTER | AI内容被过滤 | 200 |
| 5004 | AI_QUOTA_EXCEEDED | AI配额用尽 | 429 |

### AI服务降级

当AI服务不可用时，分析API仍正常返回，ai_summary使用固定提示：

```json
{
  "ai_summary": "AI分析服务暂时不可用，请稍后重试。"
}
```

---

## 七、前端错误处理建议

### 7.1 错误提示策略

| 错误类型 | 处理方式 |
|----------|----------|
| 1000-1999 | Toast提示，部分需引导用户操作 |
| 2000-2999 | 在上传区域显示详细错误 |
| 3000-3999 | 在结果区显示空态或提示 |
| 4000-4999 | 在结果区显示空态或提示 |
| 5000-5999 | AI总结区显示降级文案 |

### 7.2 重试策略

| 错误码 | 是否可重试 | 重试间隔 |
|--------|------------|----------|
| 1000 | 是 | 5秒后 |
| 1007, 5004 | 是 | 60秒后 |
| 1008, 5001, 5002 | 是 | 10秒后 |
| 其他 | 否 | - |

### 7.3 示例代码

```typescript
// 错误处理示例
async function handleApiError(error: ApiResponse) {
  const { code, message, data } = error;
  
  switch (true) {
    case code >= 2000 && code < 3000:
      // 上传错误，显示详细信息
      showUploadError(data);
      break;
    case code >= 3000 && code < 5000:
      // 分析错误，显示空态
      showEmptyState(message);
      break;
    case code >= 5000 && code < 6000:
      // AI错误，使用降级文案
      setAiSummary('AI分析服务暂时不可用');
      break;
    default:
      // 通用错误
      ElMessage.error(message);
  }
}
```

---

## 八、变更记录

| 日期 | 版本 | 变更内容 |
|------|------|----------|
| 2026-01-26 | v1.0 | 初始版本 |
