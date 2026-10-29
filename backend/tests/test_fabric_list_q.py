"""面料列表关键词检索（供答后推荐卡复用）"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Fabrics


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    session.add_all([
        Fabrics(name="妆花缎", category="织金", dynasty_peak="元—明"),
        Fabrics(name="罗", category="纱罗", dynasty_peak="宋"),
    ])
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    from app.api.fabric import router

    app = FastAPI()
    app.include_router(router, prefix="/api/fabrics")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)


def test_无关键词返回全部(client):
    assert [i["name"] for i in client.get("/api/fabrics/list").json()["items"]] == ["妆花缎", "罗"]


def test_按名称关键词过滤(client):
    body = client.get("/api/fabrics/list", params={"q": "妆花"}).json()
    assert [i["name"] for i in body["items"]] == ["妆花缎"]


def test_未命中返回空列表(client):
    assert client.get("/api/fabrics/list", params={"q": "不存在的面料"}).json()["items"] == []
