"""虚拟试穿接口。

同一能力提供两种调用方式：
- `POST /tryon`：JSON + Base64（前端主用，压缩后体积小）
- `POST /tryon/upload`：multipart/form-data（等价，便于 curl 与文档演示）
另有 `POST /tryon/batch`（多套连续试穿，加分项）与 `GET /tryon/{task_id}`（结果查询）。
"""

from __future__ import annotations

import time

from fastapi import APIRouter, Depends, File, Form, UploadFile
from starlette.concurrency import run_in_threadpool

from app.api.deps import NEW_TASK_ID, get_session
from app.errors import AppError, InvalidImageError, TryOnFailedError
from app.logs import get_logger
from app.schemas import BatchTryOnRequest, TryOnRequest, TryOnResult
from app.services import history
from app.services.garments import GarmentAsset, asset_from_bytes, load_asset
from app.services.pipeline import PipelineOutput, find_cached_task, run_tryon
from app.services.segmentation import status as segmentation_status
from app.utils.imageio import load_rgb, strip_data_uri
from app.utils.upload import max_bytes, read_upload_limited

logger = get_logger("app.api.tryon")

router = APIRouter()


def _load_person_rgb(payload_b64: str):
    """Base64 → RGB，同时返回原始字节用于缓存比对。"""
    raw = strip_data_uri(payload_b64)
    return load_rgb(raw, label="人像图"), raw


def _pick_garment(
    garment_id: str | None, garment_b64: str | None
) -> tuple[GarmentAsset, str]:
    """素材库服饰优先；临时上传服饰使用 adhoc 身份，不入素材库。"""
    if garment_id:
        return load_asset(garment_id), garment_id
    assert garment_b64 is not None
    asset = asset_from_bytes(strip_data_uri(garment_b64), gid="adhoc")
    return asset, "adhoc"


async def _execute(
    *,
    session,
    person_rgb,
    garment: GarmentAsset,
    garment_ref: str,
    quality: str,
    force_refresh: bool = False,
) -> TryOnResult:
    """跑一条完整流水线：磁盘缓存命中直接复用，否则推理并落库。

    流水线是确定性的，同一（人像, 服饰, 画质）必然得到同一张图，
    所以 `force_refresh` 必须显式跳过查表，否则“再点一次”永远看不出变化。
    """
    if force_refresh:
        logger.info("跳过磁盘缓存重算 garment=%s（force_refresh）", garment_ref)
    else:
        cached_id = await run_in_threadpool(find_cached_task, person_rgb, garment, quality)
        if cached_id:
            try:
                cached = await history.get_record_result(session, cached_id)
                cached.warnings = [*cached.warnings, "result_from_cache"]
                logger.info("命中磁盘缓存 task=%s garment=%s", cached_id, garment_ref)
                return cached
            except AppError as exc:
                logger.warning("缓存记录读取失败 task=%s: %s", cached_id, exc)

    task_id = NEW_TASK_ID()
    started = time.perf_counter()
    try:
        out: PipelineOutput = await run_in_threadpool(
            lambda: run_tryon(
                task_id=task_id, person_rgb=person_rgb, garment=garment, quality=quality
            )
        )
    except TryOnFailedError as exc:
        # 失败也留痕，便于前端展示与答辩复盘
        duration = round(time.perf_counter() - started, 4)
        try:
            await history.save_record(
                session,
                PipelineOutput(
                    task_id=task_id,
                    backend_used="none",
                    result_url="",
                    person_url="",
                    person_mask_url=None,
                    pose_overlay_url=None,
                    garment_warp_url=None,
                    warnings=[f"task_failed:{exc.error_code}"],
                    timings={"total": duration},
                ),
                garment_id=None if garment_ref == "adhoc" else garment_ref,
                quality=quality,
                status="failed",
            )
        except Exception as save_exc:  # noqa: BLE001 - 失败记录写不进去不应改变原异常
            logger.warning("失败记录入库异常: %s", save_exc)
        raise

    result = history.to_result(out, garment_ref)
    try:
        await history.save_record(
            session,
            out,
            garment_id=None if garment_ref == "adhoc" else garment_ref,
            quality=quality,
        )
    except Exception as exc:  # noqa: BLE001 - 落库失败不影响出图
        logger.warning("试穿记录入库失败 task=%s: %s", task_id, exc)
        result.warnings = [*result.warnings, "history_save_failed"]
    # 告警在落库之后才贴，避免 `cache_bypassed` 被写进记录、下次命中缓存时误报
    if force_refresh:
        result.warnings = [*result.warnings, "cache_bypassed"]
    return result


@router.post("", response_model=TryOnResult)
@router.post("/", response_model=TryOnResult, include_in_schema=False)
async def tryon(payload: TryOnRequest, session=Depends(get_session)) -> TryOnResult:
    person_rgb, _person_raw = _load_person_rgb(payload.person_image)
    garment, garment_ref = await run_in_threadpool(
        _pick_garment, payload.garment_id, payload.garment_image
    )
    return await _execute(
        session=session,
        person_rgb=person_rgb,
        garment=garment,
        garment_ref=garment_ref,
        quality=payload.quality,
        force_refresh=payload.force_refresh,
    )


@router.post("/upload", response_model=TryOnResult)
async def tryon_upload(
    person_file: UploadFile = File(..., description="真人照片"),
    garment_id: str | None = Form(default=None),
    garment_file: UploadFile = File(default=None, description="临时服饰图（与 garment_id 二选一）"),
    quality: str = Form(default="fast"),
    force_refresh: bool = Form(default=False, description="跳过磁盘缓存重算一次"),
    session=Depends(get_session),
) -> TryOnResult:
    if not garment_id and garment_file is None:
        raise InvalidImageError("garment_id 与 garment_file 必须至少提供一个")
    if quality not in {"fast", "hd"}:
        raise InvalidImageError(f"未知的 quality：{quality}")

    limit = max_bytes()
    person_raw = await read_upload_limited(person_file, label="人像图", max_bytes=limit)
    person_rgb = load_rgb(person_raw, label="人像图")

    if garment_id:
        garment, garment_ref = load_asset(garment_id), garment_id
    else:
        assert garment_file is not None
        garment_raw = await read_upload_limited(garment_file, label="服饰图", max_bytes=limit)
        # asset_from_bytes 内部会校验真实格式，伪造扩展名会被拒绝
        garment = asset_from_bytes(garment_raw, gid="adhoc")
        garment_ref = "adhoc"

    return await _execute(
        session=session,
        person_rgb=person_rgb,
        garment=garment,
        garment_ref=garment_ref,
        quality=quality,
        force_refresh=force_refresh,
    )


@router.post("/batch", response_model=list[TryOnResult])
async def tryon_batch(payload: BatchTryOnRequest, session=Depends(get_session)) -> list[TryOnResult]:
    """批量连续试穿：同一张真人照依次换多套服饰。单个失败不影响整体。"""
    person_rgb, _person_raw = _load_person_rgb(payload.person_image)
    results: list[TryOnResult] = []
    for gid in payload.garment_ids:
        try:
            garment, garment_ref = await run_in_threadpool(_pick_garment, gid, None)
            results.append(
                await _execute(
                    session=session,
                    person_rgb=person_rgb,
                    garment=garment,
                    garment_ref=garment_ref,
                    quality=payload.quality,
                    force_refresh=payload.force_refresh,
                )
            )
        except AppError as exc:
            logger.warning("批量试穿单件失败 garment=%s: %s", gid, exc.message)
            results.append(
                TryOnResult(
                    task_id=NEW_TASK_ID(),
                    status="failed",
                    backend_used="none",
                    warnings=[f"batch_item_failed:{gid}"],
                    error_code=exc.error_code,
                    message=exc.message,
                )
            )
    return results


@router.get("/meta/segmentation", response_model=dict)
async def segmentation_meta() -> dict:
    """预处理 provider 状态，供前端调试面板展示。"""
    return {"segmentation": segmentation_status()}


@router.get("/{task_id}", response_model=TryOnResult)
async def get_task(task_id: str, session=Depends(get_session)) -> TryOnResult:
    return await history.get_record_result(session, task_id)


__all__ = ["router"]
