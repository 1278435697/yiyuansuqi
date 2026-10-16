"""公共入口：UTF-8 控制台 + sys.path 注入 backend/。"""

from __future__ import annotations

import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parent.parent


def bootstrap() -> None:
    try:  # Windows 控制台默认 GBK，避免中文输出乱码
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:  # noqa: BLE001 - 某些环境 stdout 已被替换
        pass
    if str(BACKEND_ROOT) not in sys.path:
        sys.path.insert(0, str(BACKEND_ROOT))


__all__ = ["BACKEND_ROOT", "bootstrap"]
