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

    # 对外只挂三类只读资产，不再整体暴露 data/：data/uploads 是上传原图的临时落盘，
    # 没有任何入口应当被 URL 直读。注意残留风险：结果目录里有 person_source.jpg（历史页要做原图对比），
    # 所以拿到他人 task_id 仍能看到那张人像——本服务没有鉴权，多租户开放前必须加访问控制或签名 URL。
    app.mount(
        f"{settings.asset_url_prefix}/garments",
        StaticFiles(directory=str(settings.garments_dir)),
        name="tryon-garments",
    )
    app.mount(
        f"{settings.asset_url_prefix}/samples",
        StaticFiles(directory=str(settings.samples_dir)),
        name="tryon-samples",
    )
    if settings.results_served_externally:
        # 结果图已落到平台目录下（如 backend/uploads/tryon），由平台 nginx 的 /uploads 规则提供，
        # 本服务再挂一份同名前缀只会造成两份缓存，故跳过
        logger.info("结果图由宿主提供：%s → %s", settings.results_dir, settings.results_url_prefix)
        if settings.results_url_prefix == "/tryon-results":
            # 只改了落盘目录、没改 URL 前缀是最容易碎的坑：响应里的图能存下来但访问不到
            logger.warning(
                "results_root 已越出 data/（%s），但 results_url_prefix 仍是默认值 /tryon-results；"
                "请同时指向宿主的公开路径（如 YISU_RESULTS_URL_PREFIX=/uploads/tryon），否则前端图片 404",
                settings.results_dir,
            )
    else:
        app.mount(
            settings.results_url_prefix,
            StaticFiles(directory=str(settings.results_dir)),
            name="tryon-results",
        )

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
