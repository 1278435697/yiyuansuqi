"""数据库会话与引擎。"""

from __future__ import annotations

from collections.abc import AsyncIterator
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import get_settings
from app.logs import get_logger

logger = get_logger("app.db")

_engine = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def _resolved_url(url: str) -> str:
    """把 SQLite 相对路径钉到 backend/ 下，避免受启动目录影响。"""
    prefix = "sqlite+aiosqlite:///./"
    if url.startswith(prefix):
        rel = url[len(prefix) :]
        if not Path(rel).is_absolute():
            return f"sqlite+aiosqlite:///{(get_settings().data_dir.parent / rel).as_posix()}"
    return url


def get_engine():
    global _engine, _session_factory
    if _engine is None:
        url = _resolved_url(get_settings().database_url)
        kwargs: dict = {"echo": False, "pool_pre_ping": True}
        if url.startswith("sqlite"):
            Path(url.split("///")[-1]).parent.mkdir(parents=True, exist_ok=True)
            # 试穿表与平台主库是同一个 SQLite 文件，两个进程会并发读写：
            # sqlite3 的 timeout 就是 busy timeout（逐连接生效、不改动库文件），
            # 撞锁时重试而不是立刻抛 database is locked。
            kwargs["connect_args"] = {"timeout": 15.0}
        _engine = create_async_engine(url, **kwargs)
        _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
        logger.info("数据库引擎初始化完成: %s", url.split("://")[0])
    return _engine


def session_factory() -> async_sessionmaker[AsyncSession]:
    get_engine()
    assert _session_factory is not None, "数据库会话工厂未初始化"
    return _session_factory


async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI 依赖注入用的会话。"""
    async with session_factory()() as session:
        yield session


async def create_all() -> None:
    from app.db.models import Base  # 延迟导入避免循环依赖

    engine = get_engine()
    if engine.url.get_backend_name() == "sqlite" and get_settings().sqlite_wal:
        # WAL 是写在库文件里的持久设置，开一次就够；默认不开，理由见 settings.sqlite_wal
        async with engine.begin() as conn:
            await conn.exec_driver_sql("PRAGMA journal_mode=WAL")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("数据表已就绪")


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
