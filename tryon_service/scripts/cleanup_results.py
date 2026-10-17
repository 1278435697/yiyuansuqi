"""清理过期的试穿结果目录与数据库记录。

由 systemd timer 定期触发（默认每天 03:00），也可手动执行：
    python -m scripts.cleanup_results [--dry-run] [--ttl-days 30]

清理逻辑：
1. 扫描 results_dir 下所有子目录，按目录修改时间判断是否过期
2. 对过期目录：删除磁盘文件 + 删除 tryon_records 对应行
3. 同时扫描 person_sources_dir 下的过期目录一并清理

幂等：重复执行不会产生副作用。
"""

from __future__ import annotations

import argparse
import shutil
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

from scripts._bootstrap import bootstrap

bootstrap()

from app.config import get_settings  # noqa: E402
from app.db.base import session_factory  # noqa: E402
from app.db.models import TryOnRecord  # noqa: E402
from app.logs import get_logger  # noqa: E402

logger = get_logger("scripts.cleanup_results")


def _is_expired(path: Path, cutoff: float) -> bool:
    return path.stat().st_mtime < cutoff


def _safe_remove_dir(target: Path, root: Path) -> bool:
    """带路径穿越防护的目录删除。"""
    if not target.is_dir():
        return False
    try:
        target.resolve().relative_to(root.resolve())
    except ValueError:
        logger.error("拒绝删除越界目录: %s", target)
        return False
    shutil.rmtree(target, ignore_errors=True)
    return True


async def cleanup(*, ttl_days: int, dry_run: bool) -> tuple[int, int]:
    """返回 (清理的目录数, 清理的数据库行数)。"""
    settings = get_settings()
    cutoff = time.time() - ttl_days * 86400
    cutoff_dt = datetime.fromtimestamp(cutoff)

    removed_dirs = 0
    removed_rows = 0

    async with session_factory()() as session:
        # 1. 清理 results_dir
        if settings.results_dir.is_dir():
            for child in settings.results_dir.iterdir():
                if child.is_dir() and _is_expired(child, cutoff):
                    if dry_run:
                        logger.info("[dry-run] 将删除: %s", child)
                    else:
                        if _safe_remove_dir(child, settings.results_dir):
                            logger.info("已删除结果目录: %s", child)
                    removed_dirs += 1

        # 2. 清理 person_sources_dir
        if settings.person_sources_dir.is_dir():
            for child in settings.person_sources_dir.iterdir():
                if child.is_dir() and _is_expired(child, cutoff):
                    if dry_run:
                        logger.info("[dry-run] 将删除原图目录: %s", child)
                    else:
                        if _safe_remove_dir(child, settings.person_sources_dir):
                            logger.info("已删除原图目录: %s", child)

        # 3. 清理数据库过期记录
        from sqlalchemy import delete

        cutoff_iso = cutoff_dt.isoformat()
        stmt = delete(TryOnRecord).where(TryOnRecord.created_at < cutoff_dt)
        result = await session.execute(stmt)
        await session.commit()
        removed_rows = result.rowcount
        if removed_rows:
            logger.info("已删除 %d 条过期数据库记录 (created_at < %s)", removed_rows, cutoff_iso)

    return removed_dirs, removed_rows


def main() -> int:
    parser = argparse.ArgumentParser(description="清理过期的试穿结果")
    parser.add_argument("--ttl-days", type=int, default=None, help="保留天数（默认取配置）")
    parser.add_argument("--dry-run", action="store_true", help="只打印不删除")
    args = parser.parse_args()

    settings = get_settings()
    ttl = args.ttl_days if args.ttl_days is not None else settings.results_ttl_days

    logger.info("cleanup_results 启动: ttl=%d 天, dry_run=%s", ttl, args.dry_run)

    import asyncio

    dirs, rows = asyncio.run(cleanup(ttl_days=ttl, dry_run=args.dry_run))
    logger.info("完成: 清理目录 %d, 清理记录 %d", dirs, rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
