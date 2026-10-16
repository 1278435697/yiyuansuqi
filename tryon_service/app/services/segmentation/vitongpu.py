"""VitonGPCI 语义解析 Provider（gcpait_vitongpu_2k.onnx）。

输出人体部位语义图（18 类），可同时给出人体掩码与「上衣/下衣/裙」区域，
是 TPS 兜底合成最理想的输入；权重缺失时该 Provider 自动跳过。
类别索引沿用 ATR/VITON-HD 常用约定。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from app.config import get_settings
from app.logs import get_logger
from app.services.segmentation.base import SegmentResult

logger = get_logger("app.services.segmentation.vitongpu")

# ATR 18 类语义标签（下标即网络输出的类别值，0 = background）
_SEMANTIC_LABELS = [
    "background",
    "hat",
    "hair",
    "glove",
    "sunglasses",
    "upper_clothes",
    "dress",
    "skirt",
    "shorts_pants",
    "socks",
    "head",
    "face",
    "leg",
    "boot",
    "shoe",
    "hand",
    "arm",
    "hand_bag",
]
_LABEL_INDEX = {name: i for i, name in enumerate(_SEMANTIC_LABELS)}


def _labels(*names: str) -> tuple[int, ...]:
    return tuple(_LABEL_INDEX[n] for n in names)


# 人体 = 除 background / hand_bag 外的全部部位
_PERSON_LABELS = tuple(i for i in range(1, len(_SEMANTIC_LABELS)) if i != _LABEL_INDEX["hand_bag"])
# 服饰语义区域（上衣/连衣裙/裙/裤）
_CLOTHES_LABELS = _labels("upper_clothes", "dress", "skirt", "shorts_pants")
# 需要逆回服饰之上遮挡肢体的区域
_ARMS_LABELS = _labels("arm", "hand", "glove")
_HEAD_LABELS = _labels("hat", "hair", "head", "face", "sunglasses")
_INPUT_LONG_SIDE = 512


class VitonGPUProvider:
    name = "vitongpu"

    def __init__(self) -> None:
        self._session = None
        self._input_name: str | None = None
        self._path: Path | None = None
        self._probed = False
        self._error: str | None = None

    def available(self) -> tuple[bool, str | None]:
        if self._probed:
            return (self._session is not None, self._error)
        self._probed = True
        settings = get_settings()
        backend_root = Path(__file__).resolve().parents[3]
        raw_candidates = [
            settings.vitongpu_onnx,
            settings.weights_dir / "gcpait_vitongpu_2k.onnx",
            settings.weights_dir / "gcpait_vitongpu_1k_96.onnx",
            backend_root / "weights" / "gcpait_vitongpu_2k.onnx",
        ]
        path = next(
            (
                p
                for p in (Path(str(c)) for c in raw_candidates if c)
                if (p if p.is_absolute() else backend_root / p).is_file()
            ),
            None,
        )
        if path is not None and not path.is_absolute():
            path = backend_root / path
        if path is None:
            self._error = "未找到 gcpait_vitongpu_2k.onnx（可运行 scripts/download_weights.py --asset vitongpu）"
            return False, self._error
        try:
            import onnxruntime as ort

            self._session = ort.InferenceSession(
                str(path), providers=["CPUExecutionProvider"]
            )
            self._input_name = self._session.get_inputs()[0].name
            self._path = path
            logger.info("VitonGPCI 语义模型加载成功: %s", path.name)
        except Exception as exc:  # noqa: BLE001
            self._session = None
            self._error = f"VitonGPCI 模型加载失败：{exc}"
            return False, self._error
        return True, None

    @staticmethod
    def _label_map(semantics: np.ndarray) -> np.ndarray:
        """网络输出 (1,N,H,W) logits → (H,W) 类别索引；兼容 (H,W) 已 argmax 的导出。"""
        arr = np.squeeze(semantics)
        if arr.ndim == 3 and arr.shape[0] > 1:
            return np.argmax(arr, axis=0).astype(np.uint8)
        return arr.astype(np.uint8)

    def segment(self, rgb: np.ndarray) -> SegmentResult:
        ok, reason = self.available()
        if not ok or self._session is None or self._input_name is None:
            raise RuntimeError(reason or "VitonGPCI 不可用")

        from PIL import Image

        h, w = rgb.shape[:2]
        scale = _INPUT_LONG_SIDE / max(h, w)
        nw, nh = max(1, int(round(w * scale))), max(1, int(round(h * scale)))
        resized = np.asarray(Image.fromarray(rgb).resize((nw, nh), Image.BILINEAR), dtype=np.uint8)
        blob = resized.astype(np.float32).transpose(2, 0, 1)[None] / 255.0

        out = self._session.run(None, {self._input_name: blob})[0]
        labels = self._label_map(out)
        labels_up = np.asarray(
            Image.fromarray(labels.astype(np.uint8)).resize((w, h), Image.NEAREST), dtype=np.uint8
        )

        person = np.isin(labels_up, list(_PERSON_LABELS)).astype(np.uint8) * 255
        clothes = np.isin(labels_up, list(_CLOTHES_LABELS)).astype(np.uint8) * 255
        arms = np.isin(labels_up, list(_ARMS_LABELS)).astype(np.uint8) * 255
        head = np.isin(labels_up, list(_HEAD_LABELS)).astype(np.uint8) * 255
        notes = [f"model={self._path.name}", f"person_ratio={float((person > 127).mean()):.3f}"]
        if clothes.mean() < 1:
            notes.append("clothes_region_empty")
        return SegmentResult(
            person=person,
            clothes=clothes if clothes.max() > 127 else None,
            provider=self.name,
            notes=notes,
            extra={"arms": arms, "head": head},
        )


__all__ = ["VitonGPUProvider", "_SEMANTIC_LABELS"]
