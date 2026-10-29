"""溯源问答 · 检索与推荐的公共夹具

统一用 SQLite 内存库 + 四库各若干条真数据，不碰 MySQL、不发外部请求。
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.database import Base, get_db
from app.db.models import Costumes, CostumeRelations, Fabrics, News, PatternLibrary


@pytest.fixture()
def db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    mamianqun = Costumes(
        name="马面裙", dynasty="明", category="下裳", fabric="妆花缎", pattern="膝襕妆花",
        color="红", wearer="命妇", source_type="出土", image_url="/images/relics/mamianqun.jpg",
        description="两侧打褶、前后裙门平整",
    )
    session.add(mamianqun)
    session.flush()
    session.add_all([
        Costumes(name="袄裙", dynasty="明", category="上衣"),
        Costumes(name="褙子", dynasty="宋", category="上衣"),
        CostumeRelations(costume_id=mamianqun.id, relation_type="面料",
                         target_value="妆花缎", source_ref="《明史·舆服志》"),
        PatternLibrary(name="团花纹", category="植物纹", dynasty="唐代", meaning="团圆美满"),
        Fabrics(name="妆花缎", category="织金", raw_material="桑蚕丝",
                dynasty_peak="元—明", technique="挖花盘织", description="明代织造巅峰"),
        News(title="定陵出土马面裙实物公开", source="考古学报", dynasty_tags="明", entity_tags="定陵,马面裙",
             summary="实物与织造工艺复原研究"),
    ])
    session.commit()
    yield session
    session.close()


@pytest.fixture()
def client(db):
    """只挂 aiqa 路由的极小 app，依赖注入指向内存库。"""
    from app.api.ai_qa import router

    app = FastAPI()
    app.include_router(router, prefix="/api/aiqa")
    app.dependency_overrides[get_db] = lambda: db
    return TestClient(app)
