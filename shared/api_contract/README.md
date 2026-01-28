# API 契约

## openapi.yaml
OpenAPI 3.0 规范的 API 文档，由后端自动生成。

### 生成方式

```bash
# 启动后端后访问
curl http://localhost:8000/openapi.json > openapi.yaml
```

### 用途

1. **前端开发**：根据规范生成 API 客户端
2. **文档展示**：使用 Swagger UI 展示
3. **接口测试**：导入 Postman/Insomnia
4. **Mock 服务**：快速搭建 Mock 服务器

### 使用工具

```bash
# 生成 TypeScript 客户端
npx openapi-typescript-codegen --input openapi.yaml --output ../frontend/src/api/generated

# 生成 Python 客户端
openapi-generator-cli generate -i openapi.yaml -g python -o ./python-client
```

## error_codes.md
统一错误码说明文档，与 `docs/api/error-codes.md` 内容一致。

前端可直接引用此文档进行错误提示。
