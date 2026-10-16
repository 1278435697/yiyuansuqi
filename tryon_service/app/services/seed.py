"""素材入库种子：把 data/garments/index.json 中校验通过的素材 upsert 到数据库。

启动时（lifespan）与 `scripts/seed_garments.py` 共用此逻辑，
保证 `tryon_record.garment_id` 外键始终能命中已有素材。
"""

from __future__ import annotations

from app.db import repos
from app.db.base import session_factory
from app.logs import get_logger
from app.services.garments import load_index, to_db_payload, valid_entries

logger = get_logger("app.services.seed")


async def seed_garments(*, force: bool = False) -> tuple[int, list[str]]:
    """返回 (写入条数, 跳过原因列表)。异常不外抛——种子失败不应阻止服务启动。"""
    try:
        entries, skipped = valid_entries(load_index())
    except Exception as exc:  # noqa: BLE001
        logger.error("读取素材索引失败: %s", exc)
        return 0, [f"index_read_failed:{exc}"]

    if not entries:
        logger.warning(
            "没有可用素材，请先运行 `python -m scripts.gen_sample_garments` 生成示例素材"
        )
        return 0, skipped

    written = 0
    async with session_factory()() as session:
        try:
            existing_ids = {row.id for row in await repos.list_garments(session)}
        except Exception as exc:  # noqa: BLE001 - 建表可能尚未完成
            logger.error("素材表不可用，跳过种子: %s", exc)
            return 0, [*skipped, f"db_unavailable:{exc}"]

        for entry in entries:
            if not force and entry["id"] in existing_ids:
                continue
            try:
                await repos.upsert_garment(session, to_db_payload(entry))
                written += 1
            except Exception as exc:  # noqa: BLE001 - 单条失败不影响其余素材
                logger.warning("素材 %s 入库失败: %s", entry.get("id"), exc)
                skipped.append(f"{entry.get('id')}: 入库失败")

    logger.info("素材种子完成：写入/更新 %d 条，跳过 %d 条", written, len(skipped))
    return written, skipped


__all__ = ["seed_garments"]
