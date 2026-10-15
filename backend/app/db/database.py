"""数据库引擎与会话（SQLAlchemy 2.0）

- 正式模式：MySQL 8.0（settings.SQLALCHEMY_DATABASE_URI）
- 演示模式（USE_DEMO_DATA=true）：SQLite，自动建表 + 种子，免装 MySQL
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

_engine_kwargs: dict = {"pool_pre_ping": True, "echo": settings.DEBUG}
if settings.USE_DEMO_DATA:
    os.makedirs(os.path.dirname(settings.DEMO_DB_PATH) or ".", exist_ok=True)
    # SQLite 需要关闭同线程检查（FastAPI 线程池访问）
    _engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    _engine_kwargs["pool_recycle"] = 3600

engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, **_engine_kwargs)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    """FastAPI 依赖注入。"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
