"""迁移脚本测试：搬移残留 person_source.jpg + 改写 DB URL。"""

from __future__ import annotations

import asyncio
from pathlib import Path

from app.config import get_settings


def _seed_legacy_record(task_id: str, person_url: str):
    from app.db.base import session_factory
    from app.db.models import TryOnRecord

    async def _insert():
        async with session_factory()() as session:
            record = TryOnRecord(
                task_id=task_id,
                garment_id=None,
                person_url=person_url,
                result_url="",
                backend_used="mock",
                quality="fast",
                status="succeeded",
                warnings=[],
                timings={},
            )
            session.add(record)
            await session.commit()

    asyncio.run(_insert())


def _make_legacy_person_source(task_id: str) -> Path:
    settings = get_settings()
    d = settings.results_dir / task_id
    d.mkdir(parents=True, exist_ok=True)
    src = d / "person_source.jpg"
    src.write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    return src


def _get_record_person_url(task_id: str) -> str | None:
    from app.db.base import session_factory
    from app.db.repos import get_record_by_task

    async def _get():
        async with session_factory()() as session:
            record = await get_record_by_task(session, task_id)
            return record.person_url if record else None

    return asyncio.run(_get())


def test_migrate_moves_file_and_updates_url(client):
    task_id = "migrate-test-001"
    _make_legacy_person_source(task_id)
    _seed_legacy_record(task_id, "/tryon-results/old-task/person_source.jpg")

    from scripts.migrate_person_sources import migrate

    moved, updated, skipped = asyncio.run(migrate(dry_run=False))
    assert moved >= 1
    assert updated >= 1

    settings = get_settings()
    # 原文件应已搬走
    assert not (settings.results_dir / task_id / "person_source.jpg").is_file()
    # 私密目录应有文件
    assert (settings.person_sources_dir / task_id / "person_source.jpg").is_file()
    # DB URL 应已改写
    url = _get_record_person_url(task_id)
    assert url == f"/api/v1/history/{task_id}/person-source", f"URL 未改写: {url}"


def test_migrate_dry_run_does_not_move(client):
    task_id = "migrate-test-002"
    src = _make_legacy_person_source(task_id)
    _seed_legacy_record(task_id, "/tryon-results/old-task/person_source.jpg")

    from scripts.migrate_person_sources import migrate

    asyncio.run(migrate(dry_run=True))

    settings = get_settings()
    # dry-run 不应搬移
    assert src.is_file(), "dry-run 不应搬移文件"
    # DB URL 不应改写
    url = _get_record_person_url(task_id)
    assert url == "/tryon-results/old-task/person_source.jpg", "dry-run 不应改写 URL"


def test_migrate_idempotent(client):
    task_id = "migrate-test-003"
    _make_legacy_person_source(task_id)
    _seed_legacy_record(task_id, "/tryon-results/old-task/person_source.jpg")

    from scripts.migrate_person_sources import migrate

    # 第一次迁移
    asyncio.run(migrate(dry_run=False))
    # 第二次迁移（幂等）
    moved2, updated2, skipped2 = asyncio.run(migrate(dry_run=False))
    # 第二次不应再搬移（源文件已不存在）
    assert moved2 == 0 or skipped2 >= 1


def test_migrate_missing_file_no_error(client):
    task_id = "migrate-test-004"
    # 只建目录，不放 person_source.jpg
    settings = get_settings()
    (settings.results_dir / task_id).mkdir(parents=True, exist_ok=True)

    from scripts.migrate_person_sources import migrate

    # 不应报错
    moved, updated, skipped = asyncio.run(migrate(dry_run=False))
    assert moved == 0


def test_migrate_already_api_url_skipped(client):
    task_id = "migrate-test-005"
    # URL 已经是新的 API 格式，不应改写
    _seed_legacy_record(task_id, f"/api/v1/history/{task_id}/person-source")

    from scripts.migrate_person_sources import migrate

    moved, updated, skipped = asyncio.run(migrate(dry_run=False))
    assert updated == 0
    url = _get_record_person_url(task_id)
    assert url == f"/api/v1/history/{task_id}/person-source"
