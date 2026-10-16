"""素材入库：data/garments/index.json → 数据库（upsert）。

用法：
    python -m scripts.seed_garments [--force]
"""

from __future__ import annotations

import argparse
import asyncio

from scripts._bootstrap import bootstrap

bootstrap()


async def _run(force: bool) -> int:
    from app.db.base import create_all
    from app.services.seed import seed_garments

    await create_all()
    written, skipped = await seed_garments(force=force)
    print(f"[seed] 写入/更新 {written} 条素材")
    for reason in skipped:
        print(f"[seed][skip] {reason}")
    return 0 if written or not skipped else 1


def main() -> int:
    parser = argparse.ArgumentParser(description="把示例/真实素材索引导入数据库")
    parser.add_argument("--force", action="store_true", help="已存在的素材也重新覆盖写入")
    args = parser.parse_args()
    return asyncio.run(_run(args.force))


if __name__ == "__main__":
    raise SystemExit(main())
