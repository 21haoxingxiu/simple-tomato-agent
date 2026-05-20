#!/usr/bin/env python3
"""
数据库迁移脚本

用于处理数据库结构的变更。
运行方式: python scripts/migrate_db.py
"""

import sqlite3
import os
import sys
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent.parent / "data" / "agentstudio.db"


def check_column_exists(cursor, table_name, column_name):
    """检查列是否存在"""
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns


def migrate():
    """执行数据库迁移"""
    if not DB_PATH.exists():
        print(f"❌ 数据库文件不存在: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    migrations_applied = []

    try:
        # 迁移 1: 添加 avatar_url 列
        if not check_column_exists(cursor, "users", "avatar_url"):
            print("📝 添加 avatar_url 列到 users 表...")
            cursor.execute("ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500);")
            migrations_applied.append("添加 avatar_url 列")
            print("✅ avatar_url 列添加成功")
        else:
            print("✓ avatar_url 列已存在")

        # 可以在这里添加更多迁移...

        if migrations_applied:
            conn.commit()
            print(f"\n🎉 迁移完成！已应用 {len(migrations_applied)} 个变更:")
            for migration in migrations_applied:
                print(f"  - {migration}")
        else:
            print("\n✅ 数据库已是最新版本，无需迁移")

    except Exception as e:
        conn.rollback()
        print(f"\n❌ 迁移失败: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    print("=" * 60)
    print("AgentStudio 数据库迁移工具")
    print("=" * 60)
    print(f"\n数据库路径: {DB_PATH}\n")
    migrate()
