"""云端试衣链路测试：出箱 URL 的生命周期 + Aidge 签名请求与降级语义。

不打真实接口：厂商调用全部用假响应桩，断言的是「我们发出去什么」和
「失败时盘上有没有留下用户原图」。
"""

from __future__ import annotations

import json
import os
import time
from types import SimpleNamespace

import numpy as np
import pytest

from app.config import get_settings
from app.services.vton import aidge as aidge_mod
from app.services.vton.aidge import AidgeBackend, authorization
from app.utils import outbox


def _ctx(person=None, garment=None):
    person_rgb = person if person is not None else np.zeros((300, 200, 3), dtype=np.uint8)
    garment = garment or {}
    g_img = garment.get("image", np.zeros((400, 300, 3), dtype=np.uint8))
    garment_obj = SimpleNamespace(id=garment.get("id", "longfengpao-ming"),
                                  category=garment.get("category", "robe"), image=g_img,
                                  mask=garment.get("mask"),
                                  cloud_cloth=garment.get("cloud_cloth"))
    return SimpleNamespace(person_rgb=person_rgb, garment=garment_obj, shape=person_rgb.shape[:2])


@pytest.fixture
def cloud_settings(monkeypatch):
    settings = get_settings()
    monkeypatch.setattr(settings, "public_base_url", "http://tryon.test")
    monkeypatch.setattr(settings, "aidge_access_key_id", "LTAItestkey")
    monkeypatch.setattr(settings, "aidge_access_key_secret", "secret-not-real")
    monkeypatch.setattr(settings, "aidge_cloth_type", "")
    monkeypatch.setattr(settings, "outbox_ttl_seconds", 600)
    settings.outbox_dir.mkdir(parents=True, exist_ok=True)
    return settings


class FakeResponse:
    def __init__(self, payload=None, status_code=200, content=b""):
        self._payload = payload
        self.status_code = status_code
        self.content = content

    def json(self):
        if self._payload is None:
            raise ValueError("not json")
        return self._payload

    def raise_for_status(self):
        return None


def test_authorization_is_stable_and_body_bound():
    headers = {"host": "aidge.example", "x-acs-action": "AiTryOn"}
    body = b'{"Resolution":"1K"}'
    first = authorization("POST", "/", headers, body, "AKID", "SECRET")
    second = authorization("POST", "/", headers, body, "AKID", "SECRET")
    changed = authorization("POST", "/", headers, b'{"Resolution":"2K"}', "AKID", "SECRET")
    assert first == second
    assert first != changed
    assert first.startswith("ACS3-HMAC-SHA256 Credential=AKID,")
    assert "SignedHeaders=host;x-acs-action," in first  # 头名按字典序参与签名


def test_outbox_read_can_be_taken_more_than_once(cloud_settings):
    """读取不删。厂商的取图器会预检、会重试，读一次就删必然把后面那次打成 404。"""
    item = outbox.put(b"jpeg-bytes")
    assert item.url.startswith("http://tryon.test/api/v1/outbox/")
    assert outbox.read(item.token) == b"jpeg-bytes"
    assert outbox.read(item.token) == b"jpeg-bytes"
    outbox.discard(item.token)
    assert outbox.read(item.token) is None


def test_outbox_rejects_bad_tokens(cloud_settings):
    for bad in ("../../etc/passwd", "short", "has space"):
        with pytest.raises(ValueError):
            outbox.read(bad)


def test_outbox_expires(cloud_settings):
    item = outbox.put(b"x")
    path = cloud_settings.outbox_dir / f"{item.token}.jpg"
    old = time.time() - 3600
    os.utime(path, (old, old))
    assert outbox.read(item.token) is None
    assert not path.exists()


def test_outbox_put_needs_public_base_url(monkeypatch):
    monkeypatch.setattr(get_settings(), "public_base_url", "")
    with pytest.raises(RuntimeError):
        outbox.put(b"x")


def test_cloud_endpoint_serves_repeatedly_until_discarded(cloud_settings, client):
    item = outbox.put(b"abc")
    url = f"/api/v1/outbox/{item.token}"
    assert client.get(url).status_code == 200
    assert client.get(url).status_code == 200, "同一张图被取第二次不该变成 404"
    outbox.discard(item.token)
    assert client.get(url).status_code == 404
    assert client.get("/api/v1/outbox/does-not-exist-at-all").status_code == 404


def test_head_preflight_leaves_the_image_for_the_real_get(cloud_settings, client):
    """HEAD 预检（以及 nginx 代发的额外上游请求）不能把图弄没。

    厂商报「image not available. HTTP 404」时，先怀疑我们自己把 URL 提前消费了。
    """
    payload = b"jpeg-bytes-here" * 10
    item = outbox.put(payload)
    url = f"/api/v1/outbox/{item.token}"

    for i in range(2):
        head = client.head(url)
        assert head.status_code == 200, f"第{i + 1}次 HEAD"
        assert head.headers["content-type"] == "image/jpeg"
        assert int(head.headers["content-length"]) == len(payload)
        assert not head.content

    got = client.get(url)
    assert got.status_code == 200, "HEAD 之后 GET 必须仍能取到图"
    assert got.content == payload
    outbox.discard(item.token)  # 不收尾会把原图泄漏到后续测试的 outbox 目录断言里


def test_head_on_missing_or_illegal_token_is_404(cloud_settings, client):
    assert client.head("/api/v1/outbox/does-not-exist-at-all").status_code == 404
    assert client.head("/api/v1/outbox/short").status_code == 404


def test_cloud_endpoint_maps_bad_tokens_to_404_not_500(cloud_settings, client):
    """本端点无鉴权挂在公网上：非法 token 必须是干净 404。

    顶成 500 会同时干两件坏事——把扫描器的每次试探写进错误日志，
    以及让部署预检（期望 404）看起来像「链路通了但服务在报错」。
    """
    for bad in ("short", "has%20space", "..%2F..%2Fetc%2Fpasswd", "a" * 65):
        resp = client.get(f"/api/v1/outbox/{bad}")
        assert resp.status_code == 404, f"非法 token 应 404：{bad} -> {resp.status_code}"
        # 500 会把 ValueError 文本（含出件目录绝对路径）带进 detail，公网端点不能泄这个
        assert str(cloud_settings.outbox_dir) not in resp.text


def test_available_requires_credentials_and_base_url(cloud_settings, monkeypatch):
    assert AidgeBackend().available() == (True, None)
    monkeypatch.setattr(cloud_settings, "aidge_access_key_secret", "")
    assert AidgeBackend().available() == (False, "missing_credentials")
    monkeypatch.setattr(cloud_settings, "aidge_access_key_secret", "x")
    monkeypatch.setattr(cloud_settings, "public_base_url", "")
    assert AidgeBackend().available() == (False, "missing_public_base_url")


def test_payload_maps_category_to_cloth_type(cloud_settings, monkeypatch):
    backend = AidgeBackend()
    cases = {
        "robe": "dresses",
        "dress": "dresses",
        "top": "tops",
        "skirt": "bottoms",
        "unknown": "",
    }
    for category, expected in cases.items():
        body = backend._payload(_ctx(garment={"category": category}), "p", "g")
        assert body["Resolution"] == "1K"
        if expected:
            assert body["ClothType"] == expected
        else:
            assert "ClothType" not in body  # 认不出类别时交给厂商判断，不硬塞
    monkeypatch.setattr(cloud_settings, "aidge_cloth_type", "tops")
    assert backend._payload(_ctx(), "p", "g")["ClothType"] == "tops"


def test_run_sends_outbox_urls_and_cleans_up(cloud_settings, monkeypatch):
    seen = {}
    result_png = np.full((120, 90, 3), 7, dtype=np.uint8)
    import io as _io

    from PIL import Image as _Image

    buf = _io.BytesIO()
    _Image.fromarray(result_png).save(buf, format="PNG")

    def fake_post(url, data=None, headers=None, timeout=None):
        seen["url"] = url
        seen["body"] = json.loads(data.decode("utf-8"))
        seen["action"] = headers.get("x-acs-action")
        seen["version"] = headers.get("x-acs-version")
        seen["auth"] = headers.get("authorization", "")
        return FakeResponse({"Code": "200", "Data": {"ImageUrl": "https://vendor/result.png",
                                                     "UsageMap": {"ProcessedImageCount": 1}}})

    def fake_get(url, timeout=None):
        seen["fetch"] = url
        return FakeResponse(content=buf.getvalue())

    monkeypatch.setattr(aidge_mod.requests, "post", fake_post)
    monkeypatch.setattr(aidge_mod.requests, "get", fake_get)

    out = AidgeBackend().run(_ctx())
    assert out.backend == "aidge"
    assert out.result.shape == (300, 200, 3)  # 结果按人像尺寸回贴，下游后处理不改坐标系
    assert out.warped_mask is None
    assert seen["action"] == "AiTryOn" and seen["version"] == "2026-04-28"
    assert seen["fetch"] == "https://vendor/result.png"
    assert seen["body"]["ClothType"] == "dresses"
    for key in ("ModelImageUrl", "ClothImageUrl"):
        assert seen["body"][key].startswith("http://tryon.test/api/v1/outbox/")
    assert seen["auth"].startswith("ACS3-HMAC-SHA256 Credential=LTAItestkey,")
    assert list(cloud_settings.outbox_dir.glob("*.jpg")) == []  # 用户原图不留盘


def _outbox_image(url: str) -> np.ndarray | None:
    """把出箱 URL 指向的图解回内存（读取不删，所以厂商看到什么我们就能取什么）。"""
    token = url.rstrip("/").split("/")[-1]
    data = outbox.read(token)
    return None if data is None else aidge_mod.load_rgb(data, label="测试取图")


def _stub_vendor(monkeypatch, seen):
    import io as _io

    from PIL import Image as _Image

    buf = _io.BytesIO()
    _Image.fromarray(np.full((120, 90, 3), 7, dtype=np.uint8)).save(buf, format="PNG")

    def fake_post(url, data=None, headers=None, timeout=None):
        body = json.loads(data.decode("utf-8"))
        seen["body"] = body
        # 出箱在调用结束即删，要验「发出去的是哪张图」只能在厂商取图的这一刻抄下来
        seen["sent"] = {
            key: _outbox_image(value) for key, value in body.items()
            if isinstance(value, str) and "/outbox/" in value
        }
        return FakeResponse({"Code": "success", "Data": {"ImageUrl": "https://vendor/r.png"}})

    monkeypatch.setattr(aidge_mod.requests, "post", fake_post)
    monkeypatch.setattr(aidge_mod.requests, "get",
                        lambda url, timeout=None: FakeResponse(content=buf.getvalue()))


def test_run_sends_the_flat_presentation_when_the_garment_has_one(cloud_settings, monkeypatch):
    """展陈形对试衣模型是分布外输入：大袖会被补成窄袖 + 领口到腋下的斜插肩缝。

    实测（生产、同人像同引擎）只把发给厂商的服装图换成平铺 T 形，大袖、肩线、
    裙长全部回正。所以素材带 `{id}_flat.png` 时必须发那张，而不是素材原图。
    """
    seen: dict = {}
    _stub_vendor(monkeypatch, seen)
    flat = np.full((400, 300, 3), 200, dtype=np.uint8)
    display = np.zeros((400, 300, 3), dtype=np.uint8)

    out = AidgeBackend().run(_ctx(garment={"image": display, "cloud_cloth": flat}))
    assert "aidge_cloth_flat_presentation" in out.notes
    assert seen["sent"]["ClothImageUrl"].mean() > 150, "发出去的不是平铺呈现图"
    assert seen["sent"]["ModelImageUrl"].mean() < 5  # 人像仍是原图


def test_run_falls_back_to_the_display_image_without_a_flat(cloud_settings, monkeypatch):
    seen: dict = {}
    _stub_vendor(monkeypatch, seen)
    display = np.full((400, 300, 3), 210, dtype=np.uint8)

    out = AidgeBackend().run(_ctx(garment={"image": display}))
    assert "aidge_cloth_flat_presentation" not in out.notes
    assert seen["sent"]["ClothImageUrl"].mean() > 150


def test_trim_cloth_crops_the_white_margin():
    arr = np.full((400, 500, 3), 255, dtype=np.uint8)
    arr[150:250, 200:300] = 40  # 100x100 的衣服，四周大片留白

    out, trimmed = aidge_mod._trim_cloth(arr)
    assert trimmed
    assert out.shape[:2] == (108, 108)  # 100 + 两侧各 4px（4%）


def test_trim_cloth_prefers_the_mask_box():
    """有掩码时按掩码裁：边框法会被大面积浅色背景或阴影带偏。"""
    arr = np.full((400, 500, 3), 255, dtype=np.uint8)
    arr[100:300, 100:400] = 30
    mask = np.zeros((400, 500), dtype=np.uint8)
    mask[120:280, 150:350] = 255

    out, trimmed = aidge_mod._trim_cloth(arr, mask)
    assert trimmed
    assert out.shape[:2] == (176, 216)  # 160x200 + 各边 8px


def test_trim_cloth_leaves_uniform_and_full_frame_images_alone():
    uniform = np.full((120, 160, 3), 77, dtype=np.uint8)
    out, trimmed = aidge_mod._trim_cloth(uniform)
    assert not trimmed and out is uniform

    full = np.full((120, 160, 3), 255, dtype=np.uint8)
    full[4:116, 4:156] = 10  # 前景占满 98% 以上，再裁只会切到衣服
    out2, trimmed2 = aidge_mod._trim_cloth(full)
    assert not trimmed2 and out2.shape == full.shape


def test_run_sends_the_trimmed_cloth(cloud_settings, monkeypatch):
    """留白过多的图会让模型把衣服画小、按先验补形，出站前必须先裁。"""
    seen: dict = {}
    _stub_vendor(monkeypatch, seen)
    cloth = np.full((1600, 1200, 3), 255, dtype=np.uint8)
    cloth[600:1000, 500:1100] = 30  # 400x600 的衣服

    out = AidgeBackend().run(_ctx(garment={"image": cloth}))
    assert "aidge_cloth_trimmed" in out.notes
    sent = seen["sent"]["ClothImageUrl"]
    assert sent.shape[1] > sent.shape[0]  # 原图竖长，裁到衣服后是横长


def test_cache_key_follows_the_cloud_presentation():
    """补一张平铺图必须让旧缓存失效，否则线上仍返回按展陈形算出来的那张图。"""
    from app.services.pipeline import _cache_key

    person = np.zeros((60, 40, 3), dtype=np.uint8)
    base = dict(id="g", image=np.zeros((50, 30, 3), dtype=np.uint8),
                mask=np.zeros((50, 30), dtype=np.uint8))
    without = _cache_key(person, SimpleNamespace(cloud_cloth=None, **base), "fast")
    flat = np.full((50, 30, 3), 9, dtype=np.uint8)
    with_flat = _cache_key(person, SimpleNamespace(cloud_cloth=flat, **base), "fast")
    other_flat = _cache_key(person, SimpleNamespace(cloud_cloth=flat + 1, **base), "fast")
    assert len({without, with_flat, other_flat}) == 3


def test_success_is_judged_by_the_vendors_own_code_words():
    """生产实测 AiTryOn 成功回 Code="success"/Message="Success"，不是 "200"。

    只认 "200" 会把已经出图的调用判成失败并回落本地引擎，表面看不出问题，
    实际每次都白烧一次云端调用。
    """
    assert aidge_mod._is_success({"Code": "success", "Message": "Success"})
    assert aidge_mod._is_success({"Code": "200"})
    assert aidge_mod._is_success({"Code": 200})
    assert aidge_mod._is_success({"Success": True})
    assert aidge_mod._is_success({})  # 没有 Code 字段按成功处理，交给 ImageUrl 兜底
    assert not aidge_mod._is_success({"Code": "InvalidParameter"})
    assert not aidge_mod._is_success({"Code": "DownstreamUnavailable"})


def test_run_cleans_up_when_vendor_rejects(cloud_settings, monkeypatch):
    def fake_post(url, data=None, headers=None, timeout=None):
        return FakeResponse({"Code": "InvalidParameter", "Message": "bad", "RequestId": "r1"},
                            status_code=400)

    monkeypatch.setattr(aidge_mod.requests, "post", fake_post)
    with pytest.raises(RuntimeError) as exc:
        AidgeBackend().run(_ctx())
    assert "Aidge 调用失败" in str(exc.value)
    assert list(cloud_settings.outbox_dir.glob("*.jpg")) == []


def test_vendor_error_message_redacts_access_key():
    masked = aidge_mod.redact("ak=LTAI5tSuperSecretKeyValue message=oops")
    assert "LTAI<REDACTED>" in masked
    assert "SuperSecret" not in masked
