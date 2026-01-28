# 数据库迁移指南

## 1. 迁移工具

项目使用 **Alembic** 管理数据库迁移。

### 配置文件
- `backend/alembic.ini` - Alembic 配置
- `backend/app/db/migrations/` - 迁移脚本目录

---

## 2. 常用命令

### 2.1 创建迁移

```bash
cd backend

# 自动生成迁移（推荐）
alembic revision --autogenerate -m "添加 AI 反馈表"

# 手动创建空迁移
alembic revision -m "手动迁移说明"
```

### 2.2 执行迁移

```bash
# 升级到最新版本
alembic upgrade head

# 升级指定版本
alembic upgrade <revision_id>

# 升级一个版本
alembic upgrade +1
```

### 2.3 回滚迁移

```bash
# 回滚一个版本
alembic downgrade -1

# 回滚到指定版本
alembic downgrade <revision_id>

# 回滚所有
alembic downgrade base
```

### 2.4 查看迁移历史

```bash
# 查看当前版本
alembic current

# 查看迁移历史
alembic history

# 查看待执行的迁移
alembic history --verbose
```

---

## 3. 迁移脚本编写规范

### 3.1 基本结构

```python
"""添加 AI 反馈表

Revision ID: abc123
Revises: def456
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = 'abc123'
down_revision = 'def456'
branch_labels = None
depends_on = None

def upgrade():
    """升级操作"""
    op.create_table(
        'ai_feedbacks',
        sa.Column('id', sa.BigInteger(), nullable=False),
        sa.Column('result_id', sa.BigInteger(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_result_id', 'ai_feedbacks', ['result_id'])

def downgrade():
    """回滚操作"""
    op.drop_index('idx_result_id', table_name='ai_feedbacks')
    op.drop_table('ai_feedbacks')
```

### 3.2 命名规范

- **文件名**：自动生成（如 `abc123_add_ai_feedback_table.py`）
- **描述**：简洁明了，说明变更内容
- **每次迁移**：尽量只做一件事

---

## 4. 常见迁移操作

### 4.1 创建表

```python
def upgrade():
    op.create_table(
        'table_name',
        sa.Column('id', sa.BigInteger(), autoincrement=True, primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now())
    )
```

### 4.2 删除表

```python
def upgrade():
    op.drop_table('table_name')

def downgrade():
    # 回滚时重建表
    op.create_table(...)
```

### 4.3 添加字段

```python
def upgrade():
    op.add_column('table_name', sa.Column('new_field', sa.String(50)))

def downgrade():
    op.drop_column('table_name', 'new_field')
```

### 4.4 修改字段

```python
def upgrade():
    op.alter_column('table_name', 'field_name',
                    existing_type=sa.String(50),
                    type_=sa.String(100))
```

### 4.5 添加索引

```python
def upgrade():
    op.create_index('idx_table_field', 'table_name', ['field_name'])

def downgrade():
    op.drop_index('idx_table_field', table_name='table_name')
```

### 4.6 数据迁移

```python
from sqlalchemy import table, column

def upgrade():
    # 定义表结构
    users_table = table('users',
        column('id', sa.BigInteger),
        column('status', sa.String)
    )
    
    # 批量更新
    op.execute(
        users_table.update()
        .where(users_table.c.status == None)
        .values(status='active')
    )
```

---

## 5. 生产环境迁移流程

### 5.1 迁移前检查

1. **备份数据库**
```bash
mysqldump -u user -p database_name > backup_$(date +%Y%m%d_%H%M%S).sql
```

2. **在测试环境验证**
```bash
# 测试环境执行迁移
alembic upgrade head

# 验证功能
pytest tests/

# 测试回滚
alembic downgrade -1
alembic upgrade head
```

3. **评估影响范围**
- 是否锁表？
- 预计执行时间？
- 是否需要停机？

### 5.2 迁移执行

```bash
# 1. 进入维护模式（可选）
# 2. 执行迁移
alembic upgrade head

# 3. 验证
alembic current
mysql -e "SHOW TABLES; DESCRIBE new_table;"

# 4. 重启服务
systemctl restart kpi_backend

# 5. 退出维护模式
```

### 5.3 迁移失败应急

```bash
# 1. 立即回滚
alembic downgrade -1

# 2. 恢复备份（最坏情况）
mysql -u user -p database_name < backup.sql

# 3. 记录错误日志
# 4. 分析原因，修复脚本
# 5. 重新测试后再执行
```

---

## 6. 大表迁移策略

### 6.1 问题场景

对包含千万级数据的表进行结构变更（如添加字段、修改索引）。

### 6.2 在线迁移方案

使用 **pt-online-schema-change**（Percona Toolkit）

```bash
pt-online-schema-change \
  --alter "ADD COLUMN new_field VARCHAR(50)" \
  --execute \
  D=database_name,t=table_name \
  --host=localhost \
  --user=root \
  --password=password
```

**优点**：
- 不锁表
- 可实时监控进度
- 失败可自动回滚

### 6.3 分批迁移

```python
def upgrade():
    # 先添加字段（允许 NULL）
    op.add_column('large_table', sa.Column('new_field', sa.String(50)))
    
    # 通过后台任务分批更新数据
    # 不在迁移脚本中直接执行

def downgrade():
    op.drop_column('large_table', 'new_field')
```

---

## 7. 注意事项

### 7.1 禁止操作

❌ **直接修改已执行的迁移脚本**（会导致版本混乱）
❌ **在生产环境直接执行 SQL**（绕过迁移管理）
❌ **不写 downgrade**（无法回滚）
❌ **一次迁移改太多东西**（难以排查问题）

### 7.2 最佳实践

✅ 每次迁移只做一件事
✅ 必须在测试环境验证
✅ 大表变更使用在线工具
✅ 重要迁移在低峰期执行
✅ 迁移前后都要备份
✅ 保留足够的回滚时间窗口

### 7.3 字段变更原则

**添加字段**：先允许 NULL，再批量更新，最后改 NOT NULL

```python
# 第一次迁移
def upgrade():
    op.add_column('users', sa.Column('email', sa.String(100)))

# 第二次迁移（数据填充完成后）
def upgrade():
    op.alter_column('users', 'email', nullable=False)
```

---

## 8. 初始化数据库

### 8.1 全新环境

```bash
# 创建数据库
mysql -u root -p -e "CREATE DATABASE kpi_visual CHARACTER SET utf8mb4;"

# 执行初始化 SQL
mysql -u root -p kpi_visual < infra/mysql/init/001_init.sql

# 运行所有迁移
cd backend
alembic upgrade head
```

### 8.2 开发环境重置

```bash
# 使用脚本一键重置
bash infra/scripts/reset_db.sh
```

---

## 9. 迁移日志示例

建议在团队文档中记录每次生产迁移：

| 日期 | 版本 | 说明 | 执行人 | 耗时 | 备注 |
|------|------|------|--------|------|------|
| 2024-01-20 | abc123 | 添加 AI 反馈表 | 张三 | 5s | 无问题 |
| 2024-01-25 | def456 | kpi_details 添加索引 | 李四 | 3min | 使用 pt-osc |

---

## 10. 相关资源

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [Percona Toolkit](https://www.percona.com/software/database-tools/percona-toolkit)
- [MySQL DDL 最佳实践](https://dev.mysql.com/doc/)
