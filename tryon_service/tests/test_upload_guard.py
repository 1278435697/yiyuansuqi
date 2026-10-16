"""上传防护测试：真实格式校验、体积上限、伪造扩展名拒绝。"""

from __future__ import annotations

import base64

import numpy as np
import pytest
from PIL import Image

from app.errors import ImageTooLargeError, InvalidImageError
from app.utils.imageio import load_rgb, strip_data_uri
from app.utils.upload import read_upload_limited


def _png_bytes(color=(120, 60, 200), size=(80, 80)) -> bytes:
    import io

    buf = io.BytesIO()
    base = np.zeros((size[1], size[0], 3), dtype=np.uint16) + np.array(color, dtype=np.uint16)
    Image.fromarray(np.clip(base, 0, 255).astype(np.uint8)).save(buf, format="PNG")
    return buf.getvalue()


class _FakeUpload:
    def __init__(self, payload: bytes, size: int | None = None) -> None:
        self._payload = payload
        self.size = len(payload) if size is None else size

    async def read(self, n: int = -1) -> bytes:
        chunk, self._payload = self._payload[:n], self._payload[n:]
        return chunk


def test_reject_non_image_bytes():
    with pytest.raises(InvalidImageError):
        load_rgb(b"this is definitely not an image", label="人像图")


def test_reject_disguised_extension():
    """内容是 HTML，但按 .jpg 上传：必须按真实格式拒绝。"""
    fake = b"<html><body>not an image</body></html>"
    with pytest.raises(InvalidImageError):
        load_rgb(fake, label="人像图")


def test_reject_unsupported_format_gif():
    import io

    buf = io.BytesIO()
    Image.new("P", (64, 64)).save(buf, format="GIF")
    with pytest.raises(InvalidImageError):
        load_rgb(buf.getvalue(), label="人像图")


def test_reject_oversized_payload():
    big = _png_bytes() + b"\x00" * (5 * 1024 * 1024)  # 超过测试配的 4MB
    with pytest.raises(ImageTooLargeError):
        load_rgb(big, label="人像图")


def test_read_upload_limited_streams_and_rejects():
    import asyncio

    from app.utils.upload import max_bytes

    async def _run() -> tuple[bytes, list[str]]:
        errors: list[str] = []
        ok = _FakeUpload(_png_bytes())
        data = await read_upload_limited(ok, label="服饰图", max_bytes=max_bytes())

        huge = _FakeUpload(_png_bytes(), size=1024 * 1024 * 1024)
        try:
            await read_upload_limited(huge, label="服饰图", max_bytes=max_bytes())
        except ImageTooLargeError:
            errors.append("declared")

        streaming = _FakeUpload(b"\x00" * (3 * 1024 * 1024), size=0)
        try:
            await read_upload_limited(streaming, label="服饰图", max_bytes=1024 * 1024)
        except ImageTooLargeError:
            errors.append("actual")

        empty = _FakeUpload(b"")
        try:
            await read_upload_limited(empty, label="服饰图", max_bytes=max_bytes())
        except ImageTooLargeError:
            errors.append("empty")
        return data, errors

    data, errors = asyncio.run(_run())
    assert data.startswith(b"\x89PNG")
    assert errors == ["declared", "actual", "empty"]


def test_strip_data_uri_accepts_plain_and_prefixed():
    raw = _png_bytes()
    encoded = base64.b64encode(raw).decode("ascii")
    assert strip_data_uri(encoded) == raw
    assert strip_data_uri(f"data:image/png;base64,{encoded}") == raw
    with pytest.raises(InvalidImageError):
        strip_data_uri("   ")


def test_load_rgb_enforces_min_resolution_and_long_side():
    tiny = _png_bytes(size=(16, 16))
    with pytest.raises(InvalidImageError):
        load_rgb(tiny, label="人像图")

    tall = _png_bytes(size=(2400, 3000))
    arr = load_rgb(tall, label="人像图")
    assert max(arr.shape[:2]) <= 512  # 测试环境 YISU_OUTPUT_LONG_SIDE=512
