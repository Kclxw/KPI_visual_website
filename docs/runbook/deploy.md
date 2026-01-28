# 生产环境部署手册

## 1. 部署架构

```
                    ┌──────────────┐
                    │   Nginx      │
                    │  (反向代理)   │
                    └──────┬───────┘
                           │
            ┌──────────────┼──────────────┐
            │              │              │
      ┌─────▼─────┐  ┌────▼────┐   ┌────▼────┐
      │  Frontend  │  │ Backend │   │ Backend │
      │   (静态)    │  │  Node1  │   │  Node2  │
      └───────────┘  └────┬────┘   └────┬────┘
                          │              │
            ┌─────────────┼──────────────┘
            │             │
      ┌─────▼─────┐  ┌───▼─────┐  ┌────────┐
      │   MySQL   │  │  Redis  │  │ Worker │
      │  (主从)    │  │ (缓存)   │  │ (Celery)│
      └───────────┘  └─────────┘  └────────┘
```

---

## 2. 服务器要求

### 2.1 最小配置

| 组件 | CPU | 内存 | 磁盘 | 数量 |
|------|-----|------|------|------|
| 后端 | 2核 | 4GB | 50GB | 2台 |
| 数据库 | 4核 | 8GB | 200GB | 2台(主从) |
| Redis | 2核 | 4GB | 20GB | 1台 |
| Worker | 2核 | 4GB | 50GB | 1台 |
| Nginx | 2核 | 2GB | 20GB | 1台 |

### 2.2 推荐配置（生产）

| 组件 | CPU | 内存 | 磁盘 | 数量 |
|------|-----|------|------|------|
| 后端 | 4核 | 8GB | 100GB | 3台 |
| 数据库 | 8核 | 16GB | 500GB SSD | 2台(主从) |
| Redis | 4核 | 8GB | 50GB | 2台(主从) |
| Worker | 4核 | 8GB | 100GB | 2台 |
| Nginx | 4核 | 4GB | 50GB | 2台 |

---

## 3. 部署前准备

### 3.1 检查清单

- [ ] 服务器已准备就绪
- [ ] 域名已备案并解析
- [ ] SSL 证书已申请
- [ ] 数据库已创建
- [ ] 代码已通过测试
- [ ] 部署文档已更新
- [ ] 回滚方案已准备

### 3.2 创建部署用户

```bash
# 所有服务器执行
sudo adduser deploy
sudo usermod -aG docker deploy
sudo usermod -aG sudo deploy

# 配置免密登录
ssh-copy-id deploy@<server_ip>
```

### 3.3 安装 Docker

```bash
# Ubuntu 20.04/22.04
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo systemctl start docker
sudo systemctl enable docker
```

---

## 4. 数据库部署

### 4.1 MySQL 主库

```bash
# 安装 MySQL
sudo apt update
sudo apt install mysql-server-8.0

# 安全配置
sudo mysql_secure_installation

# 配置文件 /etc/mysql/mysql.conf.d/mysqld.cnf
[mysqld]
server-id = 1
log_bin = /var/log/mysql/mysql-bin.log
binlog_format = ROW
max_binlog_size = 100M
expire_logs_days = 7
default_authentication_plugin = mysql_native_password

# 创建数据库
mysql -u root -p
CREATE DATABASE kpi_visual CHARACTER SET utf8mb4;
CREATE USER 'kpi_user'@'%' IDENTIFIED BY 'strong_password_here';
GRANT ALL PRIVILEGES ON kpi_visual.* TO 'kpi_user'@'%';

# 创建复制用户
CREATE USER 'repl'@'%' IDENTIFIED BY 'repl_password';
GRANT REPLICATION SLAVE ON *.* TO 'repl'@'%';
FLUSH PRIVILEGES;

# 重启服务
sudo systemctl restart mysql
```

### 4.2 MySQL 从库

```bash
# 安装 MySQL（同主库）

# 配置文件
[mysqld]
server-id = 2
relay-log = /var/log/mysql/mysql-relay-bin.log
log_bin = /var/log/mysql/mysql-bin.log
read_only = 1

# 重启服务
sudo systemctl restart mysql

# 配置主从复制
mysql -u root -p
CHANGE MASTER TO
  MASTER_HOST='<主库IP>',
  MASTER_USER='repl',
  MASTER_PASSWORD='repl_password',
  MASTER_LOG_FILE='mysql-bin.000001',
  MASTER_LOG_POS=0;

START SLAVE;
SHOW SLAVE STATUS\G
```

### 4.3 导入数据

```bash
# 在主库执行
mysql -u kpi_user -p kpi_visual < infra/mysql/init/001_init.sql

# 运行迁移
cd backend
alembic upgrade head
```

---

## 5. Redis 部署

### 5.1 Redis 主库

```bash
# 安装
sudo apt install redis-server

# 配置 /etc/redis/redis.conf
bind 0.0.0.0
port 6379
requirepass strong_redis_password
maxmemory 2gb
maxmemory-policy allkeys-lru

# 重启
sudo systemctl restart redis
sudo systemctl enable redis
```

### 5.2 Redis 从库（可选）

```bash
# 配置
replicaof <主库IP> 6379
masterauth strong_redis_password
replica-read-only yes
```

---

## 6. 后端部署

### 6.1 构建镜像

```bash
cd backend

# 创建 Dockerfile
cat > Dockerfile <<'EOF'
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF

# 构建镜像
docker build -t kpi-backend:latest .

# 推送到私有仓库（可选）
docker tag kpi-backend:latest registry.example.com/kpi-backend:latest
docker push registry.example.com/kpi-backend:latest
```

### 6.2 部署服务

```bash
# 创建 docker-compose.yml
cat > docker-compose.prod.yml <<'EOF'
version: '3.8'

services:
  backend:
    image: kpi-backend:latest
    container_name: kpi_backend
    restart: always
    env_file:
      - .env.production
    ports:
      - "8000:8000"
    volumes:
      - ./logs:/app/logs
      - ./exports:/app/exports
    networks:
      - kpi_network

networks:
  kpi_network:
    external: true
EOF

# 启动服务
docker-compose -f docker-compose.prod.yml up -d

# 查看日志
docker-compose -f docker-compose.prod.yml logs -f
```

### 6.3 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 检查 API 文档
curl http://localhost:8000/docs
```

---

## 7. Worker 部署

```bash
cd worker

# 构建镜像
docker build -t kpi-worker:latest .

# 启动服务
docker run -d \
  --name kpi_worker \
  --restart always \
  --env-file .env.production \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/exports:/app/exports \
  --network kpi_network \
  kpi-worker:latest

# 查看日志
docker logs -f kpi_worker
```

---

## 8. 前端部署

### 8.1 构建前端

```bash
cd frontend

# 安装依赖
npm install

# 构建生产版本
npm run build

# 打包构建结果
tar -czf dist.tar.gz dist/
```

### 8.2 部署到 Nginx

```bash
# 上传到服务器
scp dist.tar.gz deploy@<nginx_server>:/tmp/

# 解压到 Nginx 目录
ssh deploy@<nginx_server>
sudo mkdir -p /var/www/kpi_visual
sudo tar -xzf /tmp/dist.tar.gz -C /var/www/kpi_visual
sudo chown -R www-data:www-data /var/www/kpi_visual
```

---

## 9. Nginx 配置

### 9.1 安装 Nginx

```bash
sudo apt install nginx
```

### 9.2 配置站点

```bash
sudo nano /etc/nginx/sites-available/kpi_visual

# 配置内容
server {
    listen 80;
    server_name your-domain.com;

    # 重定向到 HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    # 前端静态文件
    location / {
        root /var/www/kpi_visual/dist;
        try_files $uri $uri/ /index.html;
    }

    # 后端 API
    location /api/ {
        proxy_pass http://backend_servers;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # WebSocket（如需要）
    location /ws/ {
        proxy_pass http://backend_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}

# 后端负载均衡
upstream backend_servers {
    least_conn;
    server backend1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server backend2:8000 weight=1 max_fails=3 fail_timeout=30s;
}

# 启用配置
sudo ln -s /etc/nginx/sites-available/kpi_visual /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## 10. SSL 证书

### 10.1 使用 Let's Encrypt

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 申请证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 11. 监控与日志

### 11.1 日志配置

```bash
# 后端日志
docker logs -f kpi_backend > /var/log/kpi/backend.log

# Nginx 日志
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### 11.2 监控指标

- CPU 使用率
- 内存使用率
- 磁盘空间
- API 响应时间
- 数据库连接数
- Redis 命中率

---

## 12. 备份策略

### 12.1 数据库备份

```bash
# 每日备份脚本
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backup/mysql"
mkdir -p $BACKUP_DIR

mysqldump -u kpi_user -p'password' \
  --single-transaction \
  --routines \
  --triggers \
  kpi_visual | gzip > $BACKUP_DIR/kpi_visual_$DATE.sql.gz

# 保留 7 天
find $BACKUP_DIR -name "*.sql.gz" -mtime +7 -delete
```

### 12.2 自动备份

```bash
# 添加到 crontab
crontab -e

# 每天凌晨 2 点备份
0 2 * * * /path/to/backup_script.sh
```

---

## 13. 部署验证

### 13.1 检查列表

- [ ] 所有服务正常启动
- [ ] 数据库连接正常
- [ ] Redis 连接正常
- [ ] API 接口可访问
- [ ] 前端页面正常加载
- [ ] 登录功能正常
- [ ] 核心功能测试通过
- [ ] 日志正常输出
- [ ] 监控指标正常

### 13.2 压力测试

```bash
# 使用 Apache Bench
ab -n 1000 -c 10 http://your-domain.com/api/v1/kpi/dashboard

# 使用 Locust
pip install locust
locust -f tests/load_test.py
```

---

## 14. 回滚方案

### 14.1 快速回滚

```bash
# 回滚后端
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d kpi_backend:previous_version

# 回滚数据库（如有迁移）
cd backend
alembic downgrade -1

# 回滚前端
sudo rm -rf /var/www/kpi_visual/dist
sudo tar -xzf /backup/dist_previous.tar.gz -C /var/www/kpi_visual
```

---

## 15. 运维联系

- 技术负责人：xxx
- 运维负责人：xxx
- 紧急联系电话：xxx
- 监控告警：xxx
