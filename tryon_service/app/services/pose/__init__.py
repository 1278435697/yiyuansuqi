"""人体姿态估计入口：MediaPipe 优先，掩码几何兜底。

额外提供 `refine_with_clothes_region`：当肩/髋关键点可见性低时，
用语义解析得到的服饰区域中心校正肩线与衣摆位置（处理抬手、遮挡）。
"""

from __future__ import annotations

import numpy as np

from app.logs import get_logger
from app.services.pose.base import PoseResult, build_pose_from_points, pose_from_mask
from app.services.pose.mediapipe_provider import MediaPipePoseProvider

logger = get_logger("app.services.pose")

_provider = MediaPipePoseProvider()

# 可见性低于该阈值的关键点视为不可信，需要校正
_LOW_VISIBILITY = 0.5


def refine_with_clothes_region(pose: PoseResult, clothes_mask: np.ndarray) -> PoseResult:
    """用语义服饰区域校正低可见性的肩/腰关键点。"""
    binary = clothes_mask > 127
    if not binary.any():
        return pose
    ys, xs = np.where(binary)
    top_y = float(np.percentile(ys, 1))
    bottom_y = float(np.percentile(ys, 99))
    left_x = float(np.percentile(xs, 2))
    right_x = float(np.percentile(xs, 98))

    changed = []
    ls, rs = pose.get("L_shoulder"), pose.get("R_shoulder")
    if ls and rs and (min(ls.visibility, rs.visibility) < _LOW_VISIBILITY):
        # 肩线取服饰上部 10% 分位宽度处，向内侧收 8%（避免把衣袖当肩）
        width = right_x - left_x
        pose.keypoints["L_shoulder"].x = left_x + width * 0.08
        pose.keypoints["R_shoulder"].x = right_x - width * 0.08
        pose.keypoints["L_shoulder"].y = pose.keypoints["R_shoulder"].y = top_y
        pose.keypoints["L_shoulder"].visibility = 0.6
        pose.keypoints["R_shoulder"].visibility = 0.6
        changed.append("shoulders_from_clothes")

    lh, rh = pose.get("L_hip"), pose.get("R_hip")
    if lh and rh and min(lh.visibility, rh.visibility) < _LOW_VISIBILITY:
        waist_y = top_y + (bottom_y - top_y) * 0.55
        pose.keypoints["L_hip"].x, pose.keypoints["R_hip"].x = left_x + (right_x - left_x) * 0.2, right_x - (right_x - left_x) * 0.2
        pose.keypoints["L_hip"].y = pose.keypoints["R_hip"].y = waist_y
        pose.keypoints["L_hip"].visibility = 0.6
        pose.keypoints["R_hip"].visibility = 0.6
        changed.append("hips_from_clothes")

    if changed:
        pose.notes.extend(changed)
        pose.refresh_geometry()
        logger.info("姿态已按服饰语义区域校正: %s", ",".join(changed))
    return pose


def estimate_pose(
    rgb: np.ndarray, person_mask: np.ndarray, clothes_mask: np.ndarray | None = None
) -> tuple[PoseResult, np.ndarray | None, list[str]]:
    """返回 (姿态, MediaPipe 附带的人像掩码或 None, warnings)。"""
    warnings: list[str] = []
    ok, reason = _provider.available()
    if ok:
        try:
            pose, seg_mask = _provider.detect(rgb)
            if clothes_mask is not None:
                pose = refine_with_clothes_region(pose, clothes_mask)
            low = [kp.name for kp in pose.keypoints.values() if kp.visibility < _LOW_VISIBILITY]
            if low:
                warnings.append(f"pose_low_visibility:{','.join(sorted(low)[:6])}")
            if len(pose.keypoints) < 17:
                warnings.append(f"pose_partial:{len(pose.keypoints)}/17")
            logger.info("姿态 Provider=%s", pose.provider)
            return pose, seg_mask, warnings
        except Exception as exc:  # noqa: BLE001
            logger.warning("MediaPipe 姿态推理失败，退化为掩码几何估计: %s", exc)
            warnings.append("pose_mediapipe_error")
    else:
        logger.info("MediaPipe 姿态不可用: %s", reason)
        warnings.append("pose_mediapipe_unavailable")

    points = pose_from_mask(person_mask)
    if not points:
        warnings.append("pose_estimate_failed_use_center")
        h, w = rgb.shape[:2]
        points = {
            "L_shoulder": (w * 0.35, h * 0.28, 0.2),
            "R_shoulder": (w * 0.65, h * 0.28, 0.2),
            "L_hip": (w * 0.38, h * 0.58, 0.2),
            "R_hip": (w * 0.62, h * 0.58, 0.2),
        }
    pose = build_pose_from_points(points, provider="mask_geometry", notes=["no_pose_model"])
    warnings.append("pose_fallback_to_mask_geometry")
    return pose, None, warnings


def draw_pose_overlay(rgb: np.ndarray, pose: PoseResult) -> np.ndarray:
    """把 17 关键点与骨架画到原图上，供前端展示管线中间结果。"""
    overlay = rgb.copy().astype(np.float32)
    edges = [
        ("L_shoulder", "R_shoulder"),
        ("L_shoulder", "L_elbow"),
        ("L_elbow", "L_wrist"),
        ("R_shoulder", "R_elbow"),
        ("R_elbow", "R_wrist"),
        ("L_shoulder", "L_hip"),
        ("R_shoulder", "R_hip"),
        ("L_hip", "R_hip"),
        ("L_hip", "L_knee"),
        ("R_hip", "R_knee"),
        ("L_knee", "L_ankle"),
        ("R_knee", "R_ankle"),
        ("nose", "L_shoulder"),
        ("nose", "R_shoulder"),
    ]
    color = np.array([255, 80, 80], dtype=np.float32)

    def blend(x: int, y: int, weight: float = 1.0) -> None:
        h, w = overlay.shape[:2]
        if 0 <= x < w and 0 <= y < h:
            overlay[y, x] = overlay[y, x] * (1 - weight) + color * weight

    for a, b in edges:
        ka, kb = pose.get(a), pose.get(b)
        if not ka or not kb:
            continue
        steps = int(max(abs(kb.x - ka.x), abs(kb.y - ka.y)))
        for t in range(steps + 1):
            r = t / max(1, steps)
            blend(int(round(ka.x + (kb.x - ka.x) * r)), int(round(ka.y + (kb.y - ka.y) * r)), 0.75)

    for kp in pose.keypoints.values():
        for dy in range(-2, 3):
            for dx in range(-2, 3):
                blend(int(round(kp.x)) + dx, int(round(kp.y)) + dy, 1.0)
    return np.clip(overlay, 0, 255).astype(np.uint8)


def status() -> dict[str, object]:
    ok, reason = _provider.available()
    return {"mediapipe_pose": {"available": bool(ok), "reason": reason, "mode": _provider._mode}}


__all__ = ["PoseResult", "draw_pose_overlay", "estimate_pose", "refine_with_clothes_region", "status"]
