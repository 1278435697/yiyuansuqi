"""MediaPipe 人像分割兜底 Provider。

优先使用 `mp.solutions.selfie_segmentation`（模型随 pip 包内置，零下载）；
若 weights/ 下提供 selfie_segmenter.tflite 则走 Tasks API。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.config import get_settings
from app.logs import get_logger
from app.services.segmentation.base import SegmentResult
from app.utils.imageio import normalize_mask

logger = get_logger("app.services.segmentation.mediapipe")


class MediaPipeSelfieProvider:
    name = "mediapipe_selfie"

    def __init__(self) -> None:
        self._probed = False
        self._error: str | None = None
        self._mode: str | None = None  # "solutions" | "tasks"
        self._segmenter = None
        self._tasks_options = None

    def _task_model(self) -> Path | None:
        weights = get_settings().weights_dir
        for filename in ("selfie_segmenter.tflite", "selfie_segmenter.lite"):
            candidate = weights / filename
            if candidate.is_file():
                return candidate
        return None

    def available(self) -> tuple[bool, str | None]:
        if self._probed:
            return (self._segmenter is not None or self._tasks_options is not None, self._error)
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

                base_options = mp_python.BaseOptions(model_asset_path=str(model))
                self._tasks_options = mp_vision.SelfieSegmenterOptions(
                    base_options=base_options,
                    running_mode=mp_vision.RunningMode.IMAGE,
                )
                self._mode = "tasks"
                logger.info("MediaPipe SelfieSegmenter(Tasks) 就绪: %s", model.name)
                return True, None
            except Exception as exc:  # noqa: BLE001
                logger.warning("Tasks API 初始化失败，回退 solutions: %s", exc)
                self._tasks_options = None

        solutions = getattr(mp, "solutions", None)
        if solutions is None or not hasattr(solutions, "selfie_segmentation"):
            self._error = "当前 mediapipe 版本不含 selfie_segmentation，且未提供 .tflite 模型"
            return False, self._error
        try:
            self._segmenter = solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
            self._mode = "solutions"
            logger.info("MediaPipe SelfieSegmentation(solutions) 就绪（内置模型，无需下载）")
        except Exception as exc:  # noqa: BLE001
            self._error = f"MediaPipe selfie 初始化失败：{exc}"
            return False, self._error
        return True, None

    def segment(self, rgb: np.ndarray) -> SegmentResult:
        ok, reason = self.available()
        if not ok:
            raise RuntimeError(reason or "MediaPipe 分割不可用")

        import mediapipe as mp

        if self._mode == "tasks":
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=np.ascontiguousarray(rgb))
            with mp_vision_selfie_segmenter(self._tasks_options) as segmenter:
                result = segmenter.detect(mp_image)
            mask = np.asarray(result.segmentation_mask, dtype=np.float32)
        else:
            result = self._segmenter.process(rgb)
            # solutions API 的字段名是 segmentation_mask（(H,W) float32 ∈ [0,1]）
            mask = np.asarray(result.segmentation_mask, dtype=np.float32)

        mask = np.clip(mask, 0.0, 1.0)
        person = normalize_mask((mask * 255.0).astype(np.uint8), threshold=127)
        coverage = float((person > 127).mean())
        notes = [f"mode={self._mode}", f"coverage={coverage:.3f}"]
        return SegmentResult(person=person, clothes=None, provider=self.name, notes=notes)


def mp_vision_selfie_segmenter(options):
    """延迟导入 Tasks SelfieSegmenter，避免模块级依赖新 API。"""
    from mediapipe.tasks.python import vision as mp_vision

    return mp_vision.SelfieSegmenter.create_from_options(options)


__all__ = ["MediaPipeSelfieProvider"]
