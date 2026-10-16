"""后处理：边缘羽化修复 + 轻度降噪 + 可选局部锐化。

原则：只处理合成边界窄带，不做全局平滑（会毁掉布料纹理），
不改动人体轮廓以外的原始像素。
"""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageFilter

from app.logs import get_logger
from app.utils.cv import cv_module

logger = get_logger("app.services.postprocess")


def _edge_band(mask: np.ndarray, width: int = 3) -> np.ndarray:
    """返回掩码边界窄带 (H,W) float32 in [0,1]。"""
    binary = (mask > 127).astype(np.uint8) * 255
    cv2 = cv_module()
    if cv2 is not None:
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (width * 2 + 1, width * 2 + 1))
        dilated = cv2.dilate(binary, kernel, iterations=1)
        eroded = cv2.erode(binary, kernel, iterations=1)
        band = np.clip(dilated.astype(np.int16) - eroded.astype(np.int16), 0, 255).astype(np.uint8)
    else:
        img = Image.fromarray(binary, mode="L")
        dilated = np.asarray(img.filter(ImageFilter.MaxFilter(size=width * 2 + 1)), dtype=np.uint8)
        eroded = np.asarray(img.filter(ImageFilter.MinFilter(size=width * 2 + 1)), dtype=np.uint8)
        band = np.clip(dilated.astype(np.int16) - eroded.astype(np.int16), 0, 255).astype(np.uint8)
    return band.astype(np.float32) / 255.0


def _blur_variant(rgb: np.ndarray, radius: float) -> np.ndarray:
    img = Image.fromarray(rgb)
    return np.asarray(img.filter(ImageFilter.GaussianBlur(radius=radius)), dtype=np.uint8)


def _sharpen(rgb: np.ndarray, amount: float = 0.35) -> np.ndarray:
    cv2 = cv_module()
    if cv2 is None:
        img = Image.fromarray(rgb)
        return np.asarray(img.filter(ImageFilter.UnsharpMask(radius=1.2, percent=90, threshold=2)), dtype=np.uint8)
    blurred = cv2.GaussianBlur(rgb, (0, 0), 1.2)
    merged = cv2.addWeighted(rgb, 1 + amount, blurred, -amount, 0)
    return np.clip(merged, 0, 255).astype(np.uint8)


def refine(
    result: np.ndarray,
    original: np.ndarray,
    warp_mask: np.ndarray | None,
    person_mask: np.ndarray | None,
    *,
    quality: str = "fast",
) -> tuple[np.ndarray, list[str]]:
    notes: list[str] = []
    if warp_mask is None or int((warp_mask > 127).sum()) < 64:
        notes.append("postprocess_skipped_no_warp_mask")
        return result, notes

    out = result.astype(np.float32).copy()

    # 1) 边界窄带轻度降噪：只平滑接缝，保留布料内部细节
    band = _edge_band(warp_mask, width=2 if quality == "fast" else 3)
    if band.max() > 0:
        smoothed = _blur_variant(np.clip(out, 0, 255).astype(np.uint8), radius=1.0)
        alpha = band[..., None] * 0.75
        out = out * (1 - alpha) + smoothed.astype(np.float32) * alpha
        notes.append("edge_feather")

    # 2) 局部锐化（仅 HD），限制在服饰区域内
    if quality == "hd":
        sharpened = _sharpen(np.clip(out, 0, 255).astype(np.uint8), amount=0.3)
        region = (warp_mask > 127)[..., None].astype(np.float32)
        out = out * (1 - region) + sharpened.astype(np.float32) * region
        notes.append("local_sharpen")

    # 3) 保护：人体轮廓之外的背景必须与原图一致
    if person_mask is not None:
        garment_outside = np.clip(out, 0, 255).astype(np.float32)
        # 服饰可以略微溢出轮廓（宽袖/裙摆），因此只在远离轮廓 12px 之外强制还原原图
        guard = _dilate_boolean(person_mask, 12)
        guard3 = guard[..., None].astype(np.float32)
        out = garment_outside * guard3 + original.astype(np.float32) * (1 - guard3)
        notes.append("background_preserved")

    return np.clip(out, 0, 255).astype(np.uint8), notes


def _dilate_boolean(mask: np.ndarray, radius: int) -> np.ndarray:
    cv2 = cv_module()
    binary = (mask > 0).astype(np.uint8) * 255
    if cv2 is None:
        img = Image.fromarray(binary, mode="L")
        for _ in range(max(1, radius // 2)):
            img = img.filter(ImageFilter.MaxFilter(size=5))
        return np.asarray(img, dtype=np.uint8) > 127
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    return cv2.dilate(binary, kernel, iterations=1) > 127


__all__ = ["refine"]
