"""服饰素材库接口。

数据以 SQLite 为准（启动时由 seed_garments 从 index.json 写入），
数据库不可用或为空时回退读取磁盘 index.json，保证素材库永远可浏览。
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.api.deps import get_session
from app.db import repos
from app.errors import GarmentNotFoundError
from app.logs import get_logger
from app.schemas import GarmentOut, Keypoint, TraceCard
from app.services.garments import entry_to_output, static_url, trace_card_for

logger = get_logger("app.api.garments")

router = APIRouter()


def _to_keypoints(raw: list | None) -> list[Keypoint]:
    return [
        Keypoint(name=str(p["name"]), x=float(p["x"]), y=float(p["y"]))
        for p in (raw or [])
        if isinstance(p, dict) and {"name", "x", "y"} <= set(p)
    ]


def _orm_to_out(row) -> GarmentOut:
    return GarmentOut(
        id=row.id,
        name=row.name,
        dynasty=row.dynasty,
        category=row.category,  # type: ignore[arg-type]
        tags=list(row.tags or []),
        image_url=static_url(row.image_path),
        thumb_url=static_url(row.thumb_path or row.image_path),
        keypoints=_to_keypoints(row.keypoints),
        source_text=row.source_text or "",
        references=list(row.references or []),
    )


def _disk_fallback() -> list[GarmentOut]:
    from app.services.garments import load_index, valid_entries

    try:
        entries, _skipped = valid_entries(load_index())
    except Exception as exc:  # noqa: BLE001 - 素材读取失败不能打挂接口
        logger.warning("磁盘素材读取失败: %s", exc)
        return []
    items: list[GarmentOut] = []
    for entry in entries:
        try:
            items.append(GarmentOut(**entry_to_output(entry)))
        except Exception as exc:  # noqa: BLE001
            logger.warning("素材 %s 序列化失败: %s", entry.get("id"), exc)
    return items


@router.get("", response_model=list[GarmentOut], response_model_exclude_none=True)
@router.get("/", response_model=list[GarmentOut], response_model_exclude_none=True, include_in_schema=False)
async def list_garments(
    session=Depends(get_session),
    category: str | None = Query(default=None, description="top | dress | skirt | robe"),
    dynasty: str | None = Query(default=None, description="朝代筛选"),
    keyword: str | None = Query(default=None, max_length=32, description="名称模糊搜索"),
) -> list[GarmentOut]:
    try:
        rows = await repos.list_garments(
            session,
            category=category,
            dynasty=dynasty,
            keyword=keyword,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("素材库查询失败，回退磁盘索引: %s", exc)
        rows = []
    if not rows:
        items = _disk_fallback()
        if category:
            items = [item for item in items if item.category == category]
        if dynasty:
            items = [item for item in items if item.dynasty == dynasty]
        if keyword:
            items = [item for item in items if keyword in item.name]
        return items
    return [_orm_to_out(row) for row in rows]


@router.get("/{garment_id}", response_model=GarmentOut, response_model_exclude_none=True)
async def get_garment(garment_id: str, session=Depends(get_session)) -> GarmentOut:
    row = None
    try:
        row = await repos.get_garment(session, garment_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning("素材查询失败 id=%s: %s", garment_id, exc)
    if row is not None:
        return _orm_to_out(row)
    for item in _disk_fallback():
        if item.id == garment_id:
            return item
    raise GarmentNotFoundError()


@router.get("/{garment_id}/trace", response_model=TraceCard)
async def get_garment_trace(garment_id: str) -> TraceCard:
    """史料溯源卡片数据（原文 + 文献出处）。"""
    return trace_card_for(garment_id)


__all__ = ["router"]
