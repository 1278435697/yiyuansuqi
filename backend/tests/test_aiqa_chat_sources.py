"""引用可点 · /api/aiqa/chat 返回结构化 sources（source_ref 字符串保持兼容）"""
from __future__ import annotations

import pytest

from app.ai_engine import graphrag_engine


@pytest.fixture(autouse=True)
def no_llm(monkeypatch):
    monkeypatch.setattr(graphrag_engine, "chat_completion",
                        lambda messages, *a, **k: "依据站内档案的回答")


def test_对话返回可点引用(client):
    res = client.post("/api/aiqa/chat", json={"question": "马面裙的形制是什么？"})
    assert res.status_code == 200
    body = res.json()
    assert body["sources"], body
    src = body["sources"][0]
    assert src["title"] == "马面裙"
    assert src["type"] == "costume"
    assert src["link"] == f"/archive/{src['id']}"


def test_source_ref仍是去重字符串(client):
    body = client.post("/api/aiqa/chat", json={"question": "马面裙配妆花缎"}).json()
    refs = body["source_ref"].split("；")
    assert len(refs) == len(set(refs))
    assert all(r.startswith("站内档案 · ") for r in refs)
    assert [r.removeprefix("站内档案 · ") for r in refs] == [
        f"{s['title']}（{s['code']}）" for s in body["sources"]]


def test_切片兜底不产出可点引用(client, monkeypatch):
    def fake_search(query, **kwargs):
        return [{"id": "slice-deyi", "text": "先秦深衣制度见《礼记·深衣》。", "score": 1.0}]

    monkeypatch.setattr(graphrag_engine.rag_store, "vector_search", fake_search)
    body = client.post("/api/aiqa/chat", json={"question": "今天天气好吗"}).json()
    assert body["sources"] == []
    assert "内置通史切片" in body["source_ref"]


def test_站内没命中也不报缺字段(client, monkeypatch):
    monkeypatch.setattr(graphrag_engine.rag_store, "vector_search", lambda query, **k: [])
    body = client.post("/api/aiqa/chat", json={"question": "今天天气好吗"}).json()
    assert set(body) >= {"answer", "source_ref", "sources"}
