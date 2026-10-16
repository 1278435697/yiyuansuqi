"""图片 I/O 与上传防护。

约定：内部统一使用 RGB numpy 数组 (H, W, 3) uint8，掩码为 (H, W) uint8 (0-255)。
"""

from __future__ import annotations

import base64
import binascii
import io
import re
from pathlib import Path

import numpy as np
from PIL import Image, ImageOps

from app.config import get_settings
from app.errors import ImageTooLargeError, InvalidImageError

# 允许的真实图片格式（按 PIL 检测到的格式判断，而非文件扩展名）
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP", "BMP"}
_DATA_URI_RE = re.compile(r"^data:image/(?P<sub>[a-zA-Z0-9.+-]+);base64,", re.IGNORECASE)
_MAX_PIXELS = 40_000_000  # 防解码炸弹（约 6300x6300）


def strip_data_uri(payload: str) -> bytes:
    """Base64 字符串（可含 data URI 前缀）解码为字节。"""
    if not payload or not payload.strip():
        raise InvalidImageError("图片内容为空")
    body = payload.strip()
    body = _DATA_URI_RE.sub("", body, count=1) if _DATA_URI_RE.match(body) else body
    try:
        raw = base64.b64decode(body, validate=False)
    except (binascii.Error, ValueError) as exc:
        raise InvalidImageError("图片 Base64 解码失败", detail=str(exc)) from exc
    if not raw:
        raise InvalidImageError("图片数据为空")
    return raw


def check_size_limits(raw: bytes, *, label: str) -> None:
    limit_bytes = int(get_settings().max_upload_mb * 1024 * 1024)
    if len(raw) > limit_bytes:
        raise ImageTooLargeError(
            f"{label}体积过大（{len(raw) / 1024 / 1024:.1f}MB > {get_settings().max_upload_mb:.0f}MB）"
        )


def load_rgb(raw: bytes, *, label: str = "图片") -> np.ndarray:
    """字节 → RGB ndarray，校验真实格式、EXIF 方向、长边上限。"""
    check_size_limits(raw, label=label)
    Image.MAX_IMAGE_PIXELS = _MAX_PIXELS
    try:
        img = Image.open(io.BytesIO(raw))
        img.format = img.format or "UNKNOWN"
        if img.format not in ALLOWED_FORMATS:
            raise InvalidImageError(f"{label}格式不支持：{img.format}，仅接受 JPG/PNG/WEBP/BMP")
        img.load()
    except InvalidImageError:
        raise
    except Exception as exc:  # PIL 的解码异常种类很多
        raise InvalidImageError(f"{label}无法解析，可能已损坏", detail=str(exc)) from exc

    img = ImageOps.exif_transpose(img)
    img = shrink_to_long_side(img, get_settings().output_long_side)
    if img.mode != "RGB":
        img = img.convert("RGB")
    arr = np.asarray(img, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3 or arr.shape[0] < 32 or arr.shape[1] < 32:
        raise InvalidImageError(f"{label}分辨率过小或通道异常，请使用不小于 256x256 的图片")
    return arr


def load_rgb_from_base64(payload: str, *, label: str = "图片") -> np.ndarray:
    return load_rgb(strip_data_uri(payload), label=label)


def load_rgb_with_alpha(raw: bytes, *, label: str = "图片") -> tuple[np.ndarray, np.ndarray | None]:
    """读取带透明通道的图（如服饰素材 PNG），返回 (RGB, alpha 掩码或 None)。"""
    check_size_limits(raw, label=label)
    Image.MAX_IMAGE_PIXELS = _MAX_PIXELS
    try:
        img = Image.open(io.BytesIO(raw))
        if (img.format or "UNKNOWN") not in ALLOWED_FORMATS:
            raise InvalidImageError(f"{label}格式不支持：{img.format}")
        img.load()
        has_alpha = img.mode in {"RGBA", "LA", "P"} and (
            img.mode != "P" or "transparency" in img.info
        )
        alpha = None
        if has_alpha:
            alpha = np.asarray(img.convert("RGBA"))[..., 3].copy()
        img = ImageOps.exif_transpose(img).convert("RGB")
    except InvalidImageError:
        raise
    except Exception as exc:  # noqa: BLE001
        raise InvalidImageError(f"{label}无法解析，可能已损坏", detail=str(exc)) from exc
    return np.asarray(img, dtype=np.uint8), alpha


def load_rgb_from_file(path: Path, *, label: str = "图片") -> np.ndarray:
    if not path.is_file():
        raise InvalidImageError(f"{label}文件不存在：{path.name}")
    return load_rgb(path.read_bytes(), label=label)


def shrink_to_long_side(img: Image.Image, long_side: int) -> Image.Image:
    w, h = img.size
    current = max(w, h)
    if current <= long_side or current == 0:
        return img
    scale = long_side / current
    resized = (max(1, int(round(w * scale))), max(1, int(round(h * scale))))
    return img.resize(resized, Image.LANCZOS)


def save_png(arr: np.ndarray, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path, format="PNG", optimize=True)
    return path


def save_jpg(arr: np.ndarray, path: Path, quality: int = 90) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(arr).save(path, format="JPEG", quality=quality, optimize=True)
    return path


def mask_to_overlay(mask: np.ndarray, color: tuple[int, int, int] = (220, 60, 60)) -> np.ndarray:
    """二值/灰度掩码转半透明着色图，便于前端展示管线中间结果。"""
    overlay = np.zeros((*mask.shape, 3), dtype=np.uint8)
    alpha = (mask.astype(np.float32) / 255.0)[..., None]
    tint = np.array(color, dtype=np.float32)
    overlay = (tint * alpha).astype(np.uint8)
    return overlay


def resize_mask(mask: np.ndarray, height: int, width: int) -> np.ndarray:
    if mask.shape[:2] == (height, width):
        return mask
    img = Image.fromarray(mask, mode="L").resize((width, height), Image.BILINEAR)
    return np.asarray(img, dtype=np.uint8)


def normalize_mask(mask: np.ndarray, threshold: int = 127) -> np.ndarray:
    """把任意 [0,1] / [0,255] 浮点或整型掩码归一为 0/255 uint8。"""
    arr = np.asarray(mask)
    if arr.dtype != np.uint8:
        arr = arr.astype(np.float32)
        if arr.max(initial=1.0) <= 1.5:
            arr = arr * 255.0
        arr = np.clip(arr, 0, 255).astype(np.uint8)
    return np.where(arr >= threshold, 255, 0).astype(np.uint8)
