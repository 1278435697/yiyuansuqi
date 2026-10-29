"""短时效出箱：把要交给云端厂商的图片换成一次性 URL。

云端试衣接口只收公网 http(s) 图片地址，而用户原图按隐私约定不得进公开目录。
这里的取舍是：写进 data/outbox/，文件名是 128 位随机 token，默认 10 分钟过期，
调用结束即删（`aidge.run` 的 finally 里 discard），TTL 只兜进程崩溃那种情况。

删除**不挂在读取上**：厂商取图器会 HEAD 预检、会重试，nginx 对 HEAD 还会多打一次上游，
任何「读一次就删」都会让真正的那次 GET 拿到 404，而错误长得像我们没配好公网地址。
一次 URL 的存活边界就是发起它的那次试穿调用，不是某一次 HTTP 请求。
"""

from __future__ import annotations

import re
import secrets
import time
from dataclasses import dataclass
from pathlib import Path

from app.config import get_settings
from app.logs import get_logger

logger = get_logger("app.utils.outbox")

_TOKEN_RE = re.compile(r"^[A-Za-z0-9_-]{16,64}$")


@dataclass(frozen=True)
class OutboxItem:
    token: str
    url: str
    expires_at: float


def _path_for(token: str) -> Path:
    if not _TOKEN_RE.fullmatch(token):
        raise ValueError("非法的 outbox token")
    return get_settings().outbox_dir / f"{token}.jpg"


def put(data: bytes, *, ttl: int | None = None) -> OutboxItem:
    """落盘一份 JPEG，返回厂商可直接 GET 的绝对 URL。"""
    settings = get_settings()
    if not settings.public_base_url:
        raise RuntimeError("未配置 YISU_PUBLIC_BASE_URL，无法生成厂商可回访的图片地址")
    token = secrets.token_urlsafe(24)
    life = ttl if ttl is not None else settings.outbox_ttl_seconds
    settings.outbox_dir.mkdir(parents=True, exist_ok=True)
    _path_for(token).write_bytes(data)
    url = f"{settings.public_base_url.rstrip('/')}{settings.api_prefix}/outbox/{token}"
    return OutboxItem(token=token, url=url, expires_at=time.time() + life)


def read(token: str) -> bytes | None:
    """读取，不删除。过期或不存在返回 None（对厂商表现为 404）。"""
    path = _path_for(token)
    if not path.is_file():
        return None
    ttl = get_settings().outbox_ttl_seconds
    if time.time() - path.stat().st_mtime > ttl:
        path.unlink(missing_ok=True)
        logger.info("outbox 条目已过期 token=%s", token[:8])
        return None
    return path.read_bytes()


def peek(token: str) -> int | None:
    """只报字节数，不读内容不删除。给 HEAD 用。"""
    path = _path_for(token)
    if not path.is_file():
        return None
    ttl = get_settings().outbox_ttl_seconds
    try:
        st = path.stat()
    except OSError:
        return None
    if time.time() - st.st_mtime > ttl:
        return None
    return st.st_size


def discard(token: str) -> None:
    """无条件删除。调用结束（成功或失败）都要走它——原图不能留到 TTL 才烂在盘上。"""
    _path_for(token).unlink(missing_ok=True)


def purge() -> int:
    """清掉所有超龄条目（进程崩溃或调用方没走到删除时的兜底）。"""
    ttl = get_settings().outbox_ttl_seconds
    outbox = get_settings().outbox_dir
    if not outbox.is_dir():
        return 0
    now = time.time()
    removed = 0
    for path in outbox.glob("*.jpg"):
        try:
            if now - path.stat().st_mtime > ttl:
                path.unlink(missing_ok=True)
                removed += 1
        except OSError:
            continue
    if removed:
        logger.info("outbox 清理 %d 个过期条目", removed)
    return removed


__all__ = ["OutboxItem", "discard", "peek", "purge", "put", "read"]
