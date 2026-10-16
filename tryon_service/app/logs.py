"""日志配置：控制台 + 文件双写，全链路携带 request_id。"""

from __future__ import annotations

import logging
from contextvars import ContextVar
from logging.handlers import RotatingFileHandler

from app.config import get_settings

# 请求级 ID，跨 async 传播
request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

_CONFIGURED = False


class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def setup_logging(level: int = logging.INFO) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return

    settings = get_settings()
    settings.ensure_dirs()
    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | rid=%(request_id)s | %(name)s | %(message)s"
    )
    rid_filter = RequestIdFilter()

    root = logging.getLogger()
    root.setLevel(level)
    for handler in list(root.handlers):
        root.removeHandler(handler)

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    console.addFilter(rid_filter)
    root.addHandler(console)

    file_handler = RotatingFileHandler(
        settings.logs_dir / "app.log", maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setFormatter(fmt)
    file_handler.addFilter(rid_filter)
    root.addHandler(file_handler)

    # 降噪第三方库
    for noisy in ("uvicorn.access", "matplotlib", "PIL"):
        logging.getLogger(noisy).setLevel(logging.WARNING)

    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    setup_logging()
    return logging.getLogger(name)
