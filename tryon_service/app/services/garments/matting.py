"""纯色底服饰抠图：让「真实照片素材」无需人工抠图即可入库。

白底/浅灰底商品图与馆藏翻拍图的共同特点是背景近似常量，
因此用「边框采样估背景色 → 距离图 Otsu 二值化 → 形态学清理 → 填洞 → 最大连通域」
即可得到比 GrabCut 中心先验干净得多的服饰掩码。
只依赖 numpy/scipy，opencv 缺失时降级为不做形态学闭运算。
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage

from app.logs import get_logger
from app.utils.cv import keep_largest_component, morph_close
from app.utils.imageio import normalize_mask

logger = get_logger("app.services.garments.matting")

_MIN_FOREGROUND_RATIO = 0.02  # 前景占比低于 2% 视为抠图失败
_BORDER_RATIO = 0.015  # 边框采样带宽
_EDGE_BAND_RATIO = 0.05  # 边缘「弱对比剔除」带宽（水印/角标常贴画面四边）
_EDGE_STRONG_DISTANCE = 70.0  # 边缘带上只有色差强于该值的像素才当作真实服饰


def _drop_weak_border(mask: np.ndarray, distance: np.ndarray, threshold: float) -> np.ndarray:
    """去掉贴在画面四边的弱对比前景（版权水印、角标、拍台阴影）。

    这些区域与背景色差往往刚过 Otsu 阈值，且与服饰主体被同一条阴影连成一整块，
    `keep_largest_component` 无法分离；而真正伸出画幅边缘的衣袖/裙摆色差很强，
    因此只清除边缘带内 `distance < max(2*threshold, 70)` 的像素，再交给后续最大连通域。
    """
    h, w = mask.shape[:2]
    band = max(4, int(min(h, w) * _EDGE_BAND_RATIO))
    weak = distance < max(threshold * 2.0, _EDGE_STRONG_DISTANCE)
    edge = np.zeros_like(mask, dtype=bool)
    edge[:band] = edge[-band:] = True
    edge[:, :band] = edge[:, -band:] = True
    # 必须回到 uint8：np.where 会因 Python int 0 把掩码提升为 int32，cv2.morphologyEx 直接报错
    return np.where(edge & weak, 0, mask).astype(np.uint8)


def _border_band(rgb: np.ndarray, band: int) -> np.ndarray:
    h, w = rgb.shape[:2]
    return np.concatenate(
        [
            rgb[:band].reshape(-1, 3),
            rgb[-band:].reshape(-1, 3),
            rgb[:, :band].reshape(-1, 3),
            rgb[:, -band:].reshape(-1, 3),
        ],
        axis=0,
    )


def estimate_background(rgb: np.ndarray) -> tuple[np.ndarray, float]:
    """返回 (背景中位色, 边框色离散度)。离散度越小说明背景越「纯」。"""
    band = max(2, int(min(rgb.shape[:2]) * _BORDER_RATIO))
    samples = _border_band(rgb, band).astype(np.float32)
    center = np.median(samples, axis=0)
    spread = float(np.percentile(np.linalg.norm(samples - center, axis=1), 90))
    return center.astype(np.float32), spread


def is_solid_background(rgb: np.ndarray, *, max_spread: float = 42.0) -> bool:
    """判断是否近似纯色底（可安全走抠图路径）。"""
    _, spread = estimate_background(rgb)
    return spread <= max_spread


def _otsu_threshold(values: np.ndarray) -> float:
    """标准 Otsu：遍历直方图取类间方差最大的分箱中心。"""
    flat = np.clip(values, 0, None).astype(np.float32).ravel()
    if flat.size == 0:
        return 0.0
    hist, edges = np.histogram(flat, bins=128)
    centers = ((edges[:-1] + edges[1:]) / 2).astype(np.float64)
    weights = hist.astype(np.float64) / float(hist.sum())
    w0 = np.cumsum(weights)
    if w0[-1] <= 0:
        return float(flat.max())
    m0 = np.cumsum(weights * centers) / np.maximum(w0, 1e-12)
    mean_total = float((weights * centers).sum() / max(float(w0[-1]), 1e-12))
    w1 = 1.0 - w0
    with np.errstate(invalid="ignore"):
        variance_between = w0 * w1 * (mean_total - m0) ** 2
    valid = np.isfinite(variance_between) & (w0 > 0) & (w1 > 0)
    if not valid.any():
        return float(flat.max())
    return float(centers[int(np.nanargmax(np.where(valid, variance_between, np.nan)))])


def _clean_mask(mask: np.ndarray, distance: np.ndarray, threshold: float) -> np.ndarray:
    """边缘弱对比剔除 → 闭运算 → 填洞 → 最大连通域。"""
    mask = normalize_mask(mask)
    mask = _drop_weak_border(mask, distance, threshold)
    mask = morph_close(mask, kernel_size=7)
    mask = normalize_mask(ndimage.binary_fill_holes(mask > 127).astype(np.uint8) * 255)
    return keep_largest_component(mask)


def cutout_solid_background(rgb: np.ndarray) -> np.ndarray:
    """纯色底 → 服饰前景掩码 (H,W) uint8 0/255。失败时返回全 0 掩码。"""
    h, w = rgb.shape[:2]
    empty = np.zeros((h, w), dtype=np.uint8)
    background, _ = estimate_background(rgb)
    distance = np.linalg.norm(rgb.astype(np.float32) - background, axis=2)

    threshold = _otsu_threshold(distance)
    # Otsu 在「背景极纯 + 服饰占满画面」时会偏低，给一个绝对下限防把噪点当衣服
    threshold = max(threshold, 28.0)
    foreground = distance > threshold

    if not foreground.any():
        logger.debug("纯色底抠图未找到前景（threshold=%.1f）", threshold)
        return empty
    if foreground.mean() > 0.9:
        # 背景与服饰颜色接近（如米色裙 + 白墙），交给上层降级
        return empty

    mask = _clean_mask(np.where(foreground, 255, 0), distance, threshold)
    ratio = float((mask > 127).mean())
    if ratio < _MIN_FOREGROUND_RATIO:
        logger.debug("纯色底抠图前景过小（%.3f），判定失败", ratio)
        return empty

    # 二次收紧：商品图下方的拍台投影与背景色差极小，会在裙摆/衣摆下「糊」出一圈灰边，
    # 贴图时会变成横贯服饰底部的亮块。用前景自身色差分布的低位分位数抬升阈值，
    # 对浅色服饰同样安全（它整体色差都低，分位数不会显著高于原阈值）。
    inside = distance[mask > 127]
    if inside.size > 512:
        tighter = float(np.percentile(inside, 18))
        if threshold < tighter < threshold * 3.0:
            refined = _clean_mask(np.where(distance > tighter, 255, 0), distance, tighter)
            refined_ratio = float((refined > 127).mean())
            if _MIN_FOREGROUND_RATIO <= refined_ratio and refined_ratio >= ratio * 0.55:
                logger.debug("抠图阈值收紧 %.1f → %.1f（%.3f → %.3f）", threshold, tighter, ratio, refined_ratio)
                mask = refined
    return mask


__all__ = [
    "cutout_solid_background",
    "estimate_background",
    "is_solid_background",
]
