# -*- coding: utf-8 -*-
"""自动对比 models.py 模型与 MySQL 实际表结构，补齐所有缺失列（幂等）。"""
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from sqlalchemy import inspect, text
from sqlalchemy.dialects import mysql as mysql_dialect
from app.db.models import Base
from app.db.database import engine

insp = inspect(engine)
dialect = mysql_dialect.dialect()
fixed = []
skipped = []
with engine.begin() as conn:
    for table in Base.metadata.sorted_tables:
        if not insp.has_table(table.name):
            skipped.append(table.name)
            continue
        existing = {c['name'] for c in insp.get_columns(table.name)}
        for col in table.columns:
            if col.name in existing:
                continue
            coltype = col.type.compile(dialect=dialect)
            nullable = "NULL" if col.nullable else "NOT NULL"
            default = ""
            if col.default is not None and col.default.is_scalar:
                d = col.default.arg
                default = f" DEFAULT {d!r}" if isinstance(d, (int, float, str)) else ""
            elif not col.nullable:
                default = " DEFAULT ''" if isinstance(col.type, (mysql_dialect.String, mysql_dialect.TEXT, mysql_dialect.VARCHAR)) else " DEFAULT 0"
            sql = f"ALTER TABLE `{table.name}` ADD COLUMN `{col.name}` {coltype} {nullable}{default}"
            try:
                conn.execute(text(sql))
                fixed.append(f"{table.name}.{col.name} -> {coltype}")
            except Exception as e:
                skipped.append(f"{table.name}.{col.name}: {str(e)[:120]}")

print("FIXED COLUMNS:")
for f in fixed: print("  +", f)
print("SKIPPED/TABLES:")
for s in skipped: print("  -", s)
print("DONE")
