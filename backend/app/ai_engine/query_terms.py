"""推荐检索 · 查询抽词（朝代词典 + 服饰专名 + 站内库现名）

不走向量召回：生产环境 ChromaDB 与 embedding 密钥均未启用，vector_search 恒退化为
12 条内置切片，命不中档案 id。这里用词典最长匹配，专名词典由调用方从四库实时取回。
"""
from __future__ import annotations

from typing import Iterable

from app.ai_engine.ner_news_parse import COSTUME_DICT, DYNASTY_MAP

def _scan(text: str, terms: Iterable[str]) -> list[tuple[int, str]]:
    """按位置返回命中，最长匹配优先；被长词覆盖的位置不再计入短词。

    单字朝代词紧跟「服/装」时是服装名的一部分（汉服、唐装），不算朝代指称。
    """
    term_set = {t for t in terms if t}
    covered = [False] * len(text)
    hits: list[tuple[int, str]] = []
    for term in sorted(term_set, key=len, reverse=True):
        pos = 0
        while True:
            i = text.find(term, pos)
            if i < 0:
                break
            if not any(covered[i:i + len(term)]):
                is_garment_word = len(term) == 1 and text[i + 1:i + 2] in ("服", "装")
                if not is_garment_word:
                    hits.append((i, term))
                    for k in range(i, i + len(term)):
                        covered[k] = True
            pos = i + len(term)
    return hits


def extract_terms(question: str, extra_terms: Iterable[str] = ()) -> list[str]:
    """问句里的服饰/纹样/面料/资讯专名，按出现次数排序，同频按首次出现先后。"""
    if not question:
        return []
    counts: dict[str, int] = {}
    first: dict[str, int] = {}
    for pos, term in _scan(question, list(COSTUME_DICT) + list(extra_terms)):
        if len(term) < 2:
            continue
        counts[term] = counts.get(term, 0) + 1
        first.setdefault(term, pos)
    return sorted(counts, key=lambda t: (-counts[t], first[t], t))


def dynasties_in(question: str) -> list[str]:
    """问句里的朝代词，归一到 DYNASTY_MAP 的规范值，按出现顺序去重。"""
    if not question:
        return []
    out: list[str] = []
    for _, term in sorted(_scan(question, DYNASTY_MAP)):
        value = DYNASTY_MAP[term]
        if value not in out:
            out.append(value)
    return out


def build_dictionary(db) -> list[str]:
    """站内专名词典：服饰档案名 + 纹样名 + 面料名 + 资讯实体标签 + 配饰九卷名（每次请求现取）。

    资讯标签里常有前三张表没有的专名（出土地、馆藏、工艺名），只靠表名会漏召回；
    簪、笄、步摇这类只存在于配饰九卷的数据文件里。
    """
    import re

    from app.db.models import Costumes, Fabrics, News, PatternLibrary
    from app.services import accessory_docs

    names: list[str] = []
    for model in (Costumes, PatternLibrary, Fabrics):
        names += [r[0] for r in db.query(model.name).all()]
    for (tags,) in db.query(News.entity_tags).all():
        names += [t.strip() for t in re.split(r"[，,、;；/]+", tags or "") if t.strip()]
    try:
        names += [e.get("name") for e in accessory_docs.load()]
    except (accessory_docs.AccessoryDataMissing, OSError, ValueError):
        pass
    return [n for n in names if n]


def dynasty_hit(field: str, dynasties: Iterable[str]) -> bool:
    """库里朝代字段与问句朝代是否对得上。

    档案表存规范值（明/隋唐），面料与纹样表存区间串（元—明、唐(吐蕃)—明清），
    所以整体匹配不上时再按单字判一次。
    """
    text = field or ""
    if not text:
        return False
    return any(d in text or any(ch in text for ch in d) for d in dynasties)
