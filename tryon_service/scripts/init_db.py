"""数据库初始化/重建。

用法：
    python -m scripts.init_db            # 建表（已存在则跳过）
    python -m scripts.init_db --recreate # 删除全部表后重建（会清空试穿记录！）
    python -m scripts.init_db --seed     # 建表后立即导入素材
"""

from __future__ import annotations

import argparse
import asyncio

from scripts._bootstrap import bootstrap

bootstrap()


async def _run(recreate: bool, seed: bool) -> int:
    from app.db.base import create_all, get_engine
    from app.db.models import Base
    from app.services.seed import seed_garments

    engine = get_engine()
    if recreate:
        print("[init_db] 即将删除并重建所有表（数据不可恢复）")
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
    await create_all()
    print("[init_db] 表结构已就绪")
    if seed:
        written, skipped = await seed_garments()
        print(f"[init_db] 素材种子：写入 {written} 条，跳过 {len(skipped)} 条")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="初始化 SQLite/MySQL 表结构")
    parser.add_argument("--recreate", action="store_true", help="先 drop 再 create（危险）")
    parser.add_argument("--seed", action="store_true", help="建表后导入素材索引")
    args = parser.parse_args()
    return asyncio.run(_run(args.recreate, args.seed))


if __name__ == "__main__":
    raise SystemExit(main())
