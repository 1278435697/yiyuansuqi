"""《衣冠档案》96 件文物实例（图册数据）—— 站内第五路召回。

粒度是「文物实例」：带出土地、馆藏、文物编号与七字段考证，
与 costumes 表里的 46 条「款式类型」互补，所以单独一路，不并入档案表。
纯读 JSON、按词打分，不依赖数据库，避免改 schema。
"""
from __future__ import annotations

import json
from pathlib import Path

__all__ = ["INSTANCES", "search", "merge"]

_FIELDS = ("form", "wearer", "source", "fabric", "pattern", "color", "group")

_DATA_FILE = Path(__file__).with_name("archive_instances.json")

INSTANCES: list[dict] = []
if _DATA_FILE.exists():
    try:
        INSTANCES = json.loads(_DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        INSTANCES = []


def _summary(it: dict) -> str:
    f = it.get("fields") or {}
    head = "、".join(x for x in (it.get("name"), it.get("dyn"), it.get("period"),
                                it.get("place"), it.get("museum")) if x)
    body = [v.strip()[:120] for v in (f.get("form"), f.get("fabric"), f.get("pattern"),
                                     f.get("source")) if isinstance(v, str) and v.strip()]
    s = head + "。" + "；".join(body)
    note = (it.get("note") or "").strip()
    if note:
        s += "。" + note[:110]
    return s[:300]


def _blob(it: dict) -> str:
    f = it.get("fields") or {}
    parts = [it.get("name"), it.get("alias"), it.get("dyn"), it.get("era"), it.get("period"),
             it.get("place"), it.get("museum"), it.get("srcType"), it.get("idNo"), it.get("note")]
    parts += list(it.get("craft") or [])
    parts += [f.get(k) for k in _FIELDS]
    return " ".join(x for x in parts if isinstance(x, str) and x)


for _it in INSTANCES:
    _it["_blob"] = _blob(_it)
    _it["_summary"] = _summary(_it)


def search(terms: list[str], limit: int = 2) -> list[tuple[int, dict]]:
    """按词打分：名字整词命中权重最高，别名次之，其余字段兜底。"""
    clean = [t.strip() for t in (terms or []) if isinstance(t, str) and len(t.strip()) >= 2]
    if not clean:
        return []
    scored: list[tuple[int, dict]] = []
    for it in INSTANCES:
        name = it.get("name") or ""
        alias = it.get("alias") or ""
        score = 0
        for t in clean:
            if t in name:
                score += 30
            elif t in alias:
                score += 12
            elif t in it.get("_blob", ""):
                score += 5
        if score:
            scored.append((score, it))
    scored.sort(key=lambda kv: (-kv[0], kv[1].get("no") or 0))
    return scored[:limit]


def _item(score: int, it: dict) -> dict:
    return {
        "type": "instance",
        "id": it.get("no"),
        "code": "实例-%03d" % (it.get("no") or 0),
        "title": it.get("name") or "",
        "subtitle": " · ".join(x for x in (it.get("dyn"), it.get("museum")) if x),
        "image_url": it.get("img") or "",
        "link": "/archive-book/index.html#no=%s" % (it.get("no") or 0),
        "external": True,
        "text": it.get("_summary") or "",
        "score": score,
        "exact": False,
    }


def match_question(question: str, limit: int = 2) -> list[tuple[int, dict]]:
    """问句里直接出现展品名（或名字里 3 字以上的片段）即命中。

    专名不在站内词典时（如「素罗背子」「素纱襌衣」），extract_terms 会抽空，
    这时只能靠问句与展品名的直接对撞来召回。
    """
    q = (question or "").strip()
    if len(q) < 2:
        return []
    scored: list[tuple[int, dict]] = []
    for it in INSTANCES:
        name = it.get("name") or ""
        best = 0
        for size in range(len(name), 2, -1):
            for start in range(0, len(name) - size + 1):
                if name[start:start + size] in q:
                    best = max(best, size * 8)
            if best:
                break
        if best:
            scored.append((best, it))
    scored.sort(key=lambda kv: (-kv[0], kv[1].get("no") or 0))
    return scored[:limit]


def merge(items: list[dict], terms: list[str], limit: int = 8, max_inst: int = 2,
          question: str = "") -> list[dict]:
    """把命中的文物实例插到召回列表最前：考古实物证据比款式概述更硬。"""
    hits = list(search(terms, limit=max_inst))
    if question:
        seen = {it.get("no") for _, it in hits}
        for score, it in match_question(question, limit=max_inst):
            if it.get("no") not in seen:
                hits.append((score, it))
        hits.sort(key=lambda kv: -kv[0])
        hits = hits[:max_inst]
    if not hits:
        return items
    return ([_item(score, it) for score, it in hits] + list(items))[: max(limit, len(items))]
