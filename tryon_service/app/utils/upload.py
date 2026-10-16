"""上传读取防护：分块读取 + 体积上限，避免一次性读入超大文件。"""

from __future__ import annotations

from fastapi import UploadFile

from app.errors import ImageTooLargeError
from app.logs import get_logger

logger = get_logger("app.utils.upload")

_CHUNK = 1024 * 1024


async def read_upload_limited(file: UploadFile, *, label: str, max_bytes: int) -> bytes:
    if file.size and file.size > max_bytes:
        raise ImageTooLargeError(f"{label}体积过大（{file.size / 1024 / 1024:.1f}MB 超过上限）")

    buffer = bytearray()
    while True:
        chunk = await file.read(_CHUNK)
        if not chunk:
            break
        buffer.extend(chunk)
        if len(buffer) > max_bytes:
            raise ImageTooLargeError(
                f"{label}体积过大（超过 {max_bytes / 1024 / 1024:.0f}MB 上限）"
            )
    if not buffer:
        raise ImageTooLargeError(f"{label}内容为空")
    return bytes(buffer)


def max_bytes() -> int:
    from app.config import get_settings

    return int(get_settings().max_upload_mb * 1024 * 1024)
