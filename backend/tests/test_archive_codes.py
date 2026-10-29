"""知识库条目编号 · 派生与解析（不依赖数据库与外部服务）

编号只在代码层由自增 id 派生，不落数据库：id 不回收，所以行不删编号就固定。
"""
from __future__ import annotations

import pytest

from app.ai_engine.archive_codes import code_of, parse_codes


def test_服饰档案编号用档案前缀补零四位():
    assert code_of("costume", 7) == "档案-0007"


def test_四类编号前缀清晰():
    assert code_of("pattern", 12) == "纹样-0012"
    assert code_of("fabric", 3) == "面料-0003"
    assert code_of("news", 11) == "资讯-0011"


def test_编号前缀不撞配饰九卷的卷名():
    """配饰条目 id 形如「服饰-01」，档案前缀若也用「服饰」就会撞车。"""
    from app.services.accessory_docs import CATEGORY_ORDER

    for type_, in (("costume",), ("pattern",), ("fabric",), ("news",)):
        prefix = code_of(type_, 1).split("-")[0]
        assert prefix not in CATEGORY_ORDER, f"{type_} 的编号前缀 {prefix} 与配饰卷名撞车"


def test_纹样沿用已有名录编号():
    assert code_of("pattern", 12, row_code=88) == "纹样-0088"


def test_纹样没有名录编号才退回条目id():
    assert code_of("pattern", 12, row_code=None) == "纹样-0012"
    assert code_of("pattern", 12, row_code=0) == "纹样-0012"


def test_条目多于四位仍然连续不截断():
    assert code_of("costume", 123456) == "档案-123456"


def test_从问句里解析出编号():
    assert parse_codes("档案-0007 讲了什么？") == [("costume", 7)]


def test_解析多个编号并按出现顺序去重():
    assert parse_codes("档案-0007 和 面料-0003，再看回 档案-0007") == [
        ("costume", 7),
        ("fabric", 3),
    ]


def test_不认英文前缀与残缺编号():
    assert parse_codes("costume-7 档案- 档案-abc 档案-") == []


def test_配饰卷名编号也算编号但不是档案编号():
    assert parse_codes("头饰-01 是什么") == [("accessory", "头饰-01")]


def test_空输入不抛():
    assert parse_codes("") == []
    assert parse_codes(None) == []


def test_未知类型不静默兜底():
    with pytest.raises(ValueError):
        code_of("relic", 1)
