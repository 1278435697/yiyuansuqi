"""API 契约测试：TryOnResult 全字段、结果图可访问、错误响应脱敏。"""

from __future__ import annotations

import base64

REQUIRED_FIELDS = (
    "task_id",
    "status",
    "result_url",
    "person_mask_url",
    "pose_overlay_url",
    "garment_warp_url",
    "backend_used",
    "warnings",
    "timings",
    "trace_card",
    "error_code",
    "message",
)


def _b64(raw: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def test_tryon_response_has_all_contract_fields(client, person_jpg_bytes, sample_garment_ids):
    payload = {
        "person_image": _b64(person_jpg_bytes),
        "garment_id": sample_garment_ids[0],
        "quality": "fast",
    }
    resp = client.post("/api/v1/tryon", json=payload)
    assert resp.status_code == 200, resp.text
    body = resp.json()

    for field in REQUIRED_FIELDS:
        assert field in body, f"缺少契约字段 {field}"

    assert body["status"] == "succeeded"
    assert body["task_id"]
    assert body["backend_used"] in {"hrviton", "tps", "mock"}
    assert isinstance(body["warnings"], list)
    assert isinstance(body["timings"], dict)
    assert {"segmentation", "pose", "inference", "postprocess", "total"} <= set(body["timings"])
    assert body["result_url"].startswith("/static/results/")
    assert body["error_code"] is None and body["message"] is None


def test_result_and_intermediate_images_are_downloadable(client, person_jpg_bytes, sample_garment_ids):
    resp = client.post(
        "/api/v1/tryon",
        json={"person_image": _b64(person_jpg_bytes), "garment_id": sample_garment_ids[1]},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    for key in ("result_url", "person_mask_url", "pose_overlay_url", "garment_warp_url"):
        url = body.get(key)
        assert url, f"{key} 未返回"
        asset = client.get(url)
        assert asset.status_code == 200, f"{key} -> {asset.status_code}"
        assert len(asset.content) > 512


def test_trace_card_attached_for_library_garment(client, person_jpg_bytes, sample_garment_ids):
    gid = sample_garment_ids[0]
    body = client.post(
        "/api/v1/tryon", json={"person_image": _b64(person_jpg_bytes), "garment_id": gid}
    ).json()
    trace = body["trace_card"]
    assert trace is not None
    assert trace["garment_id"] == gid
    assert trace["name"] and trace["dynasty"]
    assert "source_text" in trace and isinstance(trace["references"], list)


def test_task_query_and_history_roundtrip(client, person_jpg_bytes, sample_garment_ids):
    body = client.post(
        "/api/v1/tryon",
        json={"person_image": _b64(person_jpg_bytes), "garment_id": sample_garment_ids[2]},
    ).json()
    task_id = body["task_id"]

    fetched = client.get(f"/api/v1/tryon/{task_id}")
    assert fetched.status_code == 200
    assert fetched.json()["result_url"] == body["result_url"]

    history = client.get("/api/v1/history", params={"limit": 50})
    assert history.status_code == 200
    page = history.json()
    assert isinstance(page["items"], list) and page["total"] >= 1
    assert task_id in {item["task_id"] for item in page["items"]}


def test_validation_error_is_masked(client, person_jpg_bytes):
    resp = client.post("/api/v1/tryon", json={"person_image": _b64(person_jpg_bytes)})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error_code"] == "VALIDATION_ERROR"
    assert body["request_id"]
    # 脱敏：响应体不得包含 Python 异常栈或文件路径
    text = resp.text
    assert "Traceback" not in text and ".py" not in text


def test_unknown_garment_returns_404_code(client, person_jpg_bytes):
    resp = client.post(
        "/api/v1/tryon",
        json={"person_image": _b64(person_jpg_bytes), "garment_id": "no-such-garment"},
    )
    assert resp.status_code == 404
    assert resp.json()["error_code"] == "GARMENT_NOT_FOUND"


def test_health_reports_components(client):
    resp = client.get("/api/v1/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] in {"ok", "degraded"}
    assert body["vton_backend_resolved"] in {"hrviton", "tps", "mock"}
    for key in ("segmentation", "pose", "vton", "torch", "opencv", "database"):
        assert key in body["components"], f"健康检查缺少 {key}"
    assert body["garments_count"] >= 1


def test_batch_tryon(client, person_jpg_bytes, sample_garment_ids):
    resp = client.post(
        "/api/v1/tryon/batch",
        json={
            "person_image": _b64(person_jpg_bytes),
            "garment_ids": sample_garment_ids[:3] + sample_garment_ids[:1],  # 含重复项，应被去重
            "quality": "fast",
        },
    )
    assert resp.status_code == 200, resp.text
    results = resp.json()
    assert len(results) == 3
    assert all(item["status"] == "succeeded" for item in results)
    assert len({item["task_id"] for item in results}) == 3


def test_multipart_endpoint_equivalent(client, person_jpg_bytes, sample_garment_ids):
    resp = client.post(
        "/api/v1/tryon/upload",
        files={"person_file": ("person.jpg", person_jpg_bytes, "image/jpeg")},
        data={"garment_id": sample_garment_ids[0], "quality": "fast"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["status"] == "succeeded"
    assert body["result_url"].startswith("/static/results/")


def test_garments_list_and_detail(client, sample_garment_ids):
    listing = client.get("/api/v1/garments")
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == len(sample_garment_ids)
    for item in items:
        assert item["image_url"].startswith("/static/garments/")
        assert len(item["keypoints"]) == 9

    gid = sample_garment_ids[0]
    detail = client.get(f"/api/v1/garments/{gid}")
    assert detail.status_code == 200
    assert detail.json()["id"] == gid
    trace = client.get(f"/api/v1/garments/{gid}/trace")
    assert trace.status_code == 200 and trace.json()["garment_id"] == gid


def test_disk_cache_hit_and_force_refresh(client, person_jpg_bytes, sample_garment_ids, settings, monkeypatch):
    """开缓存后：同一（人像, 服饰, 画质）二次提交必须返回同一 task，force_refresh 才重算。

    流水线是确定性的，“再点一次没变化”属于预期行为，但必须让调用方看得见。
    """
    monkeypatch.setattr(settings, "enable_disk_cache", True, raising=False)
    payload = {
        "person_image": _b64(person_jpg_bytes),
        "garment_id": sample_garment_ids[4],
        "quality": "fast",
    }

    first = client.post("/api/v1/tryon", json=payload).json()
    assert first["status"] == "succeeded"
    assert "result_from_cache" not in first["warnings"]

    again = client.post("/api/v1/tryon", json=payload).json()
    assert again["task_id"] == first["task_id"]
    assert "result_from_cache" in again["warnings"]

    forced = client.post("/api/v1/tryon", json={**payload, "force_refresh": True}).json()
    assert forced["status"] == "succeeded"
    assert forced["task_id"] != first["task_id"]
    assert "cache_bypassed" in forced["warnings"]
    assert "result_from_cache" not in forced["warnings"]

    # 重算结果不能把 cache_bypassed 告警写进记录，否则下次命中缓存会误报
    replay = client.get(f"/api/v1/tryon/{forced['task_id']}").json()
    assert "cache_bypassed" not in replay["warnings"]
