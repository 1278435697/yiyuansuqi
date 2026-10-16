"""人像分割入口：Provider 链式降级。

优先级 vitongpu -> u2net -> mediapipe_selfie -> heuristic，
任一环节失败只记 warning 并降级，绝不因权重/依赖缺失中断请求。
"""

from __future__ import annotations

import numpy as np

from app.logs import get_logger
from app.services.segmentation.base import SegmentResult
from app.services.segmentation.heuristic import HeuristicProvider
from app.services.segmentation.mediapipe_selfie import MediaPipeSelfieProvider
from app.services.segmentation.u2net import U2NetProvider
from app.services.segmentation.vitongpu import VitonGPUProvider
from app.utils.cv import keep_largest_component
from app.utils.imageio import normalize_mask

logger = get_logger("app.services.segmentation")

_CHAIN_ORDER = ("vitongpu", "u2net", "mediapipe_selfie", "heuristic")
_PROVIDERS = {
    "vitongpu": VitonGPUProvider,
    "u2net": U2NetProvider,
    "mediapipe_selfie": MediaPipeSelfieProvider,
    "heuristic": HeuristicProvider,
}
_instances: dict[str, object] = {}


def _provider(name: str):
    if name not in _instances:
        _instances[name] = _PROVIDERS[name]()
    return _instances[name]


def _sanity_check(mask: np.ndarray) -> tuple[bool, str]:
    """掩码质量底线：前景占比 1%~99%，且存在合理连通块。"""
    ratio = float((mask > 127).mean())
    if ratio < 0.01:
        return False, f"person_mask_too_small({ratio:.3f})"
    if ratio > 0.99:
        return False, f"person_mask_covers_whole_image({ratio:.3f})"
    return True, ""


def get_person_mask(rgb: np.ndarray) -> tuple[SegmentResult, list[str]]:
    """返回 (SegmentResult, warnings)。链尾 heuristic 恒可用，因此一定有掩码输出。"""
    warnings: list[str] = []
    for name in _CHAIN_ORDER:
        provider = _provider(name)
        ok, reason = provider.available()  # type: ignore[attr-defined]
        if not ok:
            warnings.append(f"segmentation_{name}_unavailable")
            logger.info("分割 Provider %s 跳过: %s", name, reason)
            continue
        try:
            result = provider.segment(rgb)  # type: ignore[attr-defined]
        except Exception as exc:  # noqa: BLE001 - 任意推理异常都需降级
            logger.warning("分割 Provider %s 推理异常: %s", name, exc)
            warnings.append(f"segmentation_{name}_error")
            continue

        result.person = normalize_mask(result.person)
        if name != "heuristic":
            result.person = keep_largest_component(result.person)
        passed, detail = _sanity_check(result.person)
        if not passed:
            logger.warning("分割 Provider %s 结果不可用: %s", name, detail)
            warnings.append(f"segmentation_{name}_low_quality:{detail}")
            continue
        if name != "vitongpu":
            warnings.append(f"segmentation_fallback_to_{name}")
        logger.info("人像分割采用 Provider=%s", result.provider)
        return result, warnings

    # 理论上不会走到（heuristic 恒可用），保底给中心竖条
    warnings.append("segmentation_all_failed_use_prior")
    from app.services.segmentation.heuristic import _center_prior_mask

    return SegmentResult(person=_center_prior_mask(rgb.shape), provider="prior_box"), warnings


def status() -> dict[str, object]:
    """供 /health 与 doctor 使用：逐 Provider 报告可用性。"""
    out: dict[str, object] = {}
    for name in _CHAIN_ORDER:
        provider = _provider(name)
        ok, reason = provider.available()  # type: ignore[attr-defined]
        out[name] = {"available": bool(ok), "reason": reason}
    return out


__all__ = ["SegmentResult", "get_person_mask", "status"]
