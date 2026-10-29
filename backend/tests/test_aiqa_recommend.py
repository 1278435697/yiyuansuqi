"""溯源问答 · 答后推荐检索（四类站内资料卡 + 推荐追问）"""
from __future__ import annotations

from app.db.models import Costumes


def _types(cards):
    return sorted({c["type"] for c in cards})


def test_命中四类库各出一张卡(client):
    res = client.get("/api/aiqa/recommend", params={"q": "马面裙配团花纹，用妆花缎可以吗"})
    assert res.status_code == 200
    body = res.json()
    assert body["keywords"][:1] == ["马面裙"]
    assert {"costume", "fabric", "news", "pattern"} <= set(_types(body["cards"]))
    for card in body["cards"]:
        assert card["exact"] is True
        assert card["title"] and card["link"]
        assert "image_url" in card


def test_卡片带站内详情链接(client):
    body = client.get("/api/aiqa/recommend", params={"q": "马面裙"}).json()
    card = [c for c in body["cards"] if c["type"] == "costume"][0]
    assert card["title"] == "马面裙"
    assert card["link"].startswith("/archive/")


def test_每类最多三张且总数不超上限(client, db):
    db.add_all([Costumes(name=f"妆花马面裙{i}", dynasty="明", category="下裳") for i in range(4)])
    db.commit()
    body = client.get("/api/aiqa/recommend", params={"q": "马面裙"}).json()
    assert len([c for c in body["cards"] if c["type"] == "costume"]) <= 3
    assert len(body["cards"]) <= 8


def test_推荐追问来自命中实体且可点(client):
    body = client.get("/api/aiqa/recommend", params={"q": "马面裙的面料和纹样"}).json()
    assert 1 <= len(body["asks"]) <= 4
    assert all("马面裙" in ask for ask in body["asks"])


def test_追问不把资讯整条标题当实体(client):
    body = client.get("/api/aiqa/recommend", params={"q": "马面裙"}).json()
    news_titles = [c["title"] for c in body["cards"] if c["type"] == "news"]
    assert news_titles
    assert not [a for a in body["asks"] for t in news_titles if a.startswith(t)]


def test_无朝代无专名时返回空(client):
    body = client.get("/api/aiqa/recommend", params={"q": "今天天气好吗"}).json()
    assert body == {"keywords": [], "dynasties": [], "cards": [], "asks": []}


def test_只提朝代时回退同朝代并标注(client):
    body = client.get("/api/aiqa/recommend", params={"q": "明代有哪些服饰"}).json()
    assert body["dynasties"] == ["明"]
    assert body["cards"]
    assert all(c["exact"] is False for c in body["cards"])
    assert {c["type"] for c in body["cards"]} <= {"costume", "pattern", "fabric", "news"}


def test_空问题返回空而非报错(client):
    res = client.get("/api/aiqa/recommend", params={"q": "   "})
    assert res.status_code == 200
    assert res.json()["cards"] == []
