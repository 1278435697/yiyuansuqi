"""MediaPipe 姿态 Provider。

优先 `mp.solutions.pose`（BlazePose 模型内置于 pip 包，零下载），
若 weights/ 下提供 pose_landmarker_*.task 则走 Tasks API。
同时输出 33 点裁剪后的 COCO-17，以及可选的人像分割掩码。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.config import get_settings
from app.logs import get_logger
from app.services.pose.base import (
    BLAZEPOSE_TO_COCO17,
    COCO_KEYPOINT_17,
    PoseResult,
    build_pose_from_points,
)
from app.utils.imageio import normalize_mask

logger = get_logger("app.services.pose.mediapipe")

_TASK_MODELS = ("pose_landmarker_lite.task", "pose_landmarker_full.task", "pose_landmarker.task")


class MediaPipePoseProvider:
    name = "mediapipe_pose"

    def __init__(self) -> None:
        self._probed = False
        self._error: str | None = None
        self._mode: str | None = None  # "solutions" | "tasks"
        self._pose = None
        self._options = None

    def _task_model(self) -> Path | None:
        weights = get_settings().weights_dir
        for filename in _TASK_MODELS:
            candidate = weights / filename
            if candidate.is_file():
                return candidate
        return None

    def available(self) -> tuple[bool, str | None]:
        if self._probed:
            return (self._pose is not None or self._options is not None, self._error)
        self._probed = True
        try:
            import mediapipe as mp
        except Exception as exc:  # noqa: BLE001
            self._error = f"mediapipe 未安装：{exc}"
            return False, self._error

        model = self._task_model()
        if model is not None:
            try:
                from mediapipe.tasks import python as mp_python
                from mediapipe.tasks.python import vision as mp_vision

                self._options = mp_vision.PoseLandmarkerOptions(
                    base_options=mp_python.BaseOptions(model_asset_path=str(model)),
                    running_mode=mp_vision.RunningMode.IMAGE,
                    num_poses=1,
                    min_pose_detection_confidence=0.4,
                    output_segmentation_masks=True,
                )
                self._mode = "tasks"
                logger.info("MediaPipe PoseLandmarker(Tasks) 就绪: %s", model.name)
                return True, None
            except Exception as exc:  # noqa: BLE001
                logger.warning("Tasks API 不可用，回退 solutions: %s", exc)
                self._options = None

        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "pose"):
            self._error = "当前 mediapipe 版本不含 solutions.pose，且未提供 .task 模型"
            return False, self._error
        try:
            self._pose = solutions.pose.Pose(
                static_image_mode=True, model_complexity=1, min_detection_confidence=0.4,
                output_segmentation_masks=True,
            )
            self._mode = "solutions"
            logger.info("MediaPipe Pose(solutions) 就绪（内置模型，无需下载）")
        except Exception as exc:  # noqa: BLE001
            # 老版本可能不支持 output_segmentation_masks 参数
            try:
                self._pose = solutions.pose.Pose(
                    static_image_mode=True, model_complexity=1, min_detection_confidence=0.4
                )
                self._mode = "solutions"
                logger.info("MediaPipe Pose(solutions) 就绪（无分割掩码输出）")
            except Exception as exc2:  # noqa: BLE001
                self._error = f"MediaPipe Pose 初始化失败：{exc2}"
                return False, self._error
        return True, None

    # ---------- 推理 ----------
    def detect(self, rgb: np.ndarray) -> tuple[PoseResult, np.ndarray | None]:
        """返回 (COCO-17 姿态, 可选的人像分割掩码)。"""
        ok, reason = self.available()
        if not ok:
            raise RuntimeError(reason or "MediaPipe 姿态不可用")

        import mediapipe as mp

        h, w = rgb.shape[:2]
        landmarks_33: list | None = None
        seg_mask: np.ndarray | None = None

        if self._mode == "tasks":
            from mediapipe.tasks.python import vision as mp_vision

            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
            landmarker = mp_vision.PoseLandmarker.create_from_options(self._options)
            try:
                result = landmarker.detect(mp_image)
            finally:
                landmarker.close()
            if result.pose_landmarks:
                landmarks_33 = result.pose_landmarks[0]
            if result.segmentation_masks:
                seg_mask = np.asarray(result.segmentation_masks[0].mask, dtype=np.float32)
        else:
            result = self._pose.process(rgb)
            if result.pose_landmarks:
                landmarks_33 = result.pose_landmarks.landmark
            if getattr(result, "segmentation_mask", None) is not None:
                seg_mask = np.asarray(result.segmentation_mask, dtype=np.float32)

        if landmarks_33 is None:
            raise RuntimeError("MediaPipe 未检测到人体姿态")

        points: dict[str, tuple[float, float, float]] = {}
        for coco_index, bp_index in enumerate(BLAZEPOSE_TO_COCO17):
            if bp_index >= len(landmarks_33):
                continue
            lm = landmarks_33[bp_index]
            visibility = float(getattr(lm, "visibility", 1.0) or 1.0)
            points[COCO_KEYPOINT_17[coco_index]] = (lm.x * w, lm.y * h, visibility)

        # BlazePose 的 L/R 是「解剖学左右」（正身照片中位于画面右侧），而素材标注
        # 与掩码估计均按「观察者左右」命名。统一口径，否则 TPS 会把服饰水平镜像。
        points, swapped = _to_viewer_handedness(points)

        notes = [
            f"mode={self._mode}",
            f"landmarks={len(points)}/17",
            f"handedness={'viewer' if swapped else 'source'}",
        ]
        pose = build_pose_from_points(points, provider=self.name, notes=notes)

        mask = None
        if seg_mask is not None:
            mask = normalize_mask((np.clip(seg_mask, 0, 1) * 255).astype(np.uint8))
        return pose, mask


_ANATOMICAL_PAIRS = ("eye", "ear", "shoulder", "elbow", "wrist", "hip", "knee", "ankle")


def _to_viewer_handedness(
    points: dict[str, tuple[float, float, float]]
) -> tuple[dict[str, tuple[float, float, float]], bool]:
    """把每一对 L_*/R_* 按横坐标重排，保证 L_* 始终是画面左侧那一个。"""
    out = dict(points)
    changed = False
    for part in _ANATOMICAL_PAIRS:
        left, right = f"L_{part}", f"R_{part}"
        if left not in points or right not in points:
            continue
        if points[left][0] > points[right][0]:
            out[left], out[right] = points[right], points[left]
            changed = True
    return out, changed


__all__ = ["MediaPipePoseProvider"]