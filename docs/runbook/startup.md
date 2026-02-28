# 项目启动指南（本地）

本文档用于指导在本机启动 KPI 可视化分析平台的前后端服务。

---

## 1. 前置条件

- Python 3.10+（后端）
- Node.js 18+（前端）
- MySQL 8.0+（数据库）

> 如需变更端口或数据库账号，请修改 `backend/.env`。

---

## 2. 初始化数据库

确保 MySQL 服务已启动，然后在项目根目录执行：

```bash
# 初始化数据库与表结构
mysql -u root -p < scripts/db/init.sql

# （可选）导入 ODM 映射种子数据
mysql -u root -p kpi_visual < scripts/db/seed_odm_mapping.sql
```

---

## 3. 启动后端

```bash
cd backend

# 创建并激活虚拟环境
python -m venv .venv

# Windows
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

配置 `backend/.env`（可参考根目录 `env.example`），确保数据库配置正确：

```ini
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=你的密码
DB_NAME=kpi_visual
```

启动服务：

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

---

## 4. 启动前端

```bash
cd frontend
npm install
npm run dev
```

前端默认请求地址为 `http://localhost:8000/api`，配置位置为 `frontend/src/api/index.ts`。

---

## 5. 访问与验证

- 前端页面：http://localhost:5173
- 后端健康检查：http://localhost:8000/health
- 后端接口文档：http://localhost:8000/docs

---

## 6. 常见问题

1. **数据库连接失败**：检查 MySQL 是否启动、`backend/.env` 的账号密码是否正确。
2. **端口被占用**：修改启动命令端口或停止占用进程。
3. **前端无法调用后端**：确认后端运行中，且前端 `baseURL` 指向正确端口。
