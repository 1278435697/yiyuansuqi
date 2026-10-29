"""检索中枢 · 站内四库与配饰九卷真召回

对话上下文与答后推荐共用这一份结果，保证「模型引用的资料」和「用户能点的卡片」同源。
不走向量召回：生产未启用 ChromaDB 与 embedding 密钥，向量检索恒退化为 12 条内置切片，
命不中档案 id（实测 6 个真实问题 5 个空、1 个串到先秦深衣）。
"""
from __future__ import annotations

import urllib.parse

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai_engine.archive_codes import code_of, parse_codes
from app.ai_engine.query_terms import build_dictionary, dynasty_hit, dynasties_in, extract_terms
from app.services import accessory_docs

LINKS = {
    "costume": "/archive/{id}",
    "pattern": "/pattern/{id}",
    "fabric": "/fabric/{id}",
    "news": "/news/{id}",
    "accessory": "/accessories/index.html#/a/{id}",
}
# 同名条目并存时（配饰九卷的衣制卷里也有「马面裙」「褙子」），站内档案排在配饰前面。
TYPE_ORDER = ["costume", "pattern", "fabric", "news", "accessory"]
TEXT_BUDGET = 300


def _clip(text: str) -> str:
    return text if len(text) <= TEXT_BUDGET else text[:TEXT_BUDGET - 1] + "…"


def _pat_first_image(row) -> str:
    imgs = row.images or []
    if imgs and isinstance(imgs[0], dict):
        return imgs[0].get("url", "") or ""
    return ""


# ===== 资料正文（喂给模型的那段话） =====

def _text_costume(row, db: Session) -> str:
    from app.db.models import CostumeRelations

    parts = [f"{row.name}（{row.dynasty or '朝代待考'}·{row.category or '类别待考'}）"]
    for label, value in (
        ("形制", row.description), ("面料", row.fabric), ("纹样", row.pattern),
        ("色彩", row.color), ("穿着者", row.wearer), ("史料类型", row.source_type),
    ):
        if value:
            parts.append(f"{label}：{value}")
    for rel in db.query(CostumeRelations).filter_by(costume_id=row.id).all():
        src = f"（{rel.source_ref}）" if rel.source_ref else ""
        parts.append(f"{rel.relation_type}：{rel.target_value}{src}")
    return _clip("；".join(parts))


def _text_pattern(row, db: Session) -> str:
    parts = [f"{row.name}（{row.dynasty or '朝代待考'}·{row.category or '类别待考'}）"]
    for label, value in (("寓意", row.meaning), ("结构特征", row.props), ("搭配", row.pairs)):
        if value:
            parts.append(f"{label}：{value}")
    return _clip("；".join(parts))


def _text_fabric(row, db: Session) -> str:
    parts = [f"{row.name}（{row.dynasty_peak or '朝代待考'}·{row.category or '类别待考'}）"]
    for label, value in (("原料", row.raw_material), ("工艺", row.technique),
                         ("简介", row.description), ("出处", row.source_ref)):
        if value:
            parts.append(f"{label}：{value}")
    return _clip("；".join(parts))


def _text_news(row, db: Session) -> str:
    parts = [f"{row.title}"]
    if row.source:
        parts.append(f"来源：{row.source}")
    if row.summary:
        parts.append(f"摘要：{row.summary}")
    return _clip("；".join(parts))


def _as_text(value) -> str:
    """配饰 JSON 里同名字段可能是字符串也可能是列表/字典，非字符串一律不进取正文。"""
    return value.strip() if isinstance(value, str) else ""


def _text_accessory(entry: dict, db: Session) -> str:
    parts = [f"{entry.get('name')}（{_as_text(entry.get('category')) or '类别待考'}"
             f"·{_as_text(entry.get('dynasty')) or '朝代待考'}）"]
    for label, value in (("定义", entry.get("定义") or entry.get("summary")),
                         ("材质", entry.get("material") or entry.get("材质")),
                         ("形制", entry.get("form_summary"))):
        text = _as_text(value)
        if text:
            parts.append(f"{label}：{text}")
    return _clip("；".join(parts))


_TEXT_BUILDERS = {
    "costume": _text_costume,
    "pattern": _text_pattern,
    "fabric": _text_fabric,
    "news": _text_news,
    "accessory": _text_accessory,
}
_SUBTITLE = {
    "costume": lambda r: " · ".join(x for x in (r.dynasty, r.category) if x),
    "pattern": lambda r: " · ".join(x for x in (r.dynasty, r.category) if x),
    "fabric": lambda r: " · ".join(x for x in (r.dynasty_peak, r.category) if x),
    "news": lambda r: r.source or "",
    "accessory": lambda e: " · ".join(x for x in (_as_text(e.get("category")),
                                                  _as_text(e.get("dynasty"))) if x),
}
_IMAGE = {
    "costume": lambda r: r.image_url or "",
    "pattern": _pat_first_image,
    "fabric": lambda r: r.image_url or "",
    "news": lambda r: r.cover_image or "",
    "accessory": lambda e: accessory_docs.abs_paths(_as_text(e.get("photo"))),
}


# ===== 召回 =====

def _exact_hits(db: Session, terms: list[str], dyns: list[str]) -> list[tuple[int, str, int, bool, object]]:
    """逐词在四库做名称包含检索：词频排名 + 名称全等 + 朝代一致决定分值。"""
    from app.db.models import Costumes, Fabrics, News, PatternLibrary

    total = max(len(terms), 1)
    hits: list[tuple[int, str, int, bool, object]] = []
    for rank, term in enumerate(terms):
        weight = (total - rank) * 10

        for c in db.query(Costumes).filter(Costumes.name.contains(term)).limit(20).all():
            score = weight + (8 if c.name == term else 0) + (6 if dynasty_hit(c.dynasty, dyns) else 0)
            hits.append((score, "costume", c.id, True, c))

        for p in db.query(PatternLibrary).filter(PatternLibrary.name.contains(term)).limit(20).all():
            score = weight + (8 if p.name == term else 0) + (6 if dynasty_hit(p.dynasty, dyns) else 0)
            hits.append((score, "pattern", p.id, True, p))

        for f in db.query(Fabrics).filter(Fabrics.name.contains(term)).limit(20).all():
            score = weight + (8 if f.name == term else 0) + (6 if dynasty_hit(f.dynasty_peak, dyns) else 0)
            hits.append((score, "fabric", f.id, True, f))

        for n in db.query(News).filter(or_(News.title.contains(term),
                                           News.entity_tags.contains(term))).limit(20).all():
            hits.append((weight + (6 if dynasty_hit(n.dynasty_tags, dyns) else 0),
                         "news", n.id, True, n))
    return hits


def _accessory_hits(terms: list[str]) -> list[tuple[int, str, str, bool, dict]]:
    """配饰九卷按名称包含检索；数据文件缺失就少一类语料，不能把整个问答带崩。"""
    try:
        entries = accessory_docs.load()
    except (accessory_docs.AccessoryDataMissing, OSError, ValueError):
        return []
    total = max(len(terms), 1)
    hits: list[tuple[int, str, str, bool, dict]] = []
    for rank, term in enumerate(terms):
        weight = (total - rank) * 10
        for e in entries:
            name = _as_text(e.get("name"))
            if term in name:
                hits.append((weight + (8 if name == term else 0), "accessory",
                             e.get("id"), True, e))
    return hits


def _dynasty_clause(column, dyns: list[str]):
    return or_(*[column.contains(ch) for d in dyns for ch in d])


def _dynasty_hits(db: Session, dyns: list[str], limit: int) -> list[tuple[int, str, int, bool, object]]:
    """专名没命中时退到同朝代条目，前端需标注非精确匹配。"""
    from app.db.models import Costumes, Fabrics, News, PatternLibrary

    if not dyns:
        return []
    size = max(limit, 1)
    hits: list[tuple[int, str, int, bool, object]] = []
    for c in db.query(Costumes).filter(Costumes.dynasty.in_(dyns)).limit(size).all():
        hits.append((10, "costume", c.id, False, c))
    for p in db.query(PatternLibrary).filter(_dynasty_clause(PatternLibrary.dynasty, dyns)).limit(size).all():
        hits.append((9, "pattern", p.id, False, p))
    for f in db.query(Fabrics).filter(_dynasty_clause(Fabrics.dynasty_peak, dyns)).limit(size).all():
        hits.append((8, "fabric", f.id, False, f))
    for n in db.query(News).filter(_dynasty_clause(News.dynasty_tags, dyns)).limit(size).all():
        hits.append((7, "news", n.id, False, n))
    return hits


def _pick(hits, per_type: int, limit: int):
    """同一条目取最高分，按分值降序剪取；正文留给剪取后的条目补，避免为淘汰行查关系表。"""
    best: dict[tuple[str, int], tuple[int, bool, object]] = {}
    for score, card_type, row_id, exact, row in hits:
        key = (card_type, row_id)
        if best.get(key, (0,))[0] < score:
            best[key] = (score, exact, row)
    ordered = sorted(best.items(),
                     key=lambda kv: (-kv[1][0], TYPE_ORDER.index(kv[0][0]), kv[0][1]))

    out, used = [], {}
    for (card_type, row_id), (score, exact, row) in ordered:
        if used.get(card_type, 0) >= per_type:
            continue
        used[card_type] = used.get(card_type, 0) + 1
        out.append((card_type, row_id, score, exact, row))
        if len(out) >= limit:
            break
    return out


def _title(card_type: str, row) -> str:
    if card_type == "accessory":
        return _as_text(row.get("name"))
    return getattr(row, "name", None) or row.title


def _link(card_type: str, row_id) -> str:
    """配饰条目 id 是中文，跳转地址要按配饰子站的写法编码。"""
    if card_type == "accessory":
        return LINKS[card_type].format(id=urllib.parse.quote(str(row_id), safe=""))
    return LINKS[card_type].format(id=row_id)


def _build_item(card_type: str, row_id, score: int, exact: bool, row, db: Session) -> dict:
    code = str(row_id) if card_type == "accessory" else code_of(card_type, row_id, getattr(row, "code", None))
    return {
        "type": card_type,
        "id": row_id,
        "code": code,
        "title": _title(card_type, row),
        "subtitle": _SUBTITLE[card_type](row),
        "image_url": _IMAGE[card_type](row),
        "link": _link(card_type, row_id),
        "external": card_type == "accessory",
        "text": _TEXT_BUILDERS[card_type](row, db),
        "score": score,
        "exact": exact,
    }


def retrieve_items(terms: list[str], dynasties: list[str], db: Session,
                   per_type: int = 3, limit: int = 8) -> list[dict]:
    """抽词结果 → 站内条目（含编号、正文与详情链接）。"""
    hits = _exact_hits(db, terms, dynasties) + _accessory_hits(terms)
    if not hits:
        hits = _dynasty_hits(db, dynasties, limit)
    return [_build_item(card_type, row_id, score, exact, row, db)
            for card_type, row_id, score, exact, row in _pick(hits, per_type, limit)]


def _coded_items(codes: list[tuple[str, object]], db: Session, limit: int) -> list[dict]:
    """按编号直接定位条目：编号是用户从引用里点出来的，比抽词猜更准。"""
    from app.db.models import Costumes, Fabrics, News, PatternLibrary

    models = {"costume": Costumes, "pattern": PatternLibrary, "fabric": Fabrics, "news": News}
    items: list[dict] = []
    for card_type, key in codes[:limit]:
        if card_type == "accessory":
            try:
                row = accessory_docs.find(str(key))
            except (accessory_docs.AccessoryDataMissing, OSError, ValueError):
                row = None
        else:
            model = models[card_type]
            row = db.query(model).filter(model.id == key).first()
        if row is not None:
            items.append(_build_item(card_type, key if card_type == "accessory" else row.id,
                                     100, True, row, db))
    return items


def retrieve(question: str, db: Session, per_type: int = 3, limit: int = 8) -> list[dict]:
    """问句 → 站内真资料条目；先认编号，认不到再抽词，无朝代无专名时返回空列表。"""
    question = (question or "").strip()
    if not question:
        return []
    codes = parse_codes(question)
    if codes:
        items = _coded_items(codes, db, limit)
        if items:
            return items
    terms = extract_terms(question, build_dictionary(db))
    dyns = dynasties_in(question)
    return retrieve_items(terms, dyns, db, per_type=per_type, limit=limit)


PROMPT_BUDGET = 1500
_TYPE_CN = {"costume": "服饰档案", "pattern": "纹样", "fabric": "面料", "news": "资讯", "accessory": "配饰"}


def prompt_lines(items: list[dict], budget: int = PROMPT_BUDGET) -> list[str]:
    """条目正文拼成提示词行：按分值顺序装入，超出总预算即停（单条已在 300 字内截好）。

    类型标记必须写中文——模型会把提示词里的英文标记原样抄进回答。
    编号也要进这一行，模型才可能在句末标出〔档案-0007〕这种可点出处。
    """
    lines: list[str] = []
    used = 0
    for item in items:
        line = (f"【站内{_TYPE_CN[item['type']]}】{item['title']}"
                f"（编号 {item['code']}）：{item['text']}")
        if used + len(line) > budget:
            break
        lines.append(line)
        used += len(line) + 1
    return lines


def archive_refs(items: list[dict]) -> list[str]:
    """站内召回的来源标注，去重且保持排序。

    必须带编号：配饰九卷的衣制卷与服饰档案里有同名条目（都叫「马面裙」），
    只写标题会撞成一条，用户看不出引用的是哪一份。
    """
    out: list[str] = []
    for item in items:
        ref = f"站内档案 · {item['title']}（{item['code']}）"
        if ref not in out:
            out.append(ref)
    return out


def sources_of(items: list[dict]) -> list[dict]:
    """给前端的可点引用：与 archive_refs 同源同序，只是带上编号与跳转地址。

    external 为真的地址不在单页路由表里（配饰九卷是独立静态子页），前端要用普通链接渲染。
    """
    return [{"type": i["type"], "id": i["id"], "code": i["code"], "title": i["title"],
             "link": i["link"], "external": i["external"]} for i in items]
