"""对话召回 · 提示词喂站内真资料（不再只靠 12 条内置切片）"""
from __future__ import annotations

import pytest

from app.db.models import Costumes, Fabrics, PatternLibrary
from app.ai_engine import graphrag_engine


@pytest.fixture()
def captured(monkeypatch):
    """拦住大模型调用，取出实际发给模型的提示词。"""
    box: dict = {}

    def fake_chat(messages, *args, **kwargs):
        box["messages"] = messages
        return "依据所给史料的回答"

    monkeypatch.setattr(graphrag_engine, "chat_completion", fake_chat)
    return box


def _user_prompt(captured) -> str:
    return [m for m in captured["messages"] if m["role"] == "user"][-1]["content"]


def test_对话提示词含站内档案正文(db, captured):
    graphrag_engine.graphrag_chat("马面裙的形制和面料是什么？", db=db)
    prompt = _user_prompt(captured)
    assert "形制：两侧打褶" in prompt
    assert "穿着者：命妇" in prompt
    assert "面料：妆花缎" in prompt


def test_知识图谱关系行进入提示词(db, captured):
    graphrag_engine.graphrag_chat("马面裙用什么面料？", db=db)
    assert "《明史·舆服志》" in _user_prompt(captured)


def test_命中站内资料时不再引用内置切片(db, captured):
    out = graphrag_engine.graphrag_chat("马面裙的形制", db=db)
    assert "马面裙" in out["source_ref"]
    assert "内置通史切片" not in out["source_ref"]


def test_站内无命中才回退内置切片并如实标注(db, captured, monkeypatch):
    def fake_search(query, **kwargs):
        return [{"id": "slice-deyi", "text": "先秦深衣制度见《礼记·深衣》。", "score": 1.0}]

    monkeypatch.setattr(graphrag_engine.rag_store, "vector_search", fake_search)
    out = graphrag_engine.graphrag_chat("今天天气好吗", db=db)
    assert "先秦深衣" in out["context"]
    assert "内置通史切片" in out["source_ref"]


def test_兜底来源按类型标注且不重复堆叠(db, captured, monkeypatch):
    """向量索引命中的是档案切片，不能冒充「内置通史切片」；同类来源只出现一次。"""
    def fake_search(query, **kwargs):
        return [
            {"id": "costume-7-shape", "text": "褙子形制：直领对襟。", "score": 1.0},
            {"id": "costume-7-origin", "text": "褙子溯源：黄昇墓。", "score": 1.0},
            {"id": "slice-deyi", "text": "先秦深衣制度见《礼记·深衣》。", "score": 1.0},
            {"id": "slice-deyi", "text": "先秦深衣制度见《礼记·深衣》。", "score": 1.0},
        ]

    monkeypatch.setattr(graphrag_engine.rag_store, "vector_search", fake_search)
    out = graphrag_engine.graphrag_chat("今天天气好吗", db=db)
    refs = out["source_ref"].split("；")
    assert len(refs) == len(set(refs)), refs
    assert "衣溯AI向量知识库" in refs
    assert "内置通史切片 · deyi" in refs
    assert out["sources"] == []


def test_提示词与回答不出现英文类型词(db, captured):
    """全站中文：喂给模型的行不能带 costume/pattern 这类英文标记，模型会照抄进回答。"""
    graphrag_engine.graphrag_chat("马面裙配团花纹和妆花缎，步摇怎么搭", db=db)
    prompt = _user_prompt(captured)
    for token in ("costume", "pattern", "fabric", "news", "accessory"):
        assert token not in prompt


def test_提示词行带条目编号(db, captured):
    graphrag_engine.graphrag_chat("马面裙的形制和面料是什么？", db=db)
    assert "【站内服饰档案】马面裙（编号 档案-0001）" in _user_prompt(captured)


def test_系统提示词要求标注编号且不得编造(db, captured):
    graphrag_engine.graphrag_chat("马面裙的形制", db=db)
    system = captured["messages"][0]["content"]
    rule = [line for line in system.splitlines() if "〔编号〕" in line]
    assert rule, system
    assert "编造" in rule[0]


def test_展品问答的档案来源也带编号(db, captured):
    costume = db.query(Costumes).filter_by(name="褙子").one()
    out = graphrag_engine.graphrag_answer("它的形制呢", costume=costume, db=db)
    assert out["sources"][0]["code"] == "档案-0003"
    assert out["sources"][0]["external"] is False
    # 编号也得进提示词，否则模型没有可标注的原文，只能编
    assert "档案-0003" in _user_prompt(captured)


def test_多轮历史仍按序带进提示词(db, captured):
    history = [{"role": "user", "content": "明代有什么裙子"}, {"role": "assistant", "content": "马面裙"}]
    graphrag_engine.graphrag_chat("它的形制呢", history=history, db=db)
    roles = [m["role"] for m in captured["messages"]]
    assert roles == ["system", "user", "assistant", "user"]


def test_提示词正文有总量上限(db, captured):
    long_desc = "明" * 280
    db.add_all([Costumes(name=f"妆花马面裙{i}", dynasty="明", category="下裳", description=long_desc)
                for i in range(4)])
    db.add_all([PatternLibrary(name=f"妆花团花{i}", category="植物纹", dynasty="明代", meaning=long_desc)
                for i in range(4)])
    db.add_all([Fabrics(name=f"妆花缎{i}", category="织金", dynasty_peak="明", description=long_desc)
                for i in range(2)])
    db.commit()
    out = graphrag_engine.graphrag_chat("妆花的工艺", db=db)
    assert len(out["context"]) <= 1500


def test_展品问答也用站内检索(db, captured):
    graphrag_engine.graphrag_answer("妆花缎的工艺流程是什么？", db=db)
    prompt = _user_prompt(captured)
    assert "挖花盘织" in prompt
    assert "桑蚕丝" in prompt
