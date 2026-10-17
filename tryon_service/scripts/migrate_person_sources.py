"""一次性迁移：把公开结果目录里的 person_source.jpg 搬到私密目录并改写 DB URL。

背景：上轮把 person_source.jpg 从 results_dir/<task>/ 挪到了
data/private/person_sources/<task>/，但旧任务的结果目录里仍有残留副本，
且库里 person_url 还指向旧的静态路径。本脚本把残留文件搬走并改写 URL。

特性：
- 幂等：已搬过的目录跳过，URL 已改过的行跳过
- --dry-run：只打印计划，不搬文件不改 DB
- 找不到目标文件时不报错（旧任务可能已被清理）
- 绝不碰非自己管的文件（只动 person_source.jpg，不动 result.jpg 等）

用法：
    python -m scripts.migrate_person_sources            # 真跑
    python -m scripts.migrate_person_sources --dry-run  # 只打印
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

from scripts._bootstrap import bootstrap

bootstrap()

from app.config import get_settings  # noqa: E402
from app.db.base import session_factory  # noqa: E402
from app.db.models import TryOnRecord  # noqa: E402
from app.logs import get_logger  # noqa: E402

logger = get_logger("scripts.migrate_person_sources")

_API_PERSON_URL_PREFIX = "/api/v1/history"


def _is_legacy_person_url(url: str | None) -> bool:
    """判断 URL 是否指向旧的静态路径（需要改写）。"""
    if not url:
        return False
    # 旧 URL 形如 /tryon-results/<task>/person_source.jpg 或 /uploads/tryon/<task>/person_source.jpg
    return url.endswith("/person_source.jpg") and _API_PERSON_URL_PREFIX not in url


def _build_api_person_url(task_id: str) -> str:
    return f"{_API_PERSON_URL_PREFIX}/{task_id}/person-source"


async def migrate(*, dry_run: bool) -> tuple[int, int, int]:
    """返回 (搬移文件数, 改写 URL 数, 跳过数)。"""
    settings = get_settings()
    moved = 0
    updated = 0
    skipped = 0

    if not settings.results_dir.is_dir():
        logger.info("results_dir 不存在，跳过: %s", settings.results_dir)
        return 0, 0, 0

    async with session_factory()() as session:
        # 1. 扫描结果目录，搬移残留的 person_source.jpg
        for task_dir in settings.results_dir.iterdir():
            if not task_dir.is_dir():
                continue
            src = task_dir / "person_source.jpg"
            if not src.is_file():
                continue

            dst_dir = settings.person_sources_dir / task_dir.name
            dst = dst_dir / "person_source.jpg"

            if dst.is_file():
                # 目标已存在（幂等），删除源副本
                if dry_run:
                    logger.info("[dry-run] 将删除源副本: %s", src)
                else:
                    src.unlink()
                    logger.info("已删除源副本（目标已存在）: %s", src)
                skipped += 1
                continue

            if dry_run:
                logger.info("[dry-run] 将搬移: %s → %s", src, dst_dir)
            else:
                dst_dir.mkdir(parents=True, exist_ok=True)
                shutil.move(str(src), str(dst))
                logger.info("已搬移: %s → %s", src, dst_dir)
            moved += 1

        # 2. 改写库里仍指向旧静态路径的 person_url
        from sqlalchemy import select, update

        stmt = select(TryOnRecord).where(
            TryOnRecord.person_url.isnot(None),
            TryOnRecord.person_url != "",
        )
        result = await session.execute(stmt)
        records = result.scalars().all()

        for record in records:
            if not _is_legacy_person_url(record.person_url):
                continue
            new_url = _build_api_person_url(record.task_id)
            if dry_run:
                logger.info("[dry-run] 将改写 URL: %s → %s", record.person_url, new_url)
            else:
                record.person_url = new_url
                logger.info("已改写 URL: %s → %s", record.task_id, new_url)
            updated += 1

        if not dry_run and updated:
            await session.commit()

    return moved, updated, skipped


def main() -> int:
    parser = argparse.ArgumentParser(description="迁移残留的 person_source.jpg 到私密目录")
    parser.add_argument("--dry-run", action="store_true", help="只打印计划，不搬文件不改 DB")
    args = parser.parse_args()

    logger.info("migrate_person_sources 启动: dry_run=%s", args.dry_run)

    import asyncio

    moved, updated, skipped = asyncio.run(migrate(dry_run=args.dry_run))
    logger.info("完成: 搬移 %d, 改写 URL %d, 跳过 %d", moved, updated, skipped)
    return 0


if __name__ == "__main__":
    sys.exit(main())
