"""Redis 限流兼容层（社区防刷 · 多层防护之一）

- 检测到 Redis 可用：按 user+action 频率限流，超限返回 429 判定
- Redis 不可用（未安装/未启动）：静默放行，由「前端置灰 + 数据库唯一索引」兜底
正式部署启动 Redis 后本层自动生效，无需改动业务代码。
"""
from __future__ import annotations

import time

_REDIS_URL = "redis://127.0.0.1:6379/0"
_redis_client = None
_redis_checked = False


def get_redis():
    """惰性探测 Redis；返回客户端或 None。"""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client
    _redis_checked = True
    try:
        import redis
        client = redis.Redis.from_url(_REDIS_URL, socket_connect_timeout=1)
        client.ping()
        _redis_client = client
    except Exception:
        _redis_client = None
    return _redis_client


def check_rate_limit(key: str, limit: int = 30, window: int = 60) -> bool:
    """窗口内是否允许继续操作（True=放行，False=超限 429）。

    key 建议格式：f"ratelimit:{user_id}:{action}"，如 点赞/收藏/发帖/回复。
    """
    r = get_redis()
    if r is None:
        return True  # Redis 未启用 → 兼容放行
    try:
        pipe = r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window)
        count = pipe.execute()[0]
        return count <= limit
    except Exception:
        return True


def rate_remaining(key: str, limit: int = 30, window: int = 60) -> int:
    """剩余次数（供响应头/前端提示；Redis 不可用时返回 -1）。"""
    r = get_redis()
    if r is None:
        return -1
    try:
        return max(0, limit - int(r.get(key) or 0))
    except Exception:
        return -1
