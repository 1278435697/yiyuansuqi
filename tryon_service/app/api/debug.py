"""调试/截图元数据接口。

前端 `utils/snapshot.ts` 截图落盘时，把这里的 JSON 一并写入 `oneoff/` 目录，
作为答辩材料的「页面骨架 + 运行环境」证据（不引入 Playwright）。
"""

from __future__ import annotations

import platform
import sys

from fastapi import APIRouter

from app import __version__
from app.api.deps import NEW_TASK_ID
from app.config import get_settings
from app.services import pose, segmentation, vton
from app.services.garments import load_index, valid_entries

router = APIRouter()


def _skeleton_payload() -> dict:
    settings = get_settings()
    backend, fallback_reason = vton.resolve("auto")
    try:
        entries, skipped = valid_entries(load_index())
    except Exception as exc:  # noqa: BLE001
        entries, skipped = [], [f"index_read_failed:{exc}"]
    return {
        "request_id": NEW_TASK_ID(),
        "app": {"name": settings.app_name, "version": __version__},
        "python": {
            "version": sys.version.split()[0],
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
        },
        "runtime": {
            "vton_backend_configured": settings.vton_backend,
            "vton_backend_resolved": getattr(backend, "name", "unknown"),
            "fallback_reason": fallback_reason,
            "force_cpu": settings.force_cpu,
            "output_long_side": settings.output_long_side,
            "max_upload_mb": settings.max_upload_mb,
            "enable_disk_cache": settings.enable_disk_cache,
            "database_driver": settings.database_url.split("://")[0],
        },
        "providers": {
            "segmentation": segmentation.status(),
            "pose": pose.status(),
            "vton": vton.status(),
        },
        "garments": {
            "count": len(entries),
            "skipped": skipped,
            "categories": sorted({str(e.get("category")) for e in entries}),
            "dynasties": sorted({str(e.get("dynasty")) for e in entries}),
        },
        "pipeline_steps": [
            "前端压缩上传（长边≤1024 / JPEG 0.85）",
            "人像分割（Provider 链）",
            "人体姿态 17 关键点（COCO）",
            "服饰 9 关键点 → 人体锚点 TPS 变形",
            "遮挡还原 + 色彩迁移 + 边缘羽化",
            "结果落盘 + 记录入库 + 溯源卡片",
        ],
    }


@router.get("/skeleton")
async def skeleton_get() -> dict:
    return _skeleton_payload()


@router.post("/skeleton")
async def skeleton_post() -> dict:
    # 与 GET 等价，兼容项目书中写的 POST /debug/skeleton
    return _skeleton_payload()


__all__ = ["router"]
