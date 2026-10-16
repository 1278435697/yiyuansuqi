"""最后一层兜底：无模型人像分割。

有 opencv 时用 GrabCut（以人形中心竖条为前景先验）；
否则用「中心先验 + 颜色显著性」的纯 numpy 近似，保证主链路仍能出掩码。
"""

from __future__ import annotations

import numpy as np

from app.logs import get_logger
from app.services.segmentation.base import SegmentResult
from app.utils.cv import cv_module, keep_largest_component, morph_close
from app.utils.imageio import normalize_mask

logger = get_logger("app.services.segmentation.heuristic")


def _center_prior_mask(shape: tuple[int, int, int]) -> np.ndarray:
    h, w = shape[:2]
    mask = np.zeros((h, w), dtype=np.uint8)
    y0, y1 = int(h * 0.06), h - 1
    x0, x1 = int(w * 0.22), int(w * 0.78)
    mask[y0:y1, x0:x1] = 255
    return mask


def _color_salience(rgb: np.ndarray) -> np.ndarray:
    """以四周边界颜色为背景模型，计算像素与背景的色距作为前景显著性。"""
    h, w = rgb.shape[:2]
    border = np.concatenate(
        [rgb[: max(2, h // 20)].reshape(-1, 3), rgb[-max(2, h // 20) :].reshape(-1, 3)], axis=0
    )
    bg = np.median(border, axis=0)
    dist = np.linalg.norm(rgb.astype(np.float32) - bg.astype(np.float32)[None, None, :], axis=2)
    thr = np.percentile(dist, 55)
    return np.where(dist > thr, 255, 0).astype(np.uint8)


class HeuristicProvider:
    name = "heuristic"

    def available(self) -> tuple[bool, str | None]:
        return True, None

    def segment(self, rgb: np.ndarray) -> SegmentResult:
        prior = _center_prior_mask(rgb.shape)
        cv2 = cv_module()
        notes = ["no_deep_model"]

        if cv2 is None:
            salience = _color_salience(rgb)
            person = normalize_mask(np.minimum(prior, salience))
            notes.append("grabcut_unavailable")
            return SegmentResult(person=person, clothes=None, provider=self.name, notes=notes)

        mask = np.where(prior > 127, cv2.GC_PR_FGD, cv2.GC_BGD).astype(np.uint8)
        # 顶部中心保守标记为 probable background（多为天空/墙面），底部中心标记前景
        h, w = rgb.shape[:2]
        mask[: max(2, h // 12), :] = cv2.GC_PR_BGD
        bg_model = np.zeros((1, 65), dtype=np.float64)
        fg_model = np.zeros((1, 65), dtype=np.float64)
        try:
            cv2.grabCut(rgb, mask, None, bg_model, fg_model, iterCount=3, mode=cv2.GC_INIT_WITH_MASK)
        except cv2.error as exc:  # pragma: no cover - 极端尺寸才会触发
            logger.warning("GrabCut 失败，退化为显著性掩码: %s", exc)
            person = normalize_mask(np.minimum(prior, _color_salience(rgb)))
            notes.append("grabcut_failed")
            return SegmentResult(person=person, clothes=None, provider=self.name, notes=notes)

        person = np.where(
            (mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0
        ).astype(np.uint8)
        if person.mean() < 1:
            person = normalize_mask(np.minimum(prior, _color_salience(rgb)))
            notes.append("grabcut_empty_fallback_salience")
        person = keep_largest_component(morph_close(person, 5))
        return SegmentResult(person=person, clothes=None, provider=self.name, notes=notes)


__all__ = ["HeuristicProvider"]
