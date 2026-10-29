"""检索条目编号与按编号回查 · 含配饰九卷进召回

配饰语料读仓库里的 accessories.json（真实文件，不造假数据）；
缺失场景用把候选路径置空来触发，不走 mock。
"""
from __future__ import annotations

from app.ai_engine.retrieval import retrieve, sources_of
from app.db.models import PatternLibrary


def _by_type(items: list[dict], t: str) -> list[dict]:
    return [i for i in items if i["type"] == t]


def test_检索条目带中文编号(db):
    items = retrieve("马面裙", db)
    assert items[0]["code"] == "档案-0001"


def test_资讯条目也带编号(db):
    items = retrieve("定陵的发掘", db)
    assert _by_type(items, "news")[0]["code"] == "资讯-0001"


def test_纹样沿用名录编号(db):
    db.add(PatternLibrary(name="宝相花", category="组合纹", dynasty="唐", code=88))
    db.commit()
    items = retrieve("宝相花", db)
    assert items[0]["code"] == "纹样-0088"


def test_问句里的编号能直接定位条目(db):
    items = retrieve("档案-0003 讲了什么", db)
    assert [(i["type"], i["id"], i["title"]) for i in items] == [("costume", 3, "褙子")]


def test_一次回查多个编号(db):
    items = retrieve("把 档案-0001 和 面料-0001 放一起看", db)
    assert {(i["type"], i["id"]) for i in items} == {("costume", 1), ("fabric", 1)}


def test_编号指向不存在的条目就退回正常召回(db):
    items = retrieve("档案-9999 和 马面裙", db)
    assert any(i["title"] == "马面裙" for i in items)


def test_配饰条目进召回(db):
    items = retrieve("步摇怎么戴", db)
    acc = _by_type(items, "accessory")[0]
    assert acc["code"] == "头饰-04"
    assert acc["title"] == "步摇"
    assert acc["link"] == "/accessories/index.html#/a/%E5%A4%B4%E9%A5%B0-04"
    assert "垂珠" in acc["text"]


def test_配饰编号也能回查(db):
    items = retrieve("头饰-04 是什么", db)
    assert [(i["type"], i["id"]) for i in items] == [("accessory", "头饰-04")]


def test_配饰数据文件缺失不影响四库召回(db, monkeypatch):
    from app.services import accessory_docs

    monkeypatch.setattr(accessory_docs, "DATA_CANDIDATES", [])
    items = retrieve("马面裙", db)
    assert items and items[0]["type"] == "costume"


def test_配饰引用标记为站外链接(db):
    assert sources_of(_by_type(retrieve("步摇", db), "accessory"))[0]["external"] is True
    assert sources_of(_by_type(retrieve("马面裙", db), "costume"))[0]["external"] is False


def test_可点引用带上编号(db):
    items = retrieve("马面裙", db)
    assert sources_of(items)[0]["code"] == "档案-0001"


def test_推荐卡片带编号(client):
    body = client.get("/api/aiqa/recommend", params={"q": "马面裙"}).json()
    assert body["cards"][0]["code"] == "档案-0001"
    assert "external" in body["cards"][0]
