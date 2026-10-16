"""统一异常与错误响应。

对外响应只暴露 error_code + 中文 message + request_id，完整堆栈仅写日志。
"""

from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.logs import get_logger, request_id_var

logger = get_logger("app.errors")


class AppError(Exception):
    """业务异常基类。"""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "服务内部错误"

    def __init__(self, message: str | None = None, *, detail: str | None = None) -> None:
        self.message = message or self.message
        self.detail = detail
        super().__init__(self.message)


class InvalidImageError(AppError):
    status_code = 400
    error_code = "INVALID_IMAGE"
    message = "图片格式非法或已损坏"


class ImageTooLargeError(AppError):
    status_code = 413
    error_code = "IMAGE_TOO_LARGE"
    message = "图片体积超过限制"


class GarmentNotFoundError(AppError):
    status_code = 404
    error_code = "GARMENT_NOT_FOUND"
    message = "指定的服饰素材不存在"


class TaskNotFoundError(AppError):
    status_code = 404
    error_code = "TASK_NOT_FOUND"
    message = "指定的试穿任务不存在"


class DependencyMissingError(AppError):
    status_code = 503
    error_code = "DEPENDENCY_MISSING"
    message = "所需依赖未安装，请先安装 requirements-ai.txt"


class TryOnFailedError(AppError):
    status_code = 500
    error_code = "TRYON_FAILED"
    message = "试穿合成失败，请更换正身、光线清晰的图片重试"


def _error_payload(error_code: str, message: str) -> dict[str, Any]:
    """统一错误体。

    `message` 是本模块自己的字段，`detail` 是同值别名：并入 yisu-ai-platform 后，
    平台前端的 axios 拦截器只读 `data.detail`，两套前端共用一个 sidecar 时两边都不能断。
    """
    return {
        "error_code": error_code,
        "message": message,
        "detail": message,
        "request_id": request_id_var.get(),
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError) -> JSONResponse:
        logger.warning("业务异常 %s: %s | detail=%s", exc.error_code, exc.message, exc.detail)
        return JSONResponse(_error_payload(exc.error_code, exc.message), status_code=exc.status_code)

    @app.exception_handler(StarletteHTTPException)
    async def _http_error(_: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}.get(
            exc.status_code, "HTTP_ERROR"
        )
        return JSONResponse(
            _error_payload(code, str(exc.detail) or "请求处理失败"), status_code=exc.status_code
        )

    @app.exception_handler(RequestValidationError)
    async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
        first = exc.errors()[0] if exc.errors() else {}
        loc = ".".join(str(p) for p in first.get("loc", []))
        msg = f"请求参数校验失败：{loc or 'body'} {first.get('msg', '')}".strip()
        logger.warning("参数校验失败: %s", exc.errors())
        return JSONResponse(_error_payload("VALIDATION_ERROR", msg), status_code=422)

    @app.exception_handler(Exception)
    async def _unhandled(_: Request, exc: Exception) -> JSONResponse:
        # 完整 traceback 只进日志，绝不回传客户端
        logger.exception("未处理异常: %s", exc)
        return JSONResponse(
            _error_payload("INTERNAL_ERROR", "服务内部错误，请携带 request_id 反馈"),
            status_code=500,
        )
