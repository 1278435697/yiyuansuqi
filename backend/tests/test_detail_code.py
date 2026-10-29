"""详情页编号 · 三个详情数据源都要带上前端可直接显示的编号

面料没有单条详情接口（前端从 /list 里按 id 取），所以编号挂在列表条目上。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.database import get_db


@pytest.fixture()
def web(db):
    from app.api import archive, fabric, home, pattern_library

    app = FastAPI()
    app.include_router(archive.router, prefix="/api/archive")
    app.include_router(home.router, prefix="/api/home")
    app.include_router(fabric.router, prefix="/api/fabrics")
    app.include_router(pattern_library.router, prefix="/api/pattern-library")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_档案详情带编号(web):
    body = web.get("/api/archive/costumes/1").json()
    assert body["code"] == "档案-0001"


def test_资讯详情带编号(web):
    body = web.get("/api/home/news/1").json()
    assert body["code"] == "资讯-0001"


def test_面料条目带编号(web):
    body = web.get("/api/fabrics/list").json()
    item = [i for i in body["items"] if i["name"] == "妆花缎"][0]
    assert item["code"] == "面料-0001"


def test_纹样详情编号与AI引用的写法一致(web, db):
    """纹样沿用名录编号，但详情页要显示 AI 引用的那个整串写法，不能只显示裸数字。"""
    from app.db.models import PatternLibrary

    p = db.query(PatternLibrary).filter_by(name="团花纹").one()
    p.code = 88
    db.commit()
    body = web.get(f"/api/pattern-library/{p.id}").json()
    assert body["code_ref"] == "纹样-0088"
