"""OpenCV 可选依赖包装。

opencv 只用于 GrabCut 兜底分割、seamlessClone 融合、形态学优化等增强路径；
缺失时相关能力自动降级，不影响服务启动与主链路出图。
"""

from __future__ import annotations

from typing import Any

import numpy as np

from app.logs import get_logger

logger = get_logger("app.utils.cv")

try:  # pragma: no cover - 取决于本机环境
    import cv2 as _cv2
except Exception as exc:  # noqa: BLE001 - ImportError / 二进制加载失败都要兜住
    _cv2 = None  # type: ignore[assignment]
    _CV_ERROR = str(exc)
else:
    _CV_ERROR = None


def cv_module() -> Any | None:
    """返回 cv2 模块，未安装时返回 None。"""
    return _cv2


def cv_available() -> tuple[bool, str | None]:
    if _cv2 is None:
        return False, f"opencv 不可用: {_CV_ERROR}"
    return True, None


def feather_mask(mask: np.ndarray, radius: int = 3) -> np.ndarray:
    """对掩码做高斯羽化；无 opencv 时用 PIL 实现。"""
    from PIL import Image

    if radius <= 0:
        return mask
    img = Image.fromarray(mask, mode="L")
    sigma = max(1.0, radius / 2.0)
    try:
        from PIL import ImageFilter

        img = img.filter(ImageFilter.GaussianBlur(radius=sigma))
    except Exception:  # noqa: BLE001
        pass
    return np.asarray(img, dtype=np.uint8)


def morph_close(mask: np.ndarray, kernel_size: int = 5) -> np.ndarray:
    if _cv2 is None:
        return mask
    kernel = _cv2.getStructuringElement(_cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    return _cv2.morphologyEx(mask, _cv2.MORPH_CLOSE, kernel)


def keep_largest_component(mask: np.ndarray) -> np.ndarray:
    """只保留最大连通域，去除分割噪声块。"""
    if _cv2 is None:
        return mask
    labels_count, labels, stats, _ = _cv2.connectedComponentsWithStats(
        (mask > 127).astype(np.uint8), connectivity=8
    )
    if labels_count <= 1:
        return mask
    areas = stats[1:, _cv2.CC_STAT_AREA]
    best = int(np.argmax(areas)) + 1
    return np.where(labels == best, 255, 0).astype(np.uint8)
