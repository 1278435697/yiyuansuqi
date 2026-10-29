"""FastAPI 应用入口：九大模块路由装配 + CORS"""
import os as _bootstrap_os
import sys as _bootstrap_sys

# 保证从任意工作目录启动都能导入 app 包（宝塔以 python 方式直接运行本文件时必需）
_bootstrap_sys.path.insert(0, _bootstrap_os.path.dirname(_bootstrap_os.path.dirname(_bootstrap_os.path.abspath(__file__))))

from app.api import websearch
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import (
    home, archive, timeline, geo_map, pattern_workshop,
    ai_qa, community, user_center, heritage_gen, ai_simulator, fabric, upload,
    pattern_library, accessories, identify,
)
from app.core.config import settings
from app.db import models  # noqa: F401 确保模型注册
from app.db.demo_seed import init_demo_db
from app.db.init_prod import init_prod_db


async def _db_keepalive() -> None:
    """进程内数据库连接保活：每 15 秒执行一次 SELECT 1，
    维持 MySQL 连接池活跃，避免空闲后首个请求卡在 2 秒重连。"""
    while True:
        try:
            from sqlalchemy import text as _sql_text
            from app.db.database import engine as _engine
            with _engine.connect() as _conn:
                _conn.execute(_sql_text("SELECT 1"))
        except Exception:
            pass
        await asyncio.sleep(15)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """启动钩子：建表+数据初始化+服饰史料向量索引（ChromaDB）+ 连接保活。"""
    keepalive_task: asyncio.Task | None = None
    try:
        if settings.USE_DEMO_DATA:
            init_demo_db()
        else:
            # 正式模式：MySQL 8.0（或本地 SQLite 正式库）建表 + 权威基础数据导入
            init_prod_db()
        try:
            from app.ai_engine.graphrag_engine import ensure_index
            from app.db.database import SessionLocal
            with SessionLocal() as db:
                ensure_index(db)
        except Exception:
            pass  # 向量库不可用时回退内置切片，不影响主流程
        # 预热数据库连接池：避免重启后首个用户请求等待 MySQL 建连
        try:
            from sqlalchemy import text as _sql_text
            from app.db.database import engine as _engine
            with _engine.connect() as _conn:
                _conn.execute(_sql_text("SELECT 1"))
        except Exception:
            pass
        # 启动进程内数据库连接保活（与 uvicorn 同生共死）
        keepalive_task = asyncio.create_task(_db_keepalive())
    except Exception as exc:
        # 数据库不可用（如正式模式未安装 MySQL）时给出明确提示，不静默吞掉
        print(f"[衣溯AI] 数据库初始化失败：{exc}（正式模式需 MySQL 8.0 或配置本地正式库）")
        raise
    yield
    if keepalive_task:
        keepalive_task.cancel()
        try:
            await keepalive_task
        except asyncio.CancelledError:
            pass


app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===== 九大模块路由 =====
app.include_router(websearch.router, prefix="/api/archive", tags=["模块2·衣溯AI档案·全网搜索"])
app.include_router(home.router, prefix="/api/home", tags=["模块1·文博资讯首页"])
app.include_router(archive.router, prefix="/api/archive", tags=["模块2·衣溯AI档案"])
app.include_router(timeline.router, prefix="/api/timeline", tags=["模块3·千年衣脉时间轴"])
app.include_router(geo_map.router, prefix="/api/geomap", tags=["模块4·出土地理热力图"])
app.include_router(pattern_workshop.router, prefix="/api/workshop", tags=["模块5·版型制作工坊"])
app.include_router(ai_qa.router, prefix="/api/aiqa", tags=["模块6·AI智能溯源问答"])
app.include_router(community.router, prefix="/api/community", tags=["模块7·国风文化共治社区"])
app.include_router(user_center.router, prefix="/api/user", tags=["模块8·用户中心与权限"])
app.include_router(heritage_gen.router, prefix="/api/heritage", tags=["模块9·文化传承生成"])
app.include_router(ai_simulator.router, prefix="/api/simulator", tags=["创新点四·时空推演模拟器"])
app.include_router(fabric.router, prefix="/api/fabrics", tags=["服装面料·历代面料溯源"])
app.include_router(pattern_library.router, prefix="/api/pattern-library", tags=["纹样资料库·十大分类"])
app.include_router(upload.router, prefix="/api/upload", tags=["通用图片上传·云端存储"])
app.include_router(accessories.router, prefix="/api/accessories", tags=["服饰与配饰·九卷档案"])
app.include_router(identify.router, tags=["AI识纹样"])

# 静态文件服务：uploads/ 目录对外可访问（图片 URL 形如 /uploads/images/202610/xxx.jpg）
import os as _os
from fastapi.staticfiles import StaticFiles

_uploads_dir = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "..", "uploads")
_os.makedirs(_uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=_uploads_dir), name="uploads")


@app.get("/")
def root():
    return {"app": "衣溯AI · 华夏服饰溯源与复原平台", "version": settings.APP_VERSION,
            "modules": ["文博资讯首页", "衣溯AI档案", "千年衣脉时间轴", "出土地理热力图",
                        "版型制作工坊", "AI溯源问答", "国风社区", "用户中心", "文化传承生成"]}


@app.get("/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8765)
