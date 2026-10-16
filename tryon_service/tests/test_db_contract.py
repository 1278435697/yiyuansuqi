"""试穿表结构契约：ORM 列定义必须与 `database/tryon_schema.sql` 完全一致。

模块并入 yisu-ai-platform 后，同一个库里存在三份定义：
本服务的 async ORM、平台的 sync ORM、以及给 DBA 看的 MySQL DDL。
靠人肉同步迟早漂移，所以把 DDL 定为唯一事实源，用测试把列名与列序钉死。
"""

from __future__ import annotations

import re

import pytest
from sqlalchemy import Integer

from app.config import BACKEND_ROOT
from app.db.models import Garment, TryOnRecord

SCHEMA_PATH = BACKEND_ROOT.parent / "database" / "tryon_schema.sql"

# 顺序也要一致：列序不同虽然不影响功能，但会让两侧 diff 永远对不齐
CASES = [(Garment, "tryon_garments"), (TryOnRecord, "tryon_records")]


def _ddl_columns(table: str) -> list[str]:
    """从建表语句里按声明顺序取出列名，跳过索引/主键/外键行。"""
    text = SCHEMA_PATH.read_text(encoding="utf-8")
    match = re.search(
        rf"CREATE TABLE IF NOT EXISTS `{table}` \((.*?)\n\) ENGINE", text, re.S
    )
    assert match, f"{SCHEMA_PATH} 里找不到 `{table}` 的建表语句"
    columns: list[str] = []
    for raw in match.group(1).splitlines():
        line = raw.strip()
        if not line or line.upper().startswith(
            ("PRIMARY KEY", "KEY ", "UNIQUE", "CONSTRAINT", "INDEX", "FOREIGN")
        ):
            # CONSTRAINT 与 FOREIGN KEY 在 DDL 里分成两行写，两个关键字都得过滤
            continue
        head = line.split()[0]
        assert head.startswith("`"), f"`{table}` 里有无法识别的行：{line}"
        columns.append(head.strip("`"))
    return columns


def test_schema_file_exists():
    assert SCHEMA_PATH.is_file(), (
        f"找不到表结构事实源 {SCHEMA_PATH}；模块独立开发时它应位于 <仓库根>/database/，"
        "合并进平台后位于 yisu-ai-platform/database/"
    )


@pytest.mark.parametrize("model,table", CASES)
def test_orm_columns_match_ddl(model, table):
    assert [c.name for c in model.__table__.columns] == _ddl_columns(table)


@pytest.mark.parametrize("model,table", CASES)
def test_tablename_is_prefixed_and_plural(model, table):
    # 平台主库已有 costumes / collections / likes 等表，试穿表必须带 tryon_ 前缀避让
    assert model.__tablename__ == table
    assert table.startswith("tryon_")


def test_cross_table_ids_are_integer():
    """user_id / costume_id 指向平台的自增整型主键，类型不一致会导致 JOIN 静默失效。"""
    assert isinstance(Garment.__table__.c.costume_id.type, Integer)
    assert isinstance(TryOnRecord.__table__.c.user_id.type, Integer)
    assert TryOnRecord.__table__.c.user_id.nullable is True
    assert Garment.__table__.c.costume_id.nullable is True


# SQLAlchemy 版本地板：见 requirements-core.txt 里那段注释。本服务开了 pool_pre_ping，
# 2.0.36 及以下的 aiomysql 适配层 `ping(self, reconnect)` 没有默认值，生产连 MySQL 必炸；
# 而本机跑的是 sqlite，整个测试套碰不到那条代码路径，所以只能用版本断言拦下未来的降级。
SQLALCHEMY_FLOOR = (2, 0, 54)


def test_sqlalchemy_is_new_enough_for_aiomysql_preping():
    import sqlalchemy

    parts = tuple(int(x) for x in sqlalchemy.__version__.split(".")[:3])
    assert parts >= SQLALCHEMY_FLOOR, (
        f"SQLAlchemy {sqlalchemy.__version__} 低于 { '.'.join(map(str, SQLALCHEMY_FLOOR)) }："
        "它的 AsyncAdapt_aiomysql_connection.ping 缺 reconnect 默认值，"
        "连生产 MySQL 时 pre-ping 会直接 TypeError（sqlite 下复现不了）"
    )
