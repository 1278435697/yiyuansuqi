"""兜底试穿后端：基于薄板样条的几何变形 + 光影匹配合成（纯 CPU）。

流程：
1. 服饰 9 个标注关键点 → 人体 9 个身体锚点，构造 TPS 控制点对；
2. TPS 形变服饰 RGB 与掩码（只在目标包围盒内采样，控制耗时）；
3. 裁剪到人体轮廓（含外扩余量，保留宽袖/长裙体积感）；
4. LAB 光影迁移，使布料亮度贴合原图躯干光照；
5. 语义遮挡：手臂/手部/头部区域从原图重新贴回服饰之上；
6. 边缘羽化合成。
"""

from __future__ import annotations

import numpy as np

from app.logs import get_logger
from app.services.garments import REQUIRED_KEYPOINTS
from app.services.vton.base import TryOnContext, TryOnOutput, body_anchor_points
from app.services.vton.harmonize import sample_lab, transfer_lab
from app.services.vton.tps_math import warp_image_forward
from app.utils.cv import cv_module, feather_mask

logger = get_logger("app.services.vton.tps")


def _dilate(mask: np.ndarray, radius: int) -> np.ndarray:
    cv2 = cv_module()
    if cv2 is None or radius <= 0:
        return mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (radius * 2 + 1, radius * 2 + 1))
    return cv2.dilate(mask, kernel, iterations=1)


def _crop_offset_canvas(window: tuple[int, int, int, int], arr: np.ndarray, shape: tuple[int, int], dtype) -> np.ndarray:
    y0, y1, x0, x1 = window
    canvas = np.zeros((shape[0], shape[1]) + arr.shape[2:], dtype=dtype)
    canvas[y0:y1, x0:x1] = arr
    return canvas


# 裙装没有肩/袖/领语义：这 7 个点只用来表达腰头的横向分布
_SKIRT_UPPER_KEYS = (
    "collar_center",
    "shoulder_L",
    "shoulder_R",
    "sleeve_L_end",
    "sleeve_R_end",
    "waist_L",
    "waist_R",
)


def _worn_hem_y(
    pose, category: str, *, sh_y: float, g_drop: float, scale: float
) -> float:
    """衣摆落点：先按布料等比投影，再夹到该品类合理的解剖区间。

    等比投影保证「长袍不会变成短褂」，区间限制保证「权重缺失时也不会悬空或拖出画面」。
    """
    torso = pose.torso_length
    hip_y = pose.hip_center[1]
    knee = pose.get("L_knee")
    knee_y = knee.y if knee and knee.visibility >= 0.3 and knee.y > hip_y else hip_y + torso * 1.1
    ankle = pose.get("L_ankle")
    ankle_y = (
        ankle.y
        if ankle and ankle.visibility >= 0.3 and ankle.y > knee_y
        else knee_y + torso * 0.9
    )
    isotropic = sh_y + g_drop * scale
    if category == "skirt":
        low, high = knee_y + torso * 0.15, ankle_y + torso * 0.25
    elif category in ("robe", "dress"):
        low, high = knee_y, ankle_y + torso * 0.2
    else:
        low, high = hip_y - torso * 0.15, knee_y + torso * 0.45
    return float(np.clip(isotropic, low, max(low + 1.0, high)))


def _retarget_skirt(
    src: np.ndarray,
    index: dict[str, int],
    proportional,
    hem_y: float,
    anchors: dict[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    """裙装没有肩/袖语义：把领口/双肩/两袖/两腰 7 个点全部压到人体腰线带。

    否则 TPS 会试图把同一圈裙腰同时映射到肩线/肘部/领口，
    导致裙子被向上抹到整个躯干。这里只保留「裙腰→腰线」「裙摆→衣摆」两组有效对应。
    """
    rows = [index[k] for k in _SKIRT_UPPER_KEYS]
    gx = src[rows, 0]
    gy = src[rows, 1]
    g_lo, g_hi = float(gx.min()), float(gx.max())
    band_top, band_bottom = float(gy.min()), float(gy.max())
    band_h = max(1.0, band_bottom - band_top)

    waist_y = anchors["waist_L"][1]
    p_lo, p_hi = anchors["waist_L"][0], anchors["waist_R"][0]
    relief = max(6.0, abs(waist_y - anchors["shoulder_L"][1]) * 0.08)

    out: dict[str, tuple[float, float]] = {}
    for key in _SKIRT_UPPER_KEYS:
        x, y = src[index[key]]
        fx = 0.5 if g_hi - g_lo < 1e-6 else (x - g_lo) / (g_hi - g_lo)
        fy = (y - band_top) / band_h
        out[key] = (p_lo + fx * (p_hi - p_lo), waist_y + fy * relief)
    out["collar_center"] = ((p_lo + p_hi) / 2.0, waist_y - relief)
    for key in ("hem_L", "hem_R"):
        px, _ = proportional(key)
        ax, _ay = anchors[key]
        out[key] = (px + (ax - px) * 0.25, hem_y)
    return out


class TPSBackend:
    name = "tps"

    def available(self) -> tuple[bool, str | None]:
        try:
            import scipy.interpolate  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            return False, f"scipy 未安装：{exc}"
        return True, None

    # ---------- 控制点 ----------
    @staticmethod
    def _source_points(ctx: TryOnContext) -> np.ndarray:
        gh, gw = ctx.garment.image.shape[:2]
        missing = [k for k in REQUIRED_KEYPOINTS if k not in ctx.garment.keypoints]
        if missing:
            raise ValueError(f"服饰缺少关键点标注：{missing}")
        pts = np.array(
            [[ctx.garment.keypoints[k][0] * gw, ctx.garment.keypoints[k][1] * gh]
             for k in REQUIRED_KEYPOINTS],
            dtype=np.float64,
        )
        if not np.isfinite(pts).all():
            raise ValueError("服饰关键点存在非法数值")
        return pts

    @staticmethod
    def _target_points(ctx: TryOnContext, src: np.ndarray) -> np.ndarray:
        """目标控制点：横向保留服饰自身的袖展/摆宽，纵向按人体肩线→衣摆对齐。

        早期实现把袖口锚到人体肘/腕，真实汉服照片（广袖/绕襟）会被压成一条窄背心；
        布料本身不可伸长，因此改为「肩点对齐人体肩点 + 其余点按肩宽比例等比展开」，
        仅对腰/摆两个躯干内的点向人体锚点适度收拢（保留收腰）。
        """
        pose = ctx.pose
        category = ctx.garment.category
        index = {name: i for i, name in enumerate(REQUIRED_KEYPOINTS)}
        anchors = body_anchor_points(pose)
        cx = pose.shoulder_center[0]
        sh_y = pose.shoulder_center[1]

        g_sh_l, g_sh_r = src[index["shoulder_L"]], src[index["shoulder_R"]]
        gcx = float((g_sh_l[0] + g_sh_r[0]) / 2.0)
        g_sh_y = float((g_sh_l[1] + g_sh_r[1]) / 2.0)
        g_hem_y = float((src[index["hem_L"]][1] + src[index["hem_R"]][1]) / 2.0)
        g_drop = max(1.0, g_hem_y - g_sh_y)

        if category == "skirt":
            # 裙装那 7 个点其实是裙腰，用裙腰宽 vs 人体腰宽定比例
            band_x = src[[index[k] for k in _SKIRT_UPPER_KEYS], 0]
            reference = max(4.0, float(band_x.max() - band_x.min()))
            target_reference = max(4.0, pose.hip_width)
        else:
            reference = max(4.0, float(np.linalg.norm(g_sh_r - g_sh_l)))
            target_reference = max(4.0, pose.shoulder_width)
        scale = target_reference / reference
        if not (0.15 <= scale <= 8.0):
            logger.warning("体型比例异常(%.2f)，限幅后继续", scale)
            scale = float(np.clip(scale, 0.15, 8.0))

        hem_y = _worn_hem_y(pose, category, sh_y=sh_y, g_drop=g_drop, scale=scale)
        v_scale = (hem_y - sh_y) / g_drop

        def proportional(key: str) -> tuple[float, float]:
            x, y = src[index[key]]
            return cx + (x - gcx) * scale, sh_y + (y - g_sh_y) * v_scale

        if category == "skirt":
            out = _retarget_skirt(src, index, proportional, hem_y, anchors)
            return np.array([out[k] for k in REQUIRED_KEYPOINTS], dtype=np.float64)

        out: dict[str, tuple[float, float]] = {
            "collar_center": anchors["collar_center"],
            "shoulder_L": anchors["shoulder_L"],
            "shoulder_R": anchors["shoulder_R"],
            "sleeve_L_end": proportional("sleeve_L_end"),
            "sleeve_R_end": proportional("sleeve_R_end"),
        }
        for key in ("waist_L", "waist_R"):
            px, py = proportional(key)
            ax, ay = anchors[key]
            out[key] = (px + (ax - px) * 0.45, py + (ay - py) * 0.45)
        for key in ("hem_L", "hem_R"):
            px, _ = proportional(key)
            ax, _ay = anchors[key]
            out[key] = (px + (ax - px) * 0.25, hem_y)
        return np.array([out[k] for k in REQUIRED_KEYPOINTS], dtype=np.float64)

    # ---------- 主流程 ----------
    def run(self, ctx: TryOnContext) -> TryOnOutput:
        src = self._source_points(ctx)
        dst = self._target_points(ctx, src)

        warped_rgb, warped_mask, window = warp_image_forward(
            ctx.garment.image,
            ctx.garment.mask,
            src,
            dst,
            ctx.shape,
            lam=1e-3 if ctx.quality == "fast" else 5e-3,
            pad=48 if ctx.quality == "fast" else 96,
        )
        y0, y1, x0, x1 = window
        notes = [f"window={window}", f"src_points={len(src)}"]

        # 光影匹配：以人体原衣物/躯干区域为参照
        region_canvas = _crop_offset_canvas(window, warped_mask, ctx.shape, np.uint8)
        target_mask = ctx.clothes_mask if ctx.clothes_mask is not None else ctx.person_mask
        stats = sample_lab(ctx.person_rgb, target_mask)
        if ctx.quality == "hd":
            warped_rgb = transfer_lab(warped_rgb, stats, strength=0.55)
            notes.append("lab_transfer_applied")

        # 允许服饰超出人体轮廓的体积（宽袖/长裙摆），但不能漂浮到远处背景
        overflow_ratio = {"robe": 0.60, "dress": 0.55, "skirt": 0.40}.get(ctx.garment.category, 0.28)
        overflow = int(max(12, ctx.pose.shoulder_width * overflow_ratio))
        allowed = _dilate(ctx.person_mask, overflow)
        paste_region = np.minimum(region_canvas, allowed)

        # 边缘羽化（全程在包围盒窗口内计算，warped_rgb 是窗口尺寸，不能与全图 alpha 广播）
        feather = 2 if ctx.quality == "fast" else 3
        paste_alpha = (
            feather_mask(paste_region[y0:y1, x0:x1], radius=feather).astype(np.float32) / 255.0
        )

        result = ctx.person_rgb.astype(np.float32)
        result[y0:y1, x0:x1] = (
            result[y0:y1, x0:x1] * (1.0 - paste_alpha[..., None])
            + warped_rgb.astype(np.float32) * paste_alpha[..., None]
        )

        # 遮挡还原：手臂 / 手 / 头 重新压回服饰之上
        occluders = []
        if ctx.arms_mask is not None:
            occluders.append(ctx.arms_mask)
        if ctx.head_mask is not None:
            occluders.append(_dilate(ctx.head_mask, 2))
        for mask in occluders:
            m = (mask[y0:y1, x0:x1] > 127).astype(np.float32)
            if float(m.mean()) < 1e-4:
                continue
            m_soft = feather_mask((m * 255).astype(np.uint8), radius=2).astype(np.float32) / 255.0
            keep = np.clip(m_soft - paste_alpha, 0.0, 1.0)[..., None]
            result[y0:y1, x0:x1] = (
                result[y0:y1, x0:x1] * (1.0 - keep)
                + ctx.person_rgb[y0:y1, x0:x1].astype(np.float32) * keep
            )

        result = np.clip(result, 0, 255).astype(np.uint8)
        if ctx.quality == "hd":
            # 仅在 HD 模式下做一次极轻降噪，避免抹掉布料纹理
            cv2 = cv_module()
            if cv2 is not None:
                result = cv2.fastNlMeansDenoisingColored(result, None, 3, 3, 7, 21)
                notes.append("denoise_light")

        full_mask = (region_canvas > 127).astype(np.uint8) * 255
        return TryOnOutput(
            result=result,
            warped_rgb=_crop_offset_canvas(window, warped_rgb, ctx.shape, np.uint8),
            warped_mask=full_mask,
            warp_window=window,
            backend=self.name,
            notes=notes,
        )


__all__ = ["TPSBackend"]
