"""API 依赖。"""

from __future__ import annotations

import uuid

from app.db.base import get_session

NEW_TASK_ID = lambda: uuid.uuid4().hex[:16]  # noqa: E731 - 轻量任务号生成

__all__ = ["NEW_TASK_ID", "get_session"]
