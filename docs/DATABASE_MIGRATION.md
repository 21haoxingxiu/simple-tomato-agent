# 数据库迁移说明

## 问题背景

当修改数据库模型（如添加新字段）时，需要同步更新数据库结构。

## 迁移方法

### 方法 1: 使用迁移脚本（推荐）

```bash
cd agent
python scripts/migrate_db.py
```

### 方法 2: 手动迁移

如果迁移脚本无法解决问题，可以手动执行 SQL：

```bash
# 添加 avatar_url 列
sqlite3 data/agentstudio.db "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);"

# 查看表结构
sqlite3 data/agentstudio.db ".schema users"
```

### 方法 3: 重置数据库（仅开发环境）

⚠️ **警告：这会删除所有数据！**

```bash
# 停止服务
# 删除数据库
rm data/agentstudio.db

# 重启服务（会自动创建新的数据库）
```

## 常见迁移场景

### 添加新列

```python
# 在 db/models.py 中添加字段
class User(Base):
    new_field: Mapped[Optional[str]] = mapped_column(String(200))
```

```bash
# 运行迁移
sqlite3 data/agentstudio.db "ALTER TABLE users ADD COLUMN new_field VARCHAR(200);"
```

### 添加索引

```bash
sqlite3 data/agentstudio.db "CREATE INDEX ix_users_new_field ON users(new_field);"
```

### 修改列类型

SQLite 不支持直接修改列类型，需要：

1. 创建新表
2. 复制数据
3. 删除旧表
4. 重命名新表

详见：https://www.sqlite.org/lang_altertable.html

## 检查当前数据库结构

```bash
# 查看所有表
sqlite3 data/agentstudio.db ".tables"

# 查看特定表的结构
sqlite3 data/agentstudio.db ".schema users"

# 查看所有数据
sqlite3 data/agentstudio.db "SELECT * FROM users;"
```

## 未来改进

考虑使用专业的数据库迁移工具：

- **Alembic**: SQLAlchemy 的迁移工具
- **Django migrations**: 如果使用 Django
- **Flyway**: 通用数据库迁移工具
