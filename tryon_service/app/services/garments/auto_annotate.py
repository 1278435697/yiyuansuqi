"""从服饰掩码自动推导 9 个关键点（用户临时上传的无标注服饰）。

约定与手工标注完全一致，因此 TPS 后端无需区分来源：
- 领口取掩码顶行中心
- 肩线取上部 12% 高度处的左右极值
- 袖口取最宽处（多在 35% 高度）的左右极值下方
- 腰线取高度 50% 处的左右边界（向内收 8%）
- 衣摆取底部 8% 高度处的左右边界
"""

from __future__ import annotations

import numpy as np

from app.services.garments import REQUIRED_KEYPOINTS


def infer_keypoints_from_mask(mask: np.ndarray) -> dict[str, tuple[float, float]]:
    binary = mask > 127
    ys, xs = np.where(binary)
    if ys.size < 16:
        raise ValueError("服饰掩码过小，无法自动标注关键点")
    h, w = mask.shape[:2]
    top, bottom = int(ys.min()), int(ys.max())
    left, right = int(xs.min()), int(xs.max())
    span_y = max(1, bottom - top)
    span_x = max(1, right - left)

    def row_bounds(y: int, *, shrink: float = 0.0) -> tuple[float, float]:
        y = int(np.clip(y, top, bottom))
        row = xs[ys == y]
        if row.size == 0:
            # 该行无前景（斜肩/不规则衣型），取靠近该行的若干行并集
            order = np.argsort(np.abs(ys - y))[: max(1, ys.size // 20)]
            row = xs[order]
            if row.size == 0:
                return left + span_x * shrink, right - span_x * shrink
        lo, hi = float(row.min()), float(row.max())
        pad = (hi - lo) * shrink
        return lo + pad, hi - pad

    shoulder_y = top + span_y * 0.12
    s_left, s_right = row_bounds(shoulder_y, shrink=0.02)
    sleeve_y = top + span_y * 0.38
    sl_left, sl_right = row_bounds(sleeve_y)
    waist_y = top + span_y * 0.5
    waist_left, waist_right = row_bounds(waist_y, shrink=0.08)
    hem_y = bottom - span_y * 0.06
    hem_left, hem_right = row_bounds(hem_y)

    points_px = {
        "collar_center": ((s_left + s_right) / 2, top + span_y * 0.04),
        "shoulder_L": (s_left, shoulder_y),
        "shoulder_R": (s_right, shoulder_y),
        "sleeve_L_end": (sl_left, sleeve_y),
        "sleeve_R_end": (sl_right, sleeve_y),
        "waist_L": (waist_left, waist_y),
        "waist_R": (waist_right, waist_y),
        "hem_L": (hem_left, hem_y),
        "hem_R": (hem_right, hem_y),
    }
    # 归一化到 [0,1]，与素材库标注口径一致
    return {
        name: (float(np.clip(x / w, 0.005, 0.995)), float(np.clip(y / h, 0.005, 0.995)))
        for name, (x, y) in points_px.items()
    }


def keypoints_for_category(
    mask: np.ndarray, category: str
) -> dict[str, tuple[float, float]]:
    """按品类修正自动标注。

    裙装（``skirt``）没有肩/袖语义：若沿用通用规则，TPS 会把裙子的中段当成腰线、
    把裙腰提到肩膀上。这里把领口/双肩/两袖/两腰 7 个点全部压到腰头带，
    只保留「腰头 → 人体腰线」「裙摆 → 人体衣摆」两组有效对应，与手工标注口径一致。
    """
    points = infer_keypoints_from_mask(mask)
    if category != "skirt":
        return points

    binary = mask > 127
    ys, xs = np.where(binary)
    if ys.size < 16:
        return points
    h, w = mask.shape[:2]
    top, bottom = int(ys.min()), int(ys.max())
    band_y = top + max(1, int((bottom - top) * 0.05))
    rows = xs[ys <= band_y]
    lo, hi = float(rows.min()), float(rows.max())
    pad = (hi - lo) * 0.04

    def norm(x: float, y: float) -> tuple[float, float]:
        return (float(np.clip(x / w, 0.005, 0.995)), float(np.clip(y / h, 0.005, 0.995)))

    points["collar_center"] = norm((lo + hi) / 2, top + 1)
    for name, x in (("shoulder_L", lo + pad), ("waist_L", lo + pad), ("sleeve_L_end", lo)):
        points[name] = norm(x, band_y)
    for name, x in (("shoulder_R", hi - pad), ("waist_R", hi - pad), ("sleeve_R_end", hi)):
        points[name] = norm(x, band_y)
    return points


def keypoints_to_list(points: dict[str, tuple[float, float]]) -> list[dict[str, float | str]]:
    return [{"name": name, "x": round(points[name][0], 4), "y": round(points[name][1], 4)}
            for name in REQUIRED_KEYPOINTS if name in points]
