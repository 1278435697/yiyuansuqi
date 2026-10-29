"""溯源问答推荐检索 · 抽词逻辑单测（词典来自内存库夹具，不发外部请求）"""
from __future__ import annotations

import pytest

from app.ai_engine.query_terms import build_dictionary, dynasties_in, extract_terms


def test_资讯实体标签也进词典(db):
    """只在 news.entity_tags 里出现的专名（如出土地）也应被抽出来。"""
    assert "定陵" in extract_terms("定陵那次发掘怎么说", build_dictionary(db))


def test_配饰九卷名称也进词典(db):
    """簪、笄、步摇这类只在配饰九卷里的专名，四库表名里没有。"""
    dictionary = build_dictionary(db)
    assert "步摇" in dictionary
    assert "笄" in dictionary


def test_朝代词归一化():
    assert dynasties_in("唐代贵妇参加宴会穿什么？") == ["隋唐"]


def test_朝代词取最长匹配不重复():
    assert dynasties_in("明代马面裙在清朝还在穿吗") == ["明", "清"]


def test_汉服不是朝代指称():
    assert dynasties_in("汉服和影楼装的区别") == []
    assert dynasties_in("唐装的来历") == []
    assert dynasties_in("唐代的衣服") == ["隋唐"]


def test_命中服饰专名():
    terms = extract_terms("马面裙和百褶裙有什么区别？", extra_terms=["百褶裙"])
    assert "马面裙" in terms
    assert "百褶裙" in terms


def test_最长匹配吞掉短词():
    terms = extract_terms("明代马面裙的裙门是平整的吗", extra_terms=["马面裙"])
    assert terms == ["马面裙"]


def test_按词频排序():
    terms = extract_terms("褙子和褙子与深衣", extra_terms=["褙子", "深衣"])
    assert terms[0] == "褙子"


def test_去重():
    terms = extract_terms("马面裙马面裙马面裙", extra_terms=["马面裙"])
    assert terms == ["马面裙"]


def test_无命中返回空():
    assert extract_terms("今天天气怎么样") == []
    assert dynasties_in("今天天气怎么样") == []


def test_空输入不抛():
    assert extract_terms("") == []
    assert dynasties_in(None) == []
