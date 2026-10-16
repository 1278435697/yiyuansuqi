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
    assert body["result_url"].startswith("/tryon-results/")
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
    assert body["result_url"].startswith("/tryon-results/")


def test_garments_list_and_detail(client, sample_garment_ids):
    listing = client.get("/api/v1/garments")
    assert listing.status_code == 200
    items = listing.json()
    assert len(items) == len(sample_garment_ids)
    for item in items:
        assert item["image_url"].startswith("/tryon-assets/garments/")
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


def test_static_surface_is_narrowed(client, sample_garment_ids, settings):
    """对外只挂素材/示例/结果三类，旧的整目录 /static 必须撤掉。

    data/uploads/ 下是用户真人照片原图，以前跟着 /static 一起被公开，是并入平台前必须收掉的面。
    """
    canary = settings.uploads_dir / "canary_private.jpg"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_bytes(b"private-photo")

    assert client.get(f"/static/{canary.name}").status_code == 404
    assert client.get(f"/static/uploads/{canary.name}").status_code == 404

    first = sample_garment_ids[0]
    image_url = client.get(f"/api/v1/garments/{first}").json()["image_url"]
    assert client.get(image_url).status_code == 200


def test_error_body_carries_detail_alias(client):
    """错误体同时给 message 和 detail：平台前端拦截器只读 detail，本模块只读 message。"""
    resp = client.get("/api/v1/garments/no-such-garment")
    assert resp.status_code == 404
    body = resp.json()
    assert body["detail"] == body["message"]
    assert body["error_code"] and body["request_id"]


def test_legacy_static_urls_in_db_are_rewritten(client, person_jpg_bytes, sample_garment_ids, settings):
    """库里的旧 /static 地址必须在读取时改写，不能原样递给前端。

    静态面拆分前落的记录把 URL 存死了，挂载撤掉后这些链接全 404；
    命中磁盘缓存时旧地址还会被当成新结果返回，所以改写点在 history 读取层。
    """
    import sqlite3

    payload = {
        "person_image": _b64(person_jpg_bytes),
        "garment_id": sample_garment_ids[0],
        "quality": "fast",
    }
    task_id = client.post("/api/v1/tryon", json=payload).json()["task_id"]

    # 直接把库里这一行改回迁移前的写法（当时的挂载是整个 data/）
    with sqlite3.connect(settings.data_dir / "test.db", timeout=15) as conn:
        conn.execute(
            "UPDATE tryon_records SET person_url=?, result_url=?, mask_url=? WHERE task_id=?",
            (
                f"/static/uploads/{task_id}_origin.jpg",
                f"/static/results/{task_id}/result.jpg",
                f"/static/results/{task_id}/person_mask.png",
                task_id,
            ),
        )
        conn.commit()

    item = next(r for r in client.get("/api/v1/history").json()["items"] if r["task_id"] == task_id)
    assert item["result_url"] == f"/tryon-results/{task_id}/result.jpg"
    assert item["person_url"] == ""  # 原图不再对外直读，前端走「原图缺失」占位

    detail = client.get(f"/api/v1/tryon/{task_id}").json()
    assert detail["result_url"] == f"/tryon-results/{task_id}/result.jpg"
    assert detail["person_mask_url"] == f"/tryon-results/{task_id}/person_mask.png"


def test_normalize_legacy_url_mapping(settings, monkeypatch):
    """归一化函数的四种入参：旧结果/旧素材/旧原图/新地址（幂等）。"""
    from app.utils.static import normalize_legacy_url

    assert normalize_legacy_url("/static/results/t1/result.jpg") == "/tryon-results/t1/result.jpg"
    assert normalize_legacy_url("/static/garments/robe.png") == "/tryon-assets/garments/robe.png"
    assert normalize_legacy_url("/static/uploads/me.jpg") == ""
    assert normalize_legacy_url("/tryon-results/t1/result.jpg") == "/tryon-results/t1/result.jpg"
    assert normalize_legacy_url(None) is None

    # 前缀跟着配置走：生产把结果图交给平台 /uploads/tryon 时，改写结果也要跟着变
    monkeypatch.setattr(settings, "results_url_prefix", "/uploads/tryon")
    assert normalize_legacy_url("/static/results/t1/result.jpg") == "/uploads/tryon/t1/result.jpg"


def test_empty_cors_origins_env_is_accepted(monkeypatch, tmp_path):
    """同源部署时 .env 里写 `YISU_CORS_ORIGINS=`（清空），不能让 Settings 直接报错。

    pydantic-settings 对 list 字段默认会先做 json.loads，空串不是合法 JSON，
    会在 source 层抛 SettingsError，服务根本起不来。加 NoDecode 后走我们的
    before-validator，空串 → 空列表（即不放开 CORS）。
    """
    monkeypatch.setenv("YISU_CORS_ORIGINS", "")
    from app.config import Settings

    s = Settings()
    assert s.cors_origins == []

    monkeypatch.setenv("YISU_CORS_ORIGINS", "http://localhost:5173, http://127.0.0.1:3000")
    s = Settings()
    assert s.cors_origins == ["http://localhost:5173", "http://127.0.0.1:3000"]

    # 未设环境变量时走默认（开发用 vite 端口）
    monkeypatch.delenv("YISU_CORS_ORIGINS", raising=False)
    s = Settings()
    assert s.cors_origins == ["http://localhost:5173", "http://127.0.0.1:5173"]

    # 云端实际报的是 DotEnvSettingsSource（不是环境变量），这里用文件路径复现一遍
    dotfile = tmp_path / "prod.env"
    dotfile.write_text("YISU_CORS_ORIGINS=\nYISU_RESULTS_URL_PREFIX=/uploads/tryon\n", encoding="utf-8")
    s = Settings(_env_file=dotfile)
    assert s.cors_origins == []
    assert s.results_url_prefix == "/uploads/tryon"
