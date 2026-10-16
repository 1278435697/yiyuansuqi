"""Mock 后端：仅做等比缩放贴图。

用途：依赖完全缺失（无 scipy/无模型）时仍可验证接口契约、前端联调与截图。
输出会带 `mock_backend_used` 警告，避免误当成真实效果。
"""

from __future__ import annotations

import numpy as np

from app.logs import get_logger
from app.services.vton.base import TryOnContext, TryOnOutput, body_anchor_points

logger = get_logger("app.services.vton.mock")


class MockBackend:
    name = "mock"

    def available(self) -> tuple[bool, str | None]:
        return True, None

    def run(self, ctx: TryOnContext) -> TryOnOutput:
        anchors = body_anchor_points(ctx.pose)
        left = anchors["shoulder_L"][0]
        right = anchors["shoulder_R"][0]
        top = min(anchors["collar_center"][1], anchors["shoulder_L"][1])
        bottom = max(anchors["hem_L"][1], anchors["hem_R"][1])

        h, w = ctx.shape
        x0, x1 = sorted((int(max(0, min(w - 2, left))), int(max(1, min(w - 1, right)))))
        y0, y1 = sorted((int(max(0, min(h - 2, top))), int(max(1, min(h - 1, bottom)))))
        if x1 - x0 < 4 or y1 - y0 < 4:
            raise ValueError("人体区域过小，无法贴图")

        from PIL import Image

        gh, gw = ctx.garment.image.shape[:2]
        scale = max(1e-3, min((x1 - x0) / gw, (y1 - y0) / gh))
        nw, nh = max(2, int(gw * scale)), max(2, int(gh * scale))
        pasted = np.asarray(
            Image.fromarray(ctx.garment.image).resize((nw, nh), Image.BILINEAR), dtype=np.uint8
        )
        pasted_mask = np.asarray(
            Image.fromarray(ctx.garment.mask, mode="L").resize((nw, nh), Image.BILINEAR),
            dtype=np.uint8,
        )

        cx = (x0 + x1) // 2
        paste_x0 = max(0, min(w - nw, cx - nw // 2))
        paste_y0 = max(0, min(h - nh, y0))
        canvas = np.zeros((h, w), dtype=np.uint8)
        canvas[paste_y0 : paste_y0 + nh, paste_x0 : paste_x0 + nw] = pasted_mask
        rgb_canvas = np.zeros((h, w, 3), dtype=np.uint8)
        rgb_canvas[paste_y0 : paste_y0 + nh, paste_x0 : paste_x0 + nw] = pasted

        alpha = (canvas.astype(np.float32) / 255.0)[..., None] * (ctx.person_mask > 0).astype(
            np.float32
        )[..., None]
        result = np.clip(
            ctx.person_rgb.astype(np.float32) * (1 - alpha) + rgb_canvas.astype(np.float32) * alpha,
            0,
            255,
        ).astype(np.uint8)

        logger.info("Mock 后端贴图区域 y=%d:%d x=%d:%d", y0, y1, x0, x1)
        return TryOnOutput(
            result=result,
            warped_rgb=rgb_canvas,
            warped_mask=canvas,
            warp_window=(paste_y0, paste_y0 + nh, paste_x0, paste_x0 + nw),
            backend=self.name,
            notes=["mock_backend_used"],
        )


__all__ = ["MockBackend"]
