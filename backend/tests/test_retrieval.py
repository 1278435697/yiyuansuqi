"""检索中枢 · retrieve()（对话上下文与答后推荐共用同一份召回结果）"""
from __future__ import annotations

from app.ai_engine.retrieval import retrieve
from app.db.models import Costumes


def test_专名命中带站内正文与链接(db):
    items = retrieve("马面裙的形制和面料是什么？", db)
    costume = [i for i in items if i["type"] == "costume"]
    assert costume, items
    hit = costume[0]
    assert hit["title"] == "马面裙"
    assert hit["exact"] is True
    assert hit["link"] == f"/archive/{hit['id']}"
    assert "两侧打褶" in hit["text"]
    assert "妆花缎" in hit["text"]
    assert "《明史·舆服志》" in hit["text"]


def test_四类库各自给出条目(db):
    items = retrieve("马面裙配团花纹，用妆花缎织的，定陵那篇资讯怎么说", db)
    # 配饰九卷进召回后可能多出一类，这里只保证四库都出条目（配饰见 test_retrieval_codes）
    assert {"costume", "pattern", "fabric", "news"} <= {i["type"] for i in items}
    for item in items:
        assert item["id"] and item["title"] and item["text"] and item["link"]
        assert {"subtitle", "image_url", "score", "exact"} <= set(item)


def test_条目正文带本类关键字段(db):
    items = {i["type"]: i for i in retrieve("团花纹妆花缎", db)}
    assert "团圆美满" in items["pattern"]["text"]
    assert "挖花盘织" in items["fabric"]["text"]
    assert "桑蚕丝" in items["fabric"]["text"]


def test_只命中朝代时标注非精确(db):
    items = retrieve("明代有哪些服饰", db)
    assert items
    assert all(i["exact"] is False for i in items)
    assert {i["type"] for i in items} <= {"costume", "pattern", "fabric", "news"}


def test_完全无命中返回空(db):
    assert retrieve("今天天气好吗", db) == []


def test_空问题返回空(db):
    assert retrieve("   ", db) == []


def test_每类最多三条且总数不超上限(db):
    for i in range(6):
        db.add(Costumes(name=f"妆花马面裙{i}", dynasty="明", category="下裳"))
    db.commit()
    items = retrieve("马面裙", db, per_type=3, limit=8)
    assert len([i for i in items if i["type"] == "costume"]) <= 3
    assert len(items) <= 8


def test_单条正文不超三百字(db):
    long = Costumes(
        name="曳撒", dynasty="明", category="袍服",
        description="明" * 500,
    )
    db.add(long)
    db.commit()
    item = [i for i in retrieve("曳撒的形制", db) if i["title"] == "曳撒"][0]
    assert len(item["text"]) <= 300


def test_仅资讯标签里的专名也能召回(db):
    items = retrieve("定陵那次发掘怎么说", db)
    news = [i for i in items if i["type"] == "news"]
    assert news, items
    assert news[0]["exact"] is True
    assert news[0]["link"].startswith("/news/")


def test_按分值从高到低返回(db):
    items = retrieve("马面裙与团花纹", db)
    scores = [i["score"] for i in items]
    assert scores == sorted(scores, reverse=True)
