"""服饰史料向量知识库（ChromaDB 持久化）—— GraphRAG 向量召回层

切片维度：形制/面料/纹样/出土溯源/礼制/时代背景，覆盖全部服饰档案与知识图谱关系。
embedding 复用 llm_client.embed_text（配置 API Key 时用向量接口，否则本地哈希向量）。
"""
from __future__ import annotations

import os
import threading
from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine.llm_client import embed_text
from app.db.models import Costumes, CostumeRelations

_CHROMA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "data", "chroma")
_COLLECTION = "costume_knowledge"

# 内置权威史料切片（离线兜底；向量库构建时亦并入）
_BASE_SLICES: list[dict[str, str]] = [
    {"id": "slice-deyi", "text": "先秦深衣制度见《礼记·深衣》：短毋见肤，长毋被土，曲裾或直裾，交领右衽，以玄色为上、纁色为缘。"},
    {"id": "slice-qinhan-susha", "text": "马王堆一号汉墓出土素纱单衣，重约49克，为西汉轻纱工艺巅峰，象征汉代缫丝织造水平。"},
    {"id": "slice-qinhan-quju", "text": "汉代曲裾深衣绕襟而下，下裳缠绕数周，为贵族礼服，等级标识鲜明，见《后汉书·舆服志》。"},
    {"id": "slice-suitang-daxiushan", "text": "唐代大袖衫宽袖飘逸，见于《簪花仕女图》与敦煌壁画供养人像，为贵妇常服。"},
    {"id": "slice-suitang-yuanling", "text": "唐代圆领袍源自胡服改制，为百官常服，见《旧唐书·舆服志》。"},
    {"id": "slice-song-beizi", "text": "宋代褙子直领对襟、两侧开衩，福州南宋黄昇墓出土实物，以罗纱绢锦为料。"},
    {"id": "slice-ming-manianqun", "text": "明代马面裙两侧打褶、前后裙门平整，出土于定陵，妆花缎织金为贵。"},
    {"id": "slice-yuan-zhisun", "text": "元代质孙服为蒙古宫廷礼服，织金纳石失面料，见《元史·舆服志》。"},
    {"id": "slice-qing-qizhuang", "text": "清代旗装立领盘扣、直身长袍，配马褂，见《皇朝礼器图式》与清代宫廷档案。"},
    {"id": "slice-weijin-kuanshan", "text": "魏晋宽衫大袖、褒衣博带，名士风流见于《世说新语》与《洛神赋图》。"},
    {"id": "slice-shanggu", "text": "上古先民衣皮羽葛，《礼记·礼运》：未有火化，食草木之实，衣其羽皮。"},
    {"id": "slice-ming-aoqun", "text": "明代袄裙为竖领长袄配马面裙，正色五色，妆花缎织金，端正规整。"},
]

_client: Any | None = None
_built: set[str] = set()
_lock = threading.Lock()


def _get_client():
    """惰性创建持久化 ChromaDB 客户端；失败时返回 None（回退内置切片）。"""
    global _client
    if _client is not None:
        return _client
    try:
        import chromadb
        from chromadb.config import Settings
        _client = chromadb.PersistentClient(path=_CHROMA_DIR, settings=Settings(anonymized_telemetry=False))
    except Exception:
        _client = False  # 标记不可用
    return _client


def _slice_from_costume(c: Costumes) -> list[dict[str, str]]:
    return [
        {"id": f"costume-{c.id}-shape", "text": f"{c.name}（{c.dynasty}·{c.category}）形制：{c.description or '见档案'}，穿着者{ c.wearer or '不详'}，形制来源为{c.source_type or '文献'}记载。"},
        {"id": f"costume-{c.id}-fabric", "text": f"{c.name}面料：{c.fabric}，纹样：{c.pattern}，服色：{c.color}。"},
        {"id": f"costume-{c.id}-origin", "text": f"{c.name}出土溯源：{c.source_type}；朝代：{c.dynasty}。"},
    ]


def ensure_index(db: Session | None = None) -> dict[str, int]:
    """构建/增量写入向量索引（幂等：按文档 id 去重）。"""
    client = _get_client()
    if client is False:
        return {"mode": "fallback", "docs": len(_BASE_SLICES)}
    try:
        col = client.get_or_create_collection(
            _COLLECTION,
            metadata={"hnsw:space": "cosine", "description": "衣溯AI 服饰史料知识库"},
        )
    except Exception:
        return {"mode": "fallback", "docs": len(_BASE_SLICES)}

    docs: list[dict[str, str]] = []
    if db is not None:
        try:
            for c in db.query(Costumes).all():
                docs.extend(_slice_from_costume(c))
                for rel in db.query(CostumeRelations).filter_by(costume_id=c.id).all():
                    docs.append({
                        "id": f"rel-{rel.id}",
                        "text": f"{c.name}与{rel.target_value}存在{rel.relation_type}关系。{rel.source_ref or ''}",
                    })
        except Exception:
            docs = []
    docs.extend(_BASE_SLICES)

    new_docs = [d for d in docs if d["id"] not in _built]
    if not new_docs:
        return {"mode": "chromadb", "docs": len(_built)}
    try:
        with _lock:
            for d in new_docs:
                try:
                    col.add(ids=[d["id"]], documents=[d["text"]],
                            embeddings=[embed_text(d["text"])])
                    _built.add(d["id"])
                except Exception:
                    # 单条失败不中断（如重复 id）
                    _built.add(d["id"])
        return {"mode": "chromadb", "docs": len(_built)}
    except Exception:
        return {"mode": "fallback", "docs": len(_BASE_SLICES)}


def vector_search(query: str, k: int = 4) -> list[dict[str, str]]:
    """向量召回：返回 [{id, text, distance}]，失败时回退关键词匹配内置切片。"""
    client = _get_client()
    if client is False:
        return _keyword_fallback(query)
    try:
        col = client.get_collection(_COLLECTION)
        res = col.query(query_embeddings=[embed_text(query)], n_results=k)
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        return [{"id": i, "text": t, "distance": float(d)} for i, t, d in zip(ids, docs, dists) if t]
    except Exception:
        return _keyword_fallback(query)


def _keyword_fallback(query: str) -> list[dict[str, str]]:
    hits = []
    for s in _BASE_SLICES:
        kw = s["text"].split("：")[0][:4]
        if kw and kw in query:
            hits.append({"id": s["id"], "text": s["text"], "distance": 0.0})
    if not hits:
        for s in _BASE_SLICES:
            if any(ch in query for ch in ["先秦", "秦汉", "魏晋", "隋唐", "宋", "元", "明", "清", "上古"]):
                hits.append({"id": s["id"], "text": s["text"], "distance": 0.0})
                break
    return hits or [{"id": "none", "text": "（暂无匹配史料切片）", "distance": 1.0}]
