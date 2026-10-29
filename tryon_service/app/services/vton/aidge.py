"""云端试衣后端：阿里云 Aidge「虚拟试穿」（AiTryOn，API 版本 2026-04-28）。

与本地 TPS/HR-VITON 的根本差别：它只收**公网可取的图片 URL**，不吃内存里的数组。
所以人像必须先经 outbox 换成一次性 URL 才能送出去，这条链路的隐私面由
`app/utils/outbox.py` 的短 TTL + 调用结束即删兜住。

凭据缺失、出箱地址未配、厂商报错都走 available()/run() 的降级通道，
让 vton.run 自动回落到本地引擎——云端挂了不能把功能打死，但绝不允许静默降级。
"""

from __future__ import annotations

import datetime as dt
import hashlib
import hmac
import io
import json
import re
import uuid

import numpy as np
import requests
from PIL import Image

from app.config import get_settings
from app.logs import get_logger
from app.services.vton.base import TryOnContext, TryOnOutput
from app.utils import outbox
from app.utils.imageio import load_rgb

logger = get_logger("app.services.vton.aidge")

API_VERSION = "2026-04-28"
ACTION = "AiTryOn"
# 官方对输入图的硬限制：两边都在 256–2049 px，单张 ≤10 MB
MIN_SIDE, MAX_SIDE = 256, 2049
MAX_UPLOAD_BYTES = 9 * 1024 * 1024
CLOTH_TYPE_BY_CATEGORY = {
    "robe": "dresses",
    "dress": "dresses",
    "top": "tops",
    "skirt": "bottoms",
}
CLOTH_TRIM_PAD = 0.04
_BG_DIFF = 32
_MIN_FOREGROUND = 0.02


def _sha256_hex(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def authorization(method: str, pathname: str, headers: dict[str, str], body: bytes,
                  access_key_id: str, access_key_secret: str) -> str:
    """阿里云 V3 签名（ACS3-HMAC-SHA256）。参与签名的头必须与请求实际发出的完全一致。"""
    lowered = {k.lower(): str(v).strip() for k, v in headers.items()}
    signed_names = sorted(lowered)
    canonical_headers = "".join(f"{name}:{lowered[name]}\n" for name in signed_names)
    canonical_request = "\n".join(
        [method, pathname, "", canonical_headers, ";".join(signed_names), _sha256_hex(body)]
    )
    string_to_sign = f"ACS3-HMAC-SHA256\n{_sha256_hex(canonical_request.encode('utf-8'))}"
    signature = hmac.new(
        access_key_secret.encode("utf-8"), string_to_sign.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return (
        f"ACS3-HMAC-SHA256 Credential={access_key_id},"
        f"SignedHeaders={';'.join(signed_names)},Signature={signature}"
    )


def _fit_sides(arr: np.ndarray) -> np.ndarray:
    h, w = arr.shape[:2]
    too_big = max(h, w) > MAX_SIDE
    too_small = min(h, w) < MIN_SIDE
    if not too_big and not too_small:
        return arr
    scale = MAX_SIDE / max(h, w) if too_big else MIN_SIDE / min(h, w)
    resized = np.asarray(
        Image.fromarray(arr).resize(
            (max(MIN_SIDE, int(w * scale)), max(MIN_SIDE, int(h * scale))), Image.LANCZOS
        ),
        dtype=np.uint8,
    )
    logger.info("云端输入尺寸调整 %dx%d → %dx%d", w, h, resized.shape[1], resized.shape[0])
    return resized


def _foreground_box(arr: np.ndarray, mask: np.ndarray | None) -> tuple[int, int, int, int] | None:
    h, w = arr.shape[:2]
    if mask is not None and mask.shape[:2] == (h, w) and int((mask > 127).sum()) >= 256:
        ys, xs = np.nonzero(mask > 127)
    else:
        edge = np.concatenate([arr[0], arr[-1], arr[:, 0], arr[:, -1]]).astype(np.int16)
        diff = np.abs(arr.astype(np.int16) - np.median(edge, axis=0)).max(axis=2)
        ys, xs = np.nonzero(diff > _BG_DIFF)
        if xs.size < h * w * _MIN_FOREGROUND:
            return None
    return int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1


def _trim_cloth(arr: np.ndarray, mask: np.ndarray | None = None) -> tuple[np.ndarray, bool]:
    """裁到服饰前景包围盒，四周留 4%。

    留白太多会让衣服在厂商画布里变小，模型只能靠先验补形（袖子被补窄、裙长被补短）。
    这里只做确定性裁剪：不猜形制、不改颜色，前景框满画面时原样返回。
    """
    box = _foreground_box(arr, mask)
    if box is None:
        return arr, False
    x0, y0, x1, y1 = box
    h, w = arr.shape[:2]
    pad = int(round(CLOTH_TRIM_PAD * max(x1 - x0, y1 - y0)))
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(w, x1 + pad), min(h, y1 + pad)
    if (x1 - x0) * (y1 - y0) >= 0.98 * w * h:
        return arr, False
    return np.ascontiguousarray(arr[y0:y1, x0:x1]), True


def _jpeg(arr: np.ndarray, quality: int = 92) -> bytes:
    buf = io.BytesIO()
    Image.fromarray(arr, mode="RGB").save(buf, format="JPEG", quality=quality)
    data = buf.getvalue()
    if len(data) > MAX_UPLOAD_BYTES:
        return _jpeg(arr, quality=max(50, quality - 15))
    return data


def redact(text: object) -> str:
    """厂商返回体里可能回显我们的 AK，出站日志一律先打码。"""
    return re.sub(r"LTAI[A-Za-z0-9]{4,}", "LTAI<REDACTED>", str(text))


# AiTryOn 成功时回的是 Code="success"/Message="Success"（生产日志实测），
# 而控制台与早期抓包见过 "200"。只认 "200" 会把已经出图的调用判成失败，
# 然后静默回落本地引擎——用户看到的是一张明显更差的图，谁也想不到原因。
_OK_CODES = {"", "200", "ok", "success"}


def _is_success(data: dict) -> bool:
    if data.get("Success") is True:
        return True
    return str(data.get("Code", "")).strip().lower() in _OK_CODES


class AidgeBackend:
    name = "aidge"

    def available(self) -> tuple[bool, str | None]:
        settings = get_settings()
        if not (settings.aidge_access_key_id and settings.aidge_access_key_secret):
            return False, "missing_credentials"
        if not settings.public_base_url:
            return False, "missing_public_base_url"
        return True, None

    def _payload(self, ctx: TryOnContext, person_url: str, garment_url: str) -> dict:
        settings = get_settings()
        cloth_type = settings.aidge_cloth_type.strip() or CLOTH_TYPE_BY_CATEGORY.get(
            ctx.garment.category, ""
        )
        body = {
            "ModelImageUrl": person_url,
            "ClothImageUrl": garment_url,
            "Resolution": settings.aidge_resolution,
        }
        if cloth_type:
            body["ClothType"] = cloth_type
        return body

    def _post(self, body_obj: dict) -> dict:
        settings = get_settings()
        body = json.dumps(body_obj, ensure_ascii=False).encode("utf-8")
        headers = {
            "host": settings.aidge_endpoint,
            "content-type": "application/json; charset=utf-8",
            "accept": "application/json",
            "x-acs-action": ACTION,
            "x-acs-version": API_VERSION,
            "x-acs-date": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "x-acs-signature-nonce": uuid.uuid4().hex,
        }
        headers["authorization"] = authorization(
            "POST", "/", headers, body,
            settings.aidge_access_key_id, settings.aidge_access_key_secret,
        )
        response = requests.post(
            f"https://{settings.aidge_endpoint}/",
            data=body,
            headers=headers,
            timeout=settings.aidge_timeout_seconds,
        )
        try:
            data = response.json()
        except ValueError:
            raise RuntimeError(f"Aidge 返回非 JSON（http {response.status_code}）") from None
        if response.status_code >= 400 or not _is_success(data):
            raise RuntimeError(
                f"Aidge 调用失败 http={response.status_code} "
                f"code={data.get('Code')} message={redact(data.get('Message'))} "
                f"requestId={data.get('RequestId')}"
            )
        return data

    def run(self, ctx: TryOnContext) -> TryOnOutput:
        settings = get_settings()
        person = outbox.put(_jpeg(_fit_sides(ctx.person_rgb)))
        # 有平铺呈现图就用它：展陈形对试衣模型是分布外输入，会把大袖补成窄袖插肩
        cloth = ctx.garment.cloud_cloth
        notes: list[str] = []
        if cloth is None:
            cloth = ctx.garment.image
            cloth_mask = ctx.garment.mask
        else:
            notes.append("aidge_cloth_flat_presentation")
            cloth_mask = None  # 平铺图没有配套掩码，按边框底色裁
        cloth, trimmed = _trim_cloth(cloth, cloth_mask)
        if trimmed:
            notes.append("aidge_cloth_trimmed")
        garment = outbox.put(_jpeg(_fit_sides(cloth)))
        try:
            data = self._post(self._payload(ctx, person.url, garment.url))
            result = (data.get("Data") or {}).get("ImageUrl")
            if not result:
                raise RuntimeError(f"Aidge 未返回 ImageUrl：{redact(json.dumps(data)[:300])}")
            usage = (data.get("Data") or {}).get("UsageMap") or {}
            if usage:
                notes.append(f"aidge_usage={json.dumps(usage, ensure_ascii=False)}")
            fetch = requests.get(result, timeout=settings.aidge_timeout_seconds)
            fetch.raise_for_status()
            out = load_rgb(fetch.content, label="云端试穿结果")
        finally:
            # 厂商没来取（报错/超时）时不能把用户原图留在盘上等 TTL
            for item in (person, garment):
                outbox.discard(item.token)

        if out.shape[:2] != ctx.shape:
            out = np.asarray(
                Image.fromarray(out).resize((ctx.shape[1], ctx.shape[0]), Image.LANCZOS),
                dtype=np.uint8,
            )
            notes.append("aidge_result_resized_to_source")
        notes.append("aidge_cloud_backend")
        logger.info("云端试衣完成 garment=%s resolution=%s", ctx.garment.id, settings.aidge_resolution)
        return TryOnOutput(result=out, backend=self.name, notes=notes)


__all__ = ["AidgeBackend", "authorization", "redact"]
