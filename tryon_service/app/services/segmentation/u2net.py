"""U2Net 人像分割（onnxruntime CPU 推理，也可退化到 pip 包 u2net）。

权重路径优先级：weights/u2net.onnx > weights/u2netp.onnx > 包内自动下载。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.config import get_settings
from app.logs import get_logger
from app.services.segmentation.base import SegmentResult
from app.utils.imageio import normalize_mask, resize_mask

logger = get_logger("app.services.segmentation.u2net")

_INPUT_SIZE = 320
_MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
_STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)


class U2NetProvider:
    name = "u2net"

    def __init__(self) -> None:
        self._session = None
        self._input_name: str | None = None
        self._model_path: Path | None = None
        self._probe_done = False
        self._probe_error: str | None = None

    # ---------- 探测 ----------
    def _candidate_models(self) -> list[Path]:
        settings = get_settings()
        candidates = [settings.u2net_onnx or Path("weights/u2net.onnx")]
        candidates += [settings.weights_dir / "u2net.onnx", settings.weights_dir / "u2netp.onnx"]
        return [p if p.is_absolute() else (Path(__file__).resolve().parents[3] / p) for p in candidates]

    def available(self) -> tuple[bool, str | None]:
        if self._probe_done:
            return (self._session is not None, self._probe_error)
        self._probe_done = True
        try:
            import onnxruntime as ort  # noqa: F401
        except Exception as exc:  # noqa: BLE001
            self._probe_error = f"onnxruntime 未安装：{exc}"
            return False, self._probe_error
        path = next((p for p in self._candidate_models() if p.is_file()), None)
        if path is None:
            self._probe_error = "未找到 u2net.onnx / u2netp.onnx 权重，可运行 scripts/download_weights.py --asset u2net"
            return False, self._probe_error
        try:
            providers = ["CPUExecutionProvider"]
            self._session = ort.InferenceSession(str(path), providers=providers)
            self._input_name = self._session.get_inputs()[0].name
            self._model_path = path
            logger.info("U2Net 加载成功: %s", path.name)
        except Exception as exc:  # noqa: BLE001
            self._session = None
            self._probe_error = f"U2Net 权重加载失败：{exc}"
            return False, self._probe_error
        return True, None

    # ---------- 预处理 ----------
    @staticmethod
    def _preprocess(rgb: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
        from PIL import Image

        h, w = rgb.shape[:2]
        resized = np.asarray(
            Image.fromarray(rgb).resize((_INPUT_SIZE, _INPUT_SIZE), Image.BILINEAR), dtype=np.uint8
        )
        arr = resized.astype(np.float32) / 255.0
        arr = (arr - _MEAN) / _STD
        arr = arr.transpose(2, 0, 1)[None].astype(np.float32)
        return arr, (h, w)

    @staticmethod
    def _postprocess(saliency: np.ndarray, orig_hw: tuple[int, int]) -> np.ndarray:
        dm = saliency.squeeze()
        dm = np.clip(dm, 0.0, 1.0)
        dm = ((dm - dm.min()) / max(1e-6, dm.max() - dm.min()) * 255.0).astype(np.uint8)
        return normalize_mask(resize_mask(dm, orig_hw[0], orig_hw[1]))

    # ---------- 推理 ----------
    def segment(self, rgb: np.ndarray) -> SegmentResult:
        ok, reason = self.available()
        if not ok or self._session is None or self._input_name is None:
            raise RuntimeError(reason or "U2Net 不可用")
        blob, orig_hw = self._preprocess(rgb)
        outputs = self._session.run(None, {self._input_name: blob})
        mask = self._postprocess(outputs[0], orig_hw)
        return SegmentResult(
            person=mask, clothes=None, provider=self.name, notes=[f"model={self._model_path}"]
        )
