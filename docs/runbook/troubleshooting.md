# 故障排查手册

## 1. 快速诊断流程

```
发现问题 → 查看日志 → 定位组件 → 检查配置 → 尝试修复 → 验证恢复 → 记录归档
```

---

## 2. 后端服务问题

### 2.1 服务无法启动

**症状**：
- Docker 容器启动失败
- 启动后立即退出

**排查步骤**：

```bash
# 查看容器日志
docker logs kpi_backend

# 检查配置文件
cat .env

# 检查端口占用
lsof -i :8000

# 手动启动测试
docker run --rm -it --env-file .env kpi-backend:latest bash
python -m app.main
```

**常见原因**：
- 数据库连接失败
- 环境变量未设置
- 端口被占用
- 依赖包缺失

**解决方案**：
```bash
# 检查数据库连接
mysql -h $DB_HOST -u $DB_USER -p$DB_PASSWORD -e "SELECT 1"

# 重新构建镜像
docker-compose build --no-cache backend

# 清理并重启
docker-compose down
docker-compose up -d
```

---

### 2.2 API 响应慢

**症状**：
- 接口响应时间超过 5 秒
- 前端请求超时

**排查步骤**：

```bash
# 查看后端日志
docker logs -f kpi_backend | grep "latency"

# 检查数据库慢查询
mysql> SHOW FULL PROCESSLIST;
mysql> SELECT * FROM mysql.slow_log ORDER BY start_time DESC LIMIT 10;

# 检查 Redis 状态
redis-cli INFO stats

# 检查系统资源
top
htop
docker stats
```

**常见原因**：
- 数据库查询未优化
- 缺少索引
- 数据量过大
- 连接池耗尽

**解决方案**：
```sql
-- 添加索引
CREATE INDEX idx_time_metric ON kpi_details(time_value, metric_code);

-- 优化查询
EXPLAIN SELECT ...;

-- 调整连接池
# .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
```

---

### 2.3 内存溢出（OOM）

**症状**：
- 容器被 Killed
- `docker logs` 显示 "Killed"

**排查步骤**：

```bash
# 查看内存使用
docker stats kpi_backend

# 查看系统内存
free -h

# 检查应用内存使用
docker exec kpi_backend python -c "import psutil; print(psutil.virtual_memory())"
```

**解决方案**：

```yaml
# docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          memory: 2G
        reservations:
          memory: 1G
```

```python
# 代码优化：分批处理
for batch in chunked(large_data, size=1000):
    process_batch(batch)
```

---

## 3. 数据库问题

### 3.1 连接数耗尽

**症状**：
- 错误：`Too many connections`
- API 返回 500 错误

**排查步骤**：

```sql
-- 查看当前连接
SHOW PROCESSLIST;

-- 查看最大连接数
SHOW VARIABLES LIKE 'max_connections';

-- 查看连接状态
SHOW STATUS LIKE 'Threads_connected';
```

**解决方案**：

```sql
-- 临时增加连接数
SET GLOBAL max_connections = 500;

-- 杀死空闲连接
SELECT CONCAT('KILL ', id, ';') FROM information_schema.processlist 
WHERE command = 'Sleep' AND time > 300;
```

```ini
# /etc/mysql/mysql.conf.d/mysqld.cnf
[mysqld]
max_connections = 500
wait_timeout = 600
interactive_timeout = 600
```

---

### 3.2 主从延迟

**症状**：
- 读取数据不一致
- 从库数据滞后

**排查步骤**：

```sql
-- 从库执行
SHOW SLAVE STATUS\G

-- 查看延迟秒数
Seconds_Behind_Master: 120
```

**常见原因**：
- 主库写入压力大
- 从库配置低
- 网络延迟
- 大事务

**解决方案**：

```sql
-- 跳过错误（慎用）
STOP SLAVE;
SET GLOBAL sql_slave_skip_counter = 1;
START SLAVE;

-- 并行复制
SET GLOBAL slave_parallel_workers = 4;
SET GLOBAL slave_parallel_type = 'LOGICAL_CLOCK';
```

---

### 3.3 磁盘空间不足

**症状**：
- 错误：`No space left on device`
- 数据库无法写入

**排查步骤**：

```bash
# 检查磁盘空间
df -h

# 查看大文件
du -sh /var/lib/mysql/*

# 查看 binlog 大小
ls -lh /var/log/mysql/mysql-bin.*
```

**解决方案**：

```bash
# 清理 binlog（慎重！）
mysql> PURGE BINARY LOGS BEFORE NOW() - INTERVAL 3 DAY;

# 清理慢查询日志
> /var/log/mysql/mysql-slow.log

# 归档旧数据
# 导出并删除 1 年前的数据
```

---

## 4. Redis 问题

### 4.1 Redis 连接失败

**症状**：
- 错误：`Connection refused`
- 缓存功能异常

**排查步骤**：

```bash
# 检查 Redis 状态
systemctl status redis
docker ps | grep redis

# 测试连接
redis-cli ping

# 查看日志
tail -f /var/log/redis/redis-server.log
```

**解决方案**：

```bash
# 重启 Redis
systemctl restart redis

# 检查配置
grep "^bind" /etc/redis/redis.conf
grep "^requirepass" /etc/redis/redis.conf
```

---

### 4.2 Redis 内存满

**症状**：
- 错误：`OOM command not allowed`
- 无法写入数据

**排查步骤**：

```bash
redis-cli INFO memory

# 查看最大内存
redis-cli CONFIG GET maxmemory

# 查看淘汰策略
redis-cli CONFIG GET maxmemory-policy
```

**解决方案**：

```bash
# 临时增加内存（重启后失效）
redis-cli CONFIG SET maxmemory 4gb

# 清理缓存
redis-cli FLUSHDB

# 设置淘汰策略
redis-cli CONFIG SET maxmemory-policy allkeys-lru
```

---

## 5. AI 模块问题

### 5.1 AI 任务失败

**症状**：
- 任务状态：`failed`
- AI 结果为空

**排查步骤**：

```bash
# 查看 Worker 日志
docker logs -f kpi_worker

# 查看任务详情
mysql> SELECT * FROM ai_tasks WHERE status='failed' ORDER BY created_at DESC LIMIT 10;

# 测试 AI 接口
curl -X POST http://localhost:8000/api/v1/ai/tasks \
  -H "Content-Type: application/json" \
  -d '{"metric": "sales_amount", "time_range": "2024-W01"}'
```

**常见原因**：
- OpenAI API Key 无效
- API 配额用尽
- 网络超时
- Prompt 版本不存在
- 证据包格式错误

**解决方案**：

```bash
# 检查 API Key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"

# 重试任务
python scripts/retry_failed_tasks.py

# 切换到本地模型
# .env
AI_PROVIDER=local
```

---

### 5.2 AI 结果校验失败

**症状**：
- 错误：`Validation failed`
- 结果不符合预期格式

**排查步骤**：

```python
# 查看原始输出
result = db.query(AIResult).filter_by(task_id=task_id).first()
print(result.raw_output)
print(result.validation_errors)
```

**解决方案**：

```python
# 优化 Prompt
# backend/app/ai/prompts/insight_v2.md

# 调整校验规则
# backend/app/ai/guardrails.py
```

---

## 6. Worker 队列问题

### 6.1 任务堆积

**症状**：
- 队列长度持续增长
- 任务等待时间过长

**排查步骤**：

```bash
# 查看队列长度
redis-cli LLEN celery

# 查看 Worker 状态
docker logs kpi_worker

# 查看任务统计
celery -A worker_main inspect stats
```

**解决方案**：

```bash
# 增加 Worker 数量
docker-compose up -d --scale worker=3

# 清空队列（慎重！）
redis-cli DEL celery

# 调整并发数
# worker/worker_main.py
app.conf.worker_concurrency = 4
```

---

### 6.2 Worker 僵死

**症状**：
- Worker 进程存在但不处理任务
- 日志无输出

**排查步骤**：

```bash
# 查看进程状态
ps aux | grep worker

# 查看资源占用
top -p <worker_pid>

# 查看堆栈
strace -p <worker_pid>
```

**解决方案**：

```bash
# 重启 Worker
docker-compose restart worker

# 清理僵尸任务
celery -A worker_main purge
```

---

## 7. 前端问题

### 7.1 白屏

**症状**：
- 页面空白
- 控制台报错

**排查步骤**：

```bash
# 浏览器控制台
F12 → Console

# 检查 Network
F12 → Network → 查看失败的请求

# 检查静态资源
ls /var/www/kpi_visual/dist/assets/
```

**常见原因**：
- JavaScript 加载失败
- API 接口不通
- 路由配置错误

**解决方案**：

```bash
# 清理缓存
Ctrl + Shift + R

# 检查 Nginx 配置
nginx -t
systemctl reload nginx

# 重新构建
cd frontend
npm run build
```

---

### 7.2 跨域错误

**症状**：
- 错误：`CORS policy blocked`
- API 请求失败

**排查步骤**：

```bash
# 检查响应头
curl -I http://localhost:8000/api/v1/kpi/dashboard

# 查看后端日志
docker logs kpi_backend | grep CORS
```

**解决方案**：

```python
# backend/app/main.py
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-domain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 8. 网络问题

### 8.1 容器间无法通信

**症状**：
- 后端无法连接数据库
- Worker 无法连接 Redis

**排查步骤**：

```bash
# 检查网络
docker network ls
docker network inspect kpi_network

# 测试连通性
docker exec kpi_backend ping mysql
docker exec kpi_backend telnet mysql 3306
```

**解决方案**：

```bash
# 重建网络
docker network rm kpi_network
docker network create kpi_network

# 重新连接容器
docker-compose down
docker-compose up -d
```

---

## 9. 性能问题

### 9.1 导出超时

**症状**：
- 导出任务长时间不完成
- 生成的文件过大

**排查步骤**：

```bash
# 查看任务状态
mysql> SELECT * FROM report_tasks WHERE status='running' AND TIMESTAMPDIFF(MINUTE, started_at, NOW()) > 10;

# 查看磁盘 I/O
iostat -x 1

# 查看文件生成进度
ls -lh /app/exports/
```

**解决方案**：

```python
# 分批导出
# backend/app/services/export_service.py
async def export_large_data(data):
    for chunk in chunks(data, size=10000):
        await write_to_file(chunk)
        await asyncio.sleep(0.1)  # 避免 CPU 占满
```

---

### 9.2 看板加载慢

**症状**：
- Dashboard 首屏加载超过 5 秒

**优化方案**：

```typescript
// 前端懒加载
const Dashboard = () => import('./views/dashboard/Dashboard.vue');

// 接口合并
Promise.all([
  api.getKpiSummary(),
  api.getTrendData(),
  api.getAbnormalList()
]);

// 数据缓存
const cache = new Map();
if (cache.has(cacheKey)) {
  return cache.get(cacheKey);
}
```

```python
# 后端缓存
from functools import lru_cache

@lru_cache(maxsize=100)
def get_kpi_summary(time_range: str):
    # ...
```

---

## 10. 日志分析

### 10.1 日志位置

| 组件 | 日志路径 |
|------|----------|
| 后端 | `/app/logs/app.log` |
| Worker | `/app/logs/worker.log` |
| Nginx | `/var/log/nginx/access.log` |
| MySQL | `/var/log/mysql/error.log` |
| Redis | `/var/log/redis/redis-server.log` |

### 10.2 常用日志命令

```bash
# 实时查看
tail -f /path/to/log

# 搜索错误
grep -i "error" /path/to/log

# 统计错误数
grep -c "ERROR" /app/logs/app.log

# 按时间过滤
awk '/2024-01-20 10:00/,/2024-01-20 11:00/' /app/logs/app.log

# 分析慢查询
pt-query-digest /var/log/mysql/mysql-slow.log
```

---

## 11. 应急联系

### 11.1 升级流程

1. **Level 1**：自行排查（参考本文档）
2. **Level 2**：联系开发团队
3. **Level 3**：联系运维负责人
4. **Level 4**：启动应急预案

### 11.2 联系方式

- 开发负责人：xxx
- 运维负责人：xxx
- DBA：xxx
- 紧急电话：xxx

---

## 12. 故障记录模板

```markdown
## 故障时间
2024-01-20 10:30 - 11:00

## 影响范围
- 用户无法访问看板
- API 响应 500 错误

## 故障原因
数据库连接池耗尽

## 解决方案
1. 临时增加连接池大小
2. 杀死空闲连接
3. 优化慢查询

## 后续优化
- 添加连接池监控
- 优化查询索引
- 调整配置参数

## 责任人
xxx

## 复盘结论
...
```
