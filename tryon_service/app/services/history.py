"""试穿记录：把流水线输出转成 API 响应并落库。"""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.db import models, repos
from app.logs import get_logger
from app.schemas import TraceCard, TryOnRecordOut, TryOnResult
from app.services.garments import trace_card_for
from app.services.pipeline import PipelineOutput

logger = get_logger("app.services.history")


def to_result(out: PipelineOutput, garment_id: str, status: str = "succeeded") -> TryOnResult:
    trace: TraceCard | None = None
    if garment_id != "adhoc":
        try:
            trace = trace_card_for(garment_id)
        except Exception as exc:  # noqa: BLE001 - 溯源卡片缺失不应影响主结果
            logger.warning("溯源卡片读取失败 garment=%s: %s", garment_id, exc)
            trace = None
    return TryOnResult(
        task_id=out.task_id,
        status=status,  # type: ignore[arg-type]
        result_url=out.result_url,
        person_mask_url=out.person_mask_url,
        pose_overlay_url=out.pose_overlay_url,
        garment_warp_url=out.garment_warp_url,
        backend_used=out.backend_used,
        warnings=out.warnings,
        timings=out.timings,
        trace_card=trace,
    )


async def save_record(
    session: AsyncSession,
    out: PipelineOutput,
    *,
    garment_id: str | None,
    quality: str,
    status: str = "succeeded",
) -> models.TryOnRecord:
    payload = {
        "task_id": out.task_id,
        "garment_id": garment_id,
        "person_url": out.person_url,
        "result_url": out.result_url,
        "mask_url": out.person_mask_url,
        "pose_url": out.pose_overlay_url,
        "warp_url": out.garment_warp_url,
        "backend_used": out.backend_used,
        "quality": quality,
        "status": status,
        "warnings": out.warnings,
        "timings": out.timings,
    }
    return await repos.add_record(session, payload)


async def list_records(session: AsyncSession, *, limit: int, offset: int) -> tuple[list[TryOnRecordOut], int]:
    records, total = await repos.list_records(session, limit=limit, offset=offset)
    out: list[TryOnRecordOut] = []
    for record in records:
        out.append(
            TryOnRecordOut(
                id=record.id,
                task_id=record.task_id,
                garment_id=record.garment_id,
                garment_name=record.garment.name if record.garment else None,
                person_url=record.person_url or "",
                result_url=record.result_url or "",
                backend_used=record.backend_used,
                quality=record.quality,
                warnings=list(record.warnings or []),
                created_at=record.created_at.isoformat() if record.created_at else "",
            )
        )
    return out, total


async def get_record_result(session: AsyncSession, task_id: str) -> TryOnResult:
    from app.errors import TaskNotFoundError

    record = await repos.get_record_by_task(session, task_id)
    if record is None:
        raise TaskNotFoundError()
    return TryOnResult(
        task_id=record.task_id,
        status=record.status,  # type: ignore[arg-type]
        result_url=record.result_url,
        person_mask_url=record.mask_url,
        pose_overlay_url=record.pose_url,
        garment_warp_url=record.warp_url,
        backend_used=record.backend_used,
        warnings=list(record.warnings or []),
        timings=dict(record.timings or {}),
        trace_card=trace_card_for(record.garment_id) if record.garment_id else None,
    )


__all__ = ["get_record_result", "list_records", "save_record", "to_result"]
