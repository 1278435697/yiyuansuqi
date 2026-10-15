"""服饰专属 GraphRAG 溯源引擎

知识图谱（MySQL 中的 costume_relations）+ 向量检索（ChromaDB 持久化向量库）
多路召回 → 重排 → 构造专用提示词 → 大模型生成可溯源回答。

- 向量层：app.ai_engine.rag_store（ChromaDB；未配置/失败时回退内置史料切片）
- 实体层：档案字段 + costume_relations 知识图谱关系
"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine.llm_client import chat_completion
from app.ai_engine import rag_store
from app.db.models import Costumes, CostumeRelations

# 内置史料切片（演示 fallback，正式版从 ChromaDB 召回）
_KNOWLEDGE_SLICE = {
    "马面裙": "明代马面裙为两侧打褶、前后裙门平整的裙式，出土于定陵，以妆花缎织金为贵。",
    "褙子": "宋代褙子为直领对襟长衣，两侧开衩，福州南宋黄昇墓有出土实物。",
    "大袖衫": "唐代大袖衫宽袖飘逸，见于《簪花仕女图》与敦煌壁画供养人像。",
    "深衣": "先秦深衣制度见《礼记·深衣》：短毋见肤，长毋被土，曲裾或直裾。",
    "曲裾": "汉代曲裾深衣缠绕下裳，马王堆出土素纱单衣为其代表。",
    "圆领袍": "唐代圆领袍源于胡服改制，为百官常服，见《旧唐书·舆服志》。",
}


def _build_system_prompt() -> str:
    return (
        "你是华夏历代服饰史专业考据助手，请像一位服饰史学者一样与用户自然对话。回答规则：\n"
        "1. 优先严格依据提供的史料切片作答，并在回答中或末尾附史料来源；\n"
        "2. 若检索史料未覆盖该问题，允许依据服饰史领域公认常识作答，"
        "但回答开头必须注明『（未检索到权威史料切片，以下为模型常识性回答，仅供参考）』；\n"
        "3. 严禁编造形制、朝代混搭或混淆考古复原与影楼臆造；\n"
        "4. 回答条理清晰、语言自然，直接解答用户问题。"
    )


def graphrag_answer(
    question: str,
    costume: Costumes | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """多路召回 + LLM 生成，返回 answer + source_ref。"""
    # 1. 实体级召回（知识图谱/档案字段）
    graph_hits: list[str] = []
    source_refs: list[str] = []
    if costume is not None:
        graph_hits.append(
            f"{costume.name}（{costume.dynasty}）——形制：{costume.description or '见档案'}；"
            f"面料：{costume.fabric}；纹样：{costume.pattern}"
        )
        source_refs.append(f"衣溯AI档案库 · {costume.dynasty} {costume.name}")
        if db is not None:
            for rel in db.query(CostumeRelations).filter_by(costume_id=costume.id).all():
                graph_hits.append(f"{rel.relation_type}：{rel.target_value}")
                if rel.source_ref:
                    source_refs.append(rel.source_ref)

    # 2. 向量召回（ChromaDB 持久化向量库；失败回退内置切片）
    vec_hits: list[str] = []
    for hit in rag_store.vector_search(question, k=4):
        if hit["id"] == "none":
            continue
        vec_hits.append(hit["text"])
        if hit["id"].startswith("slice-"):
            source_refs.append(f"史料切片 · {hit['id'].removeprefix('slice-')}")
        elif hit["id"].startswith("rel-"):
            source_refs.append("知识图谱关系")
        else:
            source_refs.append("衣溯AI向量知识库")

    # 3. 构造提示词
    context = "\n".join(graph_hits + vec_hits) or "（未检索到与问题直接相关的史料切片）"
    messages = [
        {"role": "system", "content": _build_system_prompt()},
        {
            "role": "user",
            "content": (
                f"问题：{question}\n\n可参考史料：\n{context}\n\n"
                "请依据上述史料作答，并附史料来源。"
            ),
        },
    ]
    answer = chat_completion(messages)
    if not answer:
        # 未配置大模型：回退「知识库直答」——依据召回切片给出可溯源回答，不编造
        base_hits = [h for h in vec_hits if "（" not in h] or vec_hits
        if base_hits:
            answer = (
                "（当前为离线知识库模式，未调用大模型）依据衣溯AI史料知识库检索结果：\n"
                + "\n".join(f"· {t}" for t in base_hits[:3])
            )
        else:
            answer = "（当前为离线知识库模式）未检索到与该问题直接相关的权威史料记载。"
    return {
        "answer": answer,
        "source_ref": "；".join(source_refs) or "内置史料切片（演示）",
        "context": context,
    }


def rag_fetch_context(keywords: list[str]) -> list[str]:
    """供问答/社区模块复用的检索入口（向量召回 + 关键词兜底）。"""
    hits = []
    for kw in keywords:
        if not kw:
            continue
        for hit in rag_store.vector_search(kw, k=2):
            if hit["id"] != "none" and hit["text"] not in hits:
                hits.append(hit["text"])
    return hits or ["（暂无匹配史料）"]


def graphrag_chat(
    question: str,
    history: list[dict] | None = None,
    db: Session | None = None,
) -> dict[str, Any]:
    """多轮溯源对话：RAG 召回 + 豆包生成（支持连续追问）。

    与 graphrag_answer 相比：
    - 允许带历史消息（多轮上下文）；
    - 知识库无切片时由大模型依据常识作答并显式标注，保证“能对话”。
    """
    # 1. 向量召回（ChromaDB 持久化向量库；失败回退内置切片）
    vec_hits: list[str] = []
    source_refs: list[str] = []
    for hit in rag_store.vector_search(question, k=4):
        if hit["id"] == "none":
            continue
        vec_hits.append(hit["text"])
        if hit["id"].startswith("slice-"):
            source_refs.append(f"史料切片 · {hit['id'].removeprefix('slice-')}")
        elif hit["id"].startswith("rel-"):
            source_refs.append("知识图谱关系")
        else:
            source_refs.append("衣溯AI向量知识库")

    # 2. 构造多轮提示词（历史 + 当前问题 + 召回上下文）
    context = "\n".join(vec_hits) or "（未检索到与问题直接相关的史料切片）"
    messages: list[dict] = [{"role": "system", "content": _build_system_prompt()}]
    for h in (history or [])[-8:]:
        role = h.get("role")
        content = h.get("content")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": str(content)[:1200]})
    messages.append({
        "role": "user",
        "content": (
            f"问题：{question}\n\n可参考史料：\n{context}\n\n"
            "请回答上述问题。若可参考史料覆盖请优先依据史料并标注来源；"
            "若史料未覆盖，请基于服饰史常识作答并按要求注明。"
        ),
    })

    # 3. 调用豆包生成
    answer = chat_completion(messages)
    if not answer:
        # 未配置大模型：回退「知识库直答」
        base_hits = [h for h in vec_hits if "（" not in h] or vec_hits
        if base_hits:
            answer = (
                "（当前为离线知识库模式，未调用大模型）依据衣溯AI史料知识库检索结果：\n"
                + "\n".join(f"· {t}" for t in base_hits[:3])
            )
        else:
            answer = "（当前为离线知识库模式）未检索到与该问题直接相关的权威史料记载。"
    return {
        "answer": answer,
        "source_ref": "；".join(source_refs) or "内置史料切片（演示）",
        "context": context,
    }


def ensure_index(db: Session | None = None) -> dict[str, int]:
    """构建服饰史料向量索引（应用启动/首次问答时调用）。"""
    return rag_store.ensure_index(db)
