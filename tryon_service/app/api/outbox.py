"""出箱图片读取接口：GET|HEAD /api/v1/outbox/{token}。

给云端试衣厂商回取图片用。无鉴权，安全性来自 128 位随机 token + 短 TTL +
调用结束即删（发起它的那次试穿请求在 finally 里 discard）；命中失败统一 404，
不区分「不存在」与「已过期」。这里**不**做读后即删——厂商会 HEAD 预检、会重试，
nginx 对 HEAD 还会多打一次上游，任何一次多余读取都会把后面真正要用的图删掉。
"""

from __future__ import annotations

from fastapi import APIRouter, Request, Response

from app.errors import TaskNotFoundError
from app.utils import outbox

router = APIRouter()


@router.api_route("/{token}", methods=["GET", "HEAD"], include_in_schema=False)
async def get_outbox_image(request: Request, token: str) -> Response:
    try:
        if request.method == "HEAD":
            size = outbox.peek(token)
            if size is None:
                outbox.purge()
                raise TaskNotFoundError()
            return Response(
                media_type="image/jpeg",
                headers={"Content-Length": str(size), "Cache-Control": "no-store"},
            )
        data = outbox.read(token)
    except ValueError:
        # token 格式不合法（例如 URL 解码后带斜杠的探测/遍历）。本端点无鉴权、挂在公网上，
        # 非法输入必须是一条干净的 404，而不是把 ValueError 顶成 500 —— 那既污染错误日志，
        # 又等于告诉扫描器「这里有个会炸的接口」。与「不存在」同义，不额外区分。
        raise TaskNotFoundError() from None
    if data is None:
        outbox.purge()
        raise TaskNotFoundError()
    return Response(content=data, media_type="image/jpeg", headers={"Cache-Control": "no-store"})


__all__ = ["router"]
