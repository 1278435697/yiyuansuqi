"""健康检查：逐项报告依赖可用性，供前端启动自检与答辩演示。"""

from __future__ import annotations

import importlib.util

from fastapi import APIRouter, Depends

from app import __version__
from app.api.deps import get_session
from app.config import get_settings
from app.db import repos
from app.logs import get_logger
from app.schemas import HealthOut
from app.services import pose, segmentation, vton

logger = get_logger("app.api.health")

router = APIRouter()


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ValueError):  # pragma: no cover - 极端环境
        return False


def _torch_status() -> dict[str, object]:
    """torch / CUDA 可用性，任何异常都归一为不可用而非 500。"""
    if not _module_available("torch"):
        return {"available": False, "reason": "torch_not_installed"}
    try:
        import torch

        cuda = bool(torch.cuda.is_available()) and not get_settings().force_cpu
        return {
            "available": True,
            "cuda": cuda,
            "version": str(torch.__version__),
            "device_count": int(torch.cuda.device_count()) if cuda else 0,
            "reason": None if cuda else "cuda_unavailable",
        }
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "cuda": False, "reason": f"torch_import_error:{exc}"}


def _opencv_status() -> dict[str, object]:
    from app.utils.cv import cv_module

    cv2 = cv_module()
    if cv2 is None:
        return {"available": False, "reason": "opencv_not_installed"}
    return {"available": True, "version": str(getattr(cv2, "__version__", "unknown"))}


def _onnx_status() -> dict[str, object]:
    if not _module_available("onnxruntime"):
        return {"available": False, "reason": "onnxruntime_not_installed"}
    try:
        import onnxruntime as ort

        return {"available": True, "version": str(ort.__version__), "providers": list(ort.get_available_providers())}
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "reason": f"onnxruntime_error:{exc}"}


@router.get("", response_model=HealthOut)
@router.get("/", response_model=HealthOut, include_in_schema=False)
async def health(session=Depends(get_session)) -> HealthOut:
    settings = get_settings()
    backend, fallback_reason = vton.resolve("auto")
    backend_name = getattr(backend, "name", "unknown")

    seg_status = segmentation.status()
    pose_status = pose.status()
    torch_status = _torch_status()

    components: dict[str, object] = {
        "segmentation": seg_status,
        "pose": pose_status,
        "vton": vton.status(),
        "torch": torch_status,
        "opencv": _opencv_status(),
        "onnxruntime": _onnx_status(),
        "weights": {
            "vitongpu_onnx": {
                "path": str(settings.vitongpu_onnx),
                "exists": bool(settings.vitongpu_onnx and settings.vitongpu_onnx.is_file()),
            },
            "u2net_onnx": {
                "path": str(settings.u2net_onnx),
                "exists": bool(
                    settings.u2net_onnx
                    and any(
                        p.is_file()
                        for p in (
                            settings.u2net_onnx,
                            settings.u2net_onnx.with_name("u2netp.onnx"),
                        )
                    )
                ),
            },
            "hrviton_ckpt_dir": {
                "path": str(settings.hrviton_ckpt_dir),
                "exists": bool(settings.hrviton_ckpt_dir and settings.hrviton_ckpt_dir.is_dir()),
            },
        },
        "disk_cache": settings.enable_disk_cache,
    }

    garments_count = 0
    db_ok = True
    try:
        garments_count = await repos.count_garments(session)
    except Exception as exc:  # noqa: BLE001 - 数据库故障时健康检查仍要返回
        db_ok = False
        logger.warning("素材计数查询失败: %s", exc)
    components["database"] = {
        "available": db_ok,
        "driver": settings.database_url.split("://")[0],
        "garments_count": garments_count,
    }

    seg_best = next(
        (name for name, info in seg_status.items() if info["available"]),
        None,
    )
    pose_available = bool(pose_status.get("mediapipe_pose", {}).get("available"))
    degraded = (not pose_available) or seg_best in (None, "heuristic")
    gpu_available = bool(torch_status.get("cuda", False))

    return HealthOut(
        status="degraded" if degraded else "ok",
        version=__version__,
        vton_backend_configured=settings.vton_backend,
        vton_backend_resolved=backend_name,
        fallback_reason=fallback_reason,
        gpu_available=gpu_available,
        components=components,
        garments_count=garments_count,
    )


__all__ = ["router"]
