# 本地开发环境搭建指南

## 1. 环境要求

### 必需软件

| 软件 | 版本要求 | 说明 |
|------|---------|------|
| Python | 3.10+ | 后端开发语言 |
| Node.js | 18+ | 前端开发环境 |
| MySQL | 8.0+ | 数据库 |
| Redis | 7.0+ | 缓存/队列 |
| Docker | 20.10+ | 容器化（推荐） |
| Git | 2.30+ | 版本控制 |

### 可选工具

- Docker Compose：一键启动所有服务
- MySQL Workbench：数据库管理
- Postman：API 测试
- VS Code：推荐编辑器

---

## 2. 快速启动（推荐 - 使用 Docker）

### 2.1 克隆项目

```bash
git clone <repository_url>
cd kpi_visual_website
```

### 2.2 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件，修改必要配置
# 主要修改：数据库密码、AI API Key
```

### 2.3 一键启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 2.4 初始化数据

```bash
# 进入后端容器
docker-compose exec backend bash

# 运行初始化脚本
python scripts/seed_data.py
```

### 2.5 访问服务

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000
- API 文档：http://localhost:8000/docs

---

## 3. 手动启动（不使用 Docker）

### 3.1 安装 MySQL

```bash
# macOS
brew install mysql@8.0
brew services start mysql

# Ubuntu
sudo apt install mysql-server
sudo systemctl start mysql

# Windows
# 下载安装包：https://dev.mysql.com/downloads/mysql/
```

### 3.2 创建数据库

```bash
mysql -u root -p

CREATE DATABASE kpi_visual CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'kpi_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON kpi_visual.* TO 'kpi_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# 导入初始化数据
mysql -u kpi_user -p kpi_visual < infra/mysql/init/001_init.sql
```

### 3.3 安装 Redis

```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis

# Windows
# 下载：https://github.com/microsoftarchive/redis/releases
```

### 3.4 启动后端

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate
# Windows
venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 运行数据库迁移
alembic upgrade head

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3.5 启动 Worker

```bash
cd worker

# 激活虚拟环境
source venv/bin/activate  # 或使用 backend 的 venv

# 安装依赖
pip install -r requirements.txt

# 启动 worker
python worker_main.py
```

### 3.6 启动前端

```bash
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

---

## 4. 开发工具配置

### 4.1 VS Code 推荐插件

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "Vue.volar",
    "dbaeumer.vscode-eslint",
    "esbenp.prettier-vscode",
    "ms-azuretools.vscode-docker"
  ]
}
```

### 4.2 Python 开发环境

创建 `.vscode/settings.json`：

```json
{
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

### 4.3 前端开发环境

创建 `.vscode/settings.json`（前端部分）：

```json
{
  "eslint.validate": ["javascript", "javascriptreact", "typescript", "vue"],
  "editor.codeActionsOnSave": {
    "source.fixAll.eslint": true
  }
}
```

---

## 5. 数据库管理

### 5.1 连接数据库

```bash
mysql -u kpi_user -p kpi_visual
```

### 5.2 查看表结构

```sql
SHOW TABLES;
DESCRIBE kpi_details;
```

### 5.3 重置数据库

```bash
# 使用脚本（推荐）
bash infra/scripts/reset_db.sh

# 或手动执行
mysql -u root -p -e "DROP DATABASE IF EXISTS kpi_visual; CREATE DATABASE kpi_visual;"
mysql -u kpi_user -p kpi_visual < infra/mysql/init/001_init.sql
cd backend && alembic upgrade head
```

---

## 6. 常用开发命令

### 6.1 后端

```bash
# 运行测试
pytest

# 代码格式化
black app/
isort app/

# 类型检查
mypy app/

# 生成数据库迁移
alembic revision --autogenerate -m "描述"

# 创建超级用户
python scripts/create_superuser.py
```

### 6.2 前端

```bash
# 代码格式化
npm run format

# 代码检查
npm run lint

# 构建生产版本
npm run build

# 预览生产构建
npm run preview
```

### 6.3 Docker

```bash
# 重启所有服务
docker-compose restart

# 重新构建镜像
docker-compose build

# 停止并删除容器
docker-compose down

# 查看实时日志
docker-compose logs -f backend

# 进入容器
docker-compose exec backend bash
```

---

## 7. 调试技巧

### 7.1 后端调试

VS Code 配置 `.vscode/launch.json`：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": ["app.main:app", "--reload"],
      "jinja": true
    }
  ]
}
```

### 7.2 前端调试

浏览器开发者工具：
- F12 打开 DevTools
- Vue Devtools 插件
- Network 面板查看请求

### 7.3 数据库调试

```bash
# 慢查询日志
mysql> SET GLOBAL slow_query_log = 'ON';
mysql> SET GLOBAL long_query_time = 1;

# 查看执行计划
EXPLAIN SELECT * FROM kpi_details WHERE ...;
```

---

## 8. 常见问题

### 8.1 端口被占用

```bash
# 查看端口占用
# macOS/Linux
lsof -i :8000
# Windows
netstat -ano | findstr :8000

# 杀死进程
kill -9 <PID>
```

### 8.2 数据库连接失败

检查：
1. MySQL 服务是否启动
2. 用户名密码是否正确
3. 数据库是否存在
4. 防火墙设置

### 8.3 前端无法访问后端

检查：
1. 后端是否启动
2. 跨域配置是否正确
3. `VITE_API_BASE_URL` 是否正确

### 8.4 依赖安装失败

```bash
# Python
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir

# Node.js
npm cache clean --force
rm -rf node_modules package-lock.json
npm install
```

---

## 9. 开发流程

### 9.1 日常开发

1. 拉取最新代码：`git pull`
2. 创建功能分支：`git checkout -b feature/xxx`
3. 开发功能
4. 运行测试：`pytest` / `npm test`
5. 提交代码：`git commit -m "描述"`
6. 推送分支：`git push origin feature/xxx`
7. 创建 Pull Request

### 9.2 代码规范

- Python：遵循 PEP 8
- TypeScript：遵循 ESLint 规则
- 提交信息：使用 Conventional Commits 格式

示例：
```
feat: 添加 AI 分析功能
fix: 修复下钻查询性能问题
docs: 更新 API 文档
refactor: 重构 KPI 服务层
test: 添加报表生成测试
```

---

## 10. 获取帮助

- 查看文档：`docs/` 目录
- API 文档：http://localhost:8000/docs
- 提交 Issue：项目 Issue 页面
- 联系团队：内部沟通渠道
