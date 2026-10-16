"""pytest 公共夹具。

关键约束：必须在导入 app 之前设置环境变量（Settings 为 lru_cache 单例），
因此所有 env 写入都发生在 conftest 模块顶层。
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

import pytest

_TMP_ROOT = Path(tempfile.mkdtemp(prefix="yisu_test_"))

os.environ["YISU_DATA_DIR"] = str(_TMP_ROOT / "data")
os.environ["YISU_WEIGHTS_DIR"] = str(_TMP_ROOT / "weights")
os.environ["YISU_LOGS_DIR"] = str(_TMP_ROOT / "logs")
os.environ["YISU_DATABASE_URL"] = f"sqlite+aiosqlite:///{_TMP_ROOT / 'data' / 'test.db'}"
os.environ["YISU_VTON_BACKEND"] = "auto"
os.environ["YISU_OUTPUT_LONG_SIDE"] = "512"
os.environ["YISU_ENABLE_DISK_CACHE"] = "false"
os.environ["YISU_MAX_UPLOAD_MB"] = "4"

for _sub in ("data", "weights", "logs"):
    (_TMP_ROOT / _sub).mkdir(parents=True, exist_ok=True)


@pytest.fixture(scope="session")
def settings():
    from app.config import get_settings

    cfg = get_settings()
    cfg.ensure_dirs()
    return cfg


@pytest.fixture(scope="session")
def sample_garment_ids(settings):
    """确保素材索引存在（与 gen_sample_garments 同一套标注）。"""
    from app.services.garments import load_index, valid_entries
    from scripts.gen_sample_garments import SPECS, render_spec

    index_path = settings.garments_dir / "index.json"
    if not index_path.is_file():
        import json

        entries = [render_spec(spec, settings.data_dir) for spec in SPECS]
        index_path.write_text(
            json.dumps({"version": 1, "garments": entries}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    entries, skipped = valid_entries(load_index())
    assert entries, f"示例素材校验全失败: {skipped}"
    return [entry["id"] for entry in entries]


@pytest.fixture(scope="session")
def person_jpg_bytes(settings) -> bytes:
    """合成一张正身人像（有头/肩/臂/腿），供分割与姿态使用。"""
    from scripts.gen_sample_garments import render_sample_person

    rel = render_sample_person(settings.data_dir)
    return (settings.data_dir / rel).read_bytes()


@pytest.fixture(scope="session")
def client(sample_garment_ids):
    from fastapi.testclient import TestClient

    from app.db.base import create_all
    from app.main import app
    from app.services.seed import seed_garments

    import asyncio

    async def _prepare() -> None:
        await create_all()
        await seed_garments(force=True)

    asyncio.run(_prepare())
    with TestClient(app) as test_client:
        yield test_client
