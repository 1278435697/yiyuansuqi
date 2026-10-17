"""TTL 清理脚本测试：过期目录删除、未过期保留、DB 同步、dry-run、非法 TTL。"""

from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path

import pytest

from app.config import get_settings


def _make_task_dir(task_id: str, age_days: float) -> Path:
    settings = get_settings()
    d = settings.results_dir / task_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "result.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    if age_days > 0:
        old_time = time.time() - age_days * 86400
        os.utime(d, (old_time, old_time))
    return d


def _make_private_dir(task_id: str, age_days: float) -> Path:
    settings = get_settings()
    d = settings.person_sources_dir / task_id
    d.mkdir(parents=True, exist_ok=True)
    (d / "person_source.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"\x00" * 100)
    if age_days > 0:
        old_time = time.time() - age_days * 86400
        os.utime(d, (old_time, old_time))
    return d


def _seed_db_record(task_id: str, days_ago: float):
    from datetime import datetime, timedelta

    from app.db.base import session_factory
    from app.db.models import TryOnRecord

    async def _insert():
        async with session_factory()() as session:
            record = TryOnRecord(
                task_id=task_id,
                garment_id=None,
                person_url="",
                result_url="",
                backend_used="mock",
                quality="fast",
                status="succeeded",
                warnings=[],
                timings={},
            )
            record.created_at = datetime.utcnow() - timedelta(days=days_ago)
            session.add(record)
            await session.commit()

    asyncio.run(_insert())


def _run_cleanup(ttl_days: int, dry_run: bool):
    from scripts.cleanup_results import cleanup

    return asyncio.run(cleanup(ttl_days=ttl_days, dry_run=dry_run))


def _check_record_exists(task_id: str) -> bool:
    from app.db.base import session_factory
    from app.db.repos import get_record_by_task

    async def _check():
        async with session_factory()() as session:
            return await get_record_by_task(session, task_id) is not None

    return asyncio.run(_check())


def test_expired_directory_is_deleted(client):
    task_id = "ttl-expired-test-001"
    _make_task_dir(task_id, age_days=60)
    _make_private_dir(task_id, age_days=60)
    _seed_db_record(task_id, days_ago=60)

    dirs, rows = _run_cleanup(ttl_days=30, dry_run=False)
    assert dirs >= 1
    assert rows >= 1

    settings = get_settings()
    assert not (settings.results_dir / task_id).is_dir()
    assert not (settings.person_sources_dir / task_id).is_dir()


def test_non_expired_directory_is_kept(client):
    task_id = "ttl-fresh-test-002"
    _make_task_dir(task_id, age_days=1)
    _make_private_dir(task_id, age_days=1)
    _seed_db_record(task_id, days_ago=1)

    _run_cleanup(ttl_days=30, dry_run=False)

    settings = get_settings()
    assert (settings.results_dir / task_id).is_dir()
    assert (settings.person_sources_dir / task_id).is_dir()


def test_db_rows_synced_with_cleanup(client):
    task_id = "ttl-db-sync-test-003"
    _make_task_dir(task_id, age_days=60)
    _seed_db_record(task_id, days_ago=60)

    _, rows = _run_cleanup(ttl_days=30, dry_run=False)
    assert rows >= 1
    assert not _check_record_exists(task_id)


def test_dry_run_does_not_delete(client):
    task_id = "ttl-dryrun-test-004"
    _make_task_dir(task_id, age_days=60)
    _make_private_dir(task_id, age_days=60)
    _seed_db_record(task_id, days_ago=60)

    _run_cleanup(ttl_days=30, dry_run=True)

    settings = get_settings()
    assert (settings.results_dir / task_id).is_dir(), "dry-run 不应删除目录"
    assert (settings.person_sources_dir / task_id).is_dir(), "dry-run 不应删除原图目录"


def test_invalid_ttl_rejected_by_config():
    from pydantic import ValidationError

    from app.config import Settings

    with pytest.raises(ValidationError):
        Settings(results_ttl_days=0)
    with pytest.raises(ValidationError):
        Settings(results_ttl_days=-5)
