"""隐私合规：DELETE 接口 + person_source 不再公开可读。"""

from __future__ import annotations

import base64
import re


def _b64(raw: bytes) -> str:
    return "data:image/jpeg;base64," + base64.b64encode(raw).decode("ascii")


def _create_task(client, person_jpg_bytes, garment_id):
    resp = client.post(
        "/api/v1/tryon",
        json={"person_image": _b64(person_jpg_bytes), "garment_id": garment_id},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()


def test_delete_removes_record_and_directory(client, person_jpg_bytes, sample_garment_ids, settings):
    body = _create_task(client, person_jpg_bytes, sample_garment_ids[0])
    task_id = body["task_id"]

    results_dir = settings.results_dir / task_id
    private_dir = settings.person_sources_dir / task_id
    assert results_dir.is_dir()
    assert private_dir.is_dir()

    resp = client.delete(f"/api/v1/history/{task_id}")
    assert resp.status_code == 204

    assert not results_dir.is_dir(), "结果目录应被清理"
    assert not private_dir.is_dir(), "私密原图目录应被清理"

    fetched = client.get(f"/api/v1/history/{task_id}")
    assert fetched.status_code == 404


def test_delete_is_idempotent(client):
    resp = client.delete("/api/v1/history/nonexistent-task-id-12345")
    assert resp.status_code == 204


def test_delete_rejects_path_traversal(client):
    for bad_id in ["../etc", "..\\windows", "a/b", "a\\b", "a" * 65, "a b", "a!b"]:
        resp = client.delete(f"/api/v1/history/{bad_id}")
        assert resp.status_code == 404, f"应拒绝非法 task_id: {bad_id!r}, got {resp.status_code}"


def test_person_source_not_in_static_results(client, person_jpg_bytes, sample_garment_ids, settings):
    body = _create_task(client, person_jpg_bytes, sample_garment_ids[0])
    task_id = body["task_id"]

    results_dir = settings.results_dir / task_id
    assert not (results_dir / "person_source.jpg").is_file(), "原图不应出现在公开结果目录"

    private_dir = settings.person_sources_dir / task_id
    assert (private_dir / "person_source.jpg").is_file(), "原图应落在私密目录"

    resp = client.get(f"/api/v1/history/{task_id}/person-source")
    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/jpeg")
    assert len(resp.content) > 512


def test_person_source_requires_existing_record(client):
    resp = client.get("/api/v1/history/nonexistent-999/person-source")
    assert resp.status_code == 404


def test_person_source_rejects_path_traversal(client):
    for bad_id in ["../etc", "a/b", "..", "a b", "a!b"]:
        resp = client.get(f"/api/v1/history/{bad_id}/person-source")
        assert resp.status_code == 404, f"应拒绝非法 task_id: {bad_id!r}"


def test_history_list_returns_api_person_url(client, person_jpg_bytes, sample_garment_ids):
    body = _create_task(client, person_jpg_bytes, sample_garment_ids[0])
    task_id = body["task_id"]

    history = client.get("/api/v1/history", params={"limit": 50})
    assert history.status_code == 200
    items = history.json()["items"]
    match = [i for i in items if i["task_id"] == task_id]
    assert len(match) == 1
    person_url = match[0]["person_url"]
    assert re.match(r"/api/v1/history/.+/person-source", person_url), (
        f"person_url 应指向 API 端点，实际: {person_url}"
    )
