"""FastAPI 应用入口。

启动顺序：建目录 → 建表 → 素材种子 → 挂载路由与静态资源。
所有目录/依赖缺失都只记 warning，不阻断启动（保证「拉下来就能跑」）。
"""

from __future__ import annotations

import time
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles

from app import __version__
from app.api import api_router
from app.config import get_settings
from app.db.base import create_all, dispose_engine
from app.errors import register_exception_handlers
from app.logs import get_logger, request_id_var
from app.services.seed import seed_garments

logger = get_logger("app.main")

settings = get_settings()


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    settings.ensure_dirs()
    logger.info("=" * 60)
    logger.info("%s v%s 启动中……", settings.app_name, __version__)
    logger.info("数据目录: %s", settings.data_dir)
    try:
        await create_all()
    except Exception as exc:  # noqa: BLE001 - 数据库不可用时仍允许服务起来做诊断
        logger.error("数据表初始化失败: %s", exc)

    try:
        written, skipped = await seed_garments()
        logger.info("素材种子: 写入 %d 条，跳过 %d 条", written, len(skipped))
    except Exception as exc:  # noqa: BLE001
        logger.warning("素材种子失败（不阻断启动）: %s", exc)

    from app.services import segmentation, vton

    backend, fallback = vton.resolve("auto")
    logger.info(
        "试穿后端: %s%s",
        getattr(backend, "name", "unknown"),
        f"（降级原因: {fallback}）" if fallback else "",
    )
    logger.info(
        "分割 Provider: %s",
        {name: info["available"] for name, info in segmentation.status().items()},
    )
    logger.info("接口文档: http://127.0.0.1:8000/docs")
    logger.info("=" * 60)
    yield
    await dispose_engine()
    logger.info("服务已优雅关闭")


def _body_size_limit() -> int:
    """Base64 相对原始字节膨胀约 4/3，故放宽到 2.2 倍。"""
    return int(settings.max_upload_mb * 1024 * 1024 * 2.2)


def create_app() -> FastAPI:
    settings.ensure_dirs()
    app = FastAPI(
        title=settings.app_name,
        version=__version__,
        description="汉服虚拟试穿：人像分割 + 姿态估计 + 可插拔试穿推理（HR-VITON / TPS / Mock）",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        max_age=600,
    )

    @app.middleware("http")
    async def request_context(request: Request, call_next):
        # 1) 请求级 ID 贯穿全链路日志与错误响应
        rid = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        token = request_id_var.set(rid)
        # 2) Content-Length 预检：超大上传在读取前就拒绝
        declared = request.headers.get("content-length")
        if (
            request.method in {"POST", "PUT"}
            and declared
            and declared.isdigit()
            and int(declared) > _body_size_limit()
        ):
            request_id_var.reset(token)
            return JSONResponse(
                {
                    "error_code": "IMAGE_TOO_LARGE",
                    "message": f"请求体过大（上限 {settings.max_upload_mb * 2.2:.0f}MB）",
                    "request_id": rid,
                },
                status_code=413,
            )
        started = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_var.reset(token)
        response.headers["X-Request-ID"] = rid
        response.headers["X-Process-Time"] = f"{time.perf_counter() - started:.3f}"
        return response

    register_exception_handlers(app)
    app.include_router(api_router, prefix=settings.api_prefix)

    # data/ 目录整体暴露为 /static：素材图、结果图、管线中间图均可直接访问
    app.mount("/static", StaticFiles(directory=str(settings.data_dir)), name="static")

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {
            "name": settings.app_name,
            "version": __version__,
            "docs": "/docs",
            "api": settings.api_prefix,
            "health": f"{settings.api_prefix}/health",
        }

    @app.get("/healthz", include_in_schema=False)
    async def healthz() -> RedirectResponse:
        return RedirectResponse(url=f"{settings.api_prefix}/health")

    return app


app = create_app()


__all__ = ["app", "create_app"]
