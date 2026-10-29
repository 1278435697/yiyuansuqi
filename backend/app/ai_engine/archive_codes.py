"""知识库条目编号 · 由自增 id 派生，不落数据库

数据库不加列：id 不回收，只要行不删，编号就固定，可以长期引用与回查。

前缀必须是中文，且不能撞配饰九卷的卷名（服饰/衣制/头饰…）——配饰条目 id 本身就是
「头饰-01」这种形式，撞了就没法区分「服饰-01」是第一条配饰还是服饰档案。
"""
from __future__ import annotations

import re

from app.services.accessory_docs import CATEGORY_ORDER

PREFIX = {"costume": "档案", "pattern": "纹样", "fabric": "面料", "news": "资讯"}
_TYPE_BY_PREFIX = {v: k for k, v in PREFIX.items()}

_CODE_RE = re.compile(
    r"(" + "|".join([*PREFIX.values(), *CATEGORY_ORDER]) + r")-(\d{1,6})"
)


def code_of(item_type: str, row_id: int, row_code: int | None = None) -> str:
    """条目 → 编号。纹样优先用已有的「名录编号」，保持站内两套观感一致。"""
    if item_type not in PREFIX:
        raise ValueError(f"未登记编号前缀的条目类型：{item_type}")
    if item_type == "pattern" and row_code:
        return f"{PREFIX['pattern']}-{int(row_code):04d}"
    return f"{PREFIX[item_type]}-{int(row_id):04d}"


def parse_codes(text: str) -> list[tuple[str, object]]:
    """问句 → 其中出现的编号，按出现顺序去重。

    配饰编号原样保留（位数有含义，用于回查 accessories.json 里的 id）；
    四库编号转成条目 id 整数。
    """
    out: list[tuple[str, object]] = []
    for prefix, digits in _CODE_RE.findall(text or ""):
        if prefix in _TYPE_BY_PREFIX:
            key: object = int(digits)
            item_type = _TYPE_BY_PREFIX[prefix]
        else:
            key, item_type = f"{prefix}-{digits}", "accessory"
        if (item_type, key) not in out:
            out.append((item_type, key))
    return out
