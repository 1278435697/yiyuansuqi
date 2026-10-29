"""试穿流水线编排：上传校验 → 预处理 → 推理 → 后处理 → 落盘。

CPU 密集的推理放在线程池中执行（run_in_threadpool），避免阻塞事件循环。
"""

from __future__ import annotations

import hashlib
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from app.config import get_settings
from app.errors import TryOnFailedError
from app.logs import get_logger
from app.services import postprocess, segmentation, vton
from app.services.garments import GarmentAsset, load_asset
from app.services.pose import draw_pose_overlay, estimate_pose
from app.services.vton.base import TryOnContext
from app.utils.imageio import (
    load_rgb,
    load_rgb_from_base64,
    mask_to_overlay,
    strip_data_uri,
    save_jpg,
    save_png,
)
from app.utils.static import static_for

logger = get_logger("app.services.pipeline")


@dataclass
class PipelineOutput:
    task_id: str
    backend_used: str
    result_url: str
    person_url: str
    person_mask_url: str | None
    pose_overlay_url: str | None
    garment_warp_url: str | None
    pose_keypoints: list[dict] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    timings: dict[str, float] = field(default_factory=dict)
    from_cache: bool = False


def _cache_key(person_rgb: np.ndarray, garment: GarmentAsset, quality: str) -> str:
    """缓存键同时纳入服饰图像与掩码，避免临时上传服饰（id 恒为 adhoc）互相误命中。

    云端呈现图（`cloud_cloth`）也要进键：它不改素材本身、只改发给厂商的那张图，
    漏了它的话给某件衣服补一张平铺图，线上仍会返回按展陈形算出来的旧结果。
    """
    digest = hashlib.sha256()
    digest.update(np.ascontiguousarray(person_rgb).tobytes())
    digest.update(np.ascontiguousarray(garment.image).tobytes())
    digest.update(np.ascontiguousarray(garment.mask).tobytes())
    if garment.cloud_cloth is not None:
        digest.update(b"cloud_cloth:")
        digest.update(np.ascontiguousarray(garment.cloud_cloth).tobytes())
    digest.update(garment.id.encode("utf-8"))
    digest.update(quality.encode("utf-8"))
    return digest.hexdigest()[:32]


def _stage(name: str, timings: dict[str, float], started: float) -> float:
    timings[name] = round(time.perf_counter() - started, 4)
    return time.perf_counter()


def run_tryon(
    *,
    task_id: str,
    person_rgb: np.ndarray,
    garment: GarmentAsset,
    quality: str,
) -> PipelineOutput:
    """同步执行整条流水线（由 API 层放入线程池调用）。"""
    settings = get_settings()
    timings: dict[str, float] = {}
    warnings: list[str] = []
    started = time.perf_counter()

    out_dir = settings.results_dir / task_id
    out_dir.mkdir(parents=True, exist_ok=True)

    # ---------- 1. 人像分割 ----------
    seg, seg_warnings = segmentation.get_person_mask(person_rgb)
    warnings.extend(seg_warnings)
    started = _stage("segmentation", timings, started)

    # ---------- 2. 姿态与关键点 ----------
    pose, pose_mask, pose_warnings = estimate_pose(
        person_rgb, seg.person, seg.clothes
    )
    warnings.extend(pose_warnings)
    if pose_mask is not None and float((pose_mask > 127).mean()) > float((seg.person > 127).mean()) * 1.3:
        # MediaPipe 自带的分割更完整时优先采用
        seg.person = pose_mask
        warnings.append("segmentation_replaced_by_pose_mask")
    started = _stage("pose", timings, started)

    # ---------- 3. 试穿推理（可插拔后端） ----------
    ctx = TryOnContext(
        person_rgb=person_rgb,
        person_mask=seg.person,
        pose=pose,
        garment=garment,
        quality=quality,
        out_dir=out_dir,
        clothes_mask=seg.clothes,
        arms_mask=seg.extra.get("arms"),
        head_mask=seg.extra.get("head"),
        extra=dict(seg.extra),
    )
    try:
        output, vton_warnings = vton.run(ctx)
    except TryOnFailedError:
        raise
    except Exception as exc:  # noqa: BLE001
        logger.exception("试穿推理未预期失败")
        raise TryOnFailedError(detail=str(exc)) from exc
    warnings.extend(vton_warnings)
    started = _stage("inference", timings, started)

    # ---------- 4. 后处理 ----------
    refined, pp_notes = postprocess.refine(
        output.result, person_rgb, output.warped_mask, seg.person, quality=quality
    )
    warnings.extend(pp_notes)
    started = _stage("postprocess", timings, started)

    # ---------- 5. 落盘 ----------
    result_path = save_jpg(refined, out_dir / "result.jpg", quality=92)
    # 用户原图落到私密目录（不在静态挂载下），只能通过 API 端点访问
    private_person_dir = settings.person_sources_dir / task_id
    private_person_dir.mkdir(parents=True, exist_ok=True)
    person_path = save_jpg(person_rgb, private_person_dir / "person_source.jpg", quality=90)
    mask_path = save_png(mask_to_overlay(seg.person), out_dir / "person_mask.png")
    pose_path = save_png(draw_pose_overlay(person_rgb, pose), out_dir / "pose_overlay.png")
    warp_path: Path | None = None
    if output.warped_rgb is not None:
        warp_path = save_png(output.warped_rgb, out_dir / "garment_warp.png")
    started = _stage("save", timings, started)
    timings["total"] = round(sum(timings.values()), 4)

    # 磁盘缓存标记：同一 person + garment + quality 下次直接复用
    if settings.enable_disk_cache:
        import json

        marker = out_dir / f"cache_{_cache_key(person_rgb, garment, quality)}.json"
        marker.write_text(
            json.dumps({"task_id": task_id, "garment_id": garment.id, "quality": quality}),
            encoding="utf-8",
        )

    logger.info(
        "试穿完成 task=%s backend=%s 耗时=%s warnings=%d",
        task_id,
        output.backend,
        {k: round(v, 3) for k, v in timings.items()},
        len(warnings),
    )
    # person_url 指向内部 API 端点，不走静态文件服务
    person_url = f"{settings.api_prefix}/history/{task_id}/person-source"
    return PipelineOutput(
        task_id=task_id,
        backend_used=output.backend,
        result_url=static_for(result_path),
        person_url=person_url,
        person_mask_url=static_for(mask_path),
        pose_overlay_url=static_for(pose_path),
        garment_warp_url=static_for(warp_path) if warp_path else None,
        pose_keypoints=pose.to_output(),
        warnings=warnings,
        timings=timings,
    )


def run_tryon_from_bytes(
    *, task_id: str, person_bytes: bytes, garment: GarmentAsset, quality: str
) -> PipelineOutput:
    person_rgb = load_rgb(person_bytes, label="人像图")
    return run_tryon(task_id=task_id, person_rgb=person_rgb, garment=garment, quality=quality)


def run_tryon_from_base64(*, task_id: str, person_b64: str, garment: GarmentAsset, quality: str) -> PipelineOutput:
    person_rgb = load_rgb_from_base64(person_b64, label="人像图")
    return run_tryon(task_id=task_id, person_rgb=person_rgb, garment=garment, quality=quality)


def find_cached_task(person_rgb: np.ndarray, garment: GarmentAsset, quality: str) -> str | None:
    """同一 person + garment + quality 已出过图时返回既有 task_id（磁盘缓存，无内存缓存）。"""
    settings = get_settings()
    if not settings.enable_disk_cache:
        return None
    key = _cache_key(person_rgb, garment, quality)
    matches = sorted(settings.results_dir.glob(f"*/cache_{key}.json"))
    if not matches:
        return None
    task_id = matches[0].parent.name
    if not (settings.results_dir / task_id / "result.jpg").is_file():
        return None
    return task_id


def cached_task_id(person_payload: str | bytes, garment_id: str, quality: str) -> str | None:
    """便捷入口：入参可为 Base64 字符串或原始字节。"""
    raw = (
        strip_data_uri(person_payload)
        if isinstance(person_payload, str)
        else person_payload
    )
    try:
        person_rgb = load_rgb(raw, label="人像图")
    except Exception:  # noqa: BLE001 - 缓存查询失败不应影响主流程
        return None
    return find_cached_task(person_rgb, load_asset(garment_id), quality)


__all__ = [
    "PipelineOutput",
    "cached_task_id",
    "find_cached_task",
    "run_tryon",
    "run_tryon_from_base64",
    "run_tryon_from_bytes",
]
