"""文博资讯 NER 解析流水线（创新点五）

流程：RSS 抓取 / 录入 → AI 摘要 → 实体识别（spaCy 中文模型 + 服饰/朝代词典双引擎）→
朝代与服饰标签关联 → RAG 背景补充 → 推荐提问生成 → 发布。
低置信度实体标记待人工审核。
"""
from __future__ import annotations

import re
from typing import Any

from app.ai_engine.llm_client import chat_completion

# 朝代词典（权威映射；spaCy 无朝代实体，用词典保证准确）
DYNASTY_MAP = {
    "上古": "上古", "先秦": "先秦", "秦汉": "秦汉", "汉": "秦汉", "秦": "秦汉",
    "魏晋": "魏晋", "南北朝": "魏晋", "隋": "隋唐", "唐": "隋唐", "大唐": "隋唐",
    "宋": "宋", "北宋": "宋", "南宋": "宋", "元": "元", "明": "明", "明代": "明",
    "清": "清", "清代": "清", "大清": "清",
}

# 服饰实体词典（权威考据词；spaCy 通用模型不覆盖服饰专名）
COSTUME_DICT = ["马面裙", "褙子", "深衣", "曲裾", "直裾", "大袖衫", "襦裙", "圆领袍",
                "长袍", "旗装", "马褂", "披帛", "霞帔", "云肩", "裙", "袍", "衫"]

_nlp = None
_nlp_checked = False


def _get_nlp():
    """惰性加载 spaCy 中文模型；不可用时返回 None（回退纯词典）。"""
    global _nlp, _nlp_checked
    if _nlp_checked:
        return _nlp
    _nlp_checked = True
    try:
        import spacy
        _nlp = spacy.load("zh_core_web_md")
    except Exception:
        _nlp = None
    return _nlp


def extract_entities(text: str) -> list[dict[str, Any]]:
    """spaCy 命名实体 + 服饰/朝代词典双引擎识别，附置信度。"""
    entities: list[dict[str, Any]] = []

    # 引擎一：spaCy 中文模型（人名/机构/地点/文物专名等一般实体）
    nlp = _get_nlp()
    if nlp is not None:
        try:
            doc = nlp(text[:2000])
            seen_ner = set()
            for ent in doc.ents:
                if ent.label_ in ("PERSON", "ORG", "LOC", "MISC") and len(ent.text) <= 12:
                    key = f"ner-{ent.label_}-{ent.text}"
                    if key in seen_ner:
                        continue
                    seen_ner.add(key)
                    entities.append({"type": "named_entity", "value": ent.text, "raw": ent.text,
                                     "confidence": 0.85, "label": ent.label_})
        except Exception:
            pass  # 模型推断失败 → 词典兜底

    # 引擎二：朝代词典（权威映射）
    for kw, dyn in DYNASTY_MAP.items():
        if kw in text:
            entities.append({"type": "dynasty", "value": dyn, "raw": kw,
                             "confidence": 0.95 if len(kw) > 1 else 0.8})
    # 引擎三：服饰词典
    for kw in COSTUME_DICT:
        if kw in text:
            entities.append({"type": "costume", "value": kw, "raw": kw, "confidence": 0.9})
    # 去重
    seen = set()
    unique = []
    for e in entities:
        key = (e["type"], e["value"])
        if key not in seen:
            seen.add(key)
            unique.append(e)
    return unique


def summarize_news(title: str, content: str) -> str:
    """AI 三句话摘要。"""
    messages = [
        {"role": "system", "content": "你是文博编辑，将资讯压缩为三句话中文摘要，客观平实。"},
        {"role": "user", "content": f"标题：{title}\n正文：{content[:2000]}"},
    ]
    out = chat_completion(messages, max_tokens=200)
    if out.startswith("["):
        # 降级摘要
        plain = re.sub(r"\s+", " ", content[:180])
        return f"{plain}……"
    return out


def generate_recommend_questions(entities: list[dict[str, Any]]) -> list[str]:
    dynasty = next((e["value"] for e in entities if e["type"] == "dynasty"), None)
    costume = next((e["value"] for e in entities if e["type"] == "costume"), None)
    questions = []
    if dynasty:
        questions.append(f"{dynasty}时期服饰形制有什么典型特征？")
    if costume:
        questions.append(f"如何区分正统{costume}复原与现代影楼装？")
    questions.append("历代服饰演变背后的礼制逻辑是什么？")
    return questions


def run_news_pipeline(title: str, content: str) -> dict[str, Any]:
    """完整流水线（供路由与 celery 调用）。"""
    entities = extract_entities(f"{title}\n{content}")
    dynasty_tags = ",".join(sorted({e["value"] for e in entities if e["type"] == "dynasty"}))
    costume_tags = ",".join(sorted({e["value"] for e in entities if e["type"] == "costume"}))
    summary = summarize_news(title, content)
    low_confidence = [e for e in entities if e["confidence"] < 0.85]
    return {
        "title": title,
        "summary": summary,
        "dynasty_tags": dynasty_tags,
        "entity_tags": costume_tags,
        "ai_questions": generate_recommend_questions(entities),
        "need_review": len(low_confidence) > 0,
        "entities": entities,
    }
