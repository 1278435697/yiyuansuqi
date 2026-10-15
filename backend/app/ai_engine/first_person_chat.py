"""服饰文物第一人称 AI 溯源对话（创新点二）"""
from __future__ import annotations

from typing import Any

from sqlalchemy.orm import Session

from app.ai_engine.graphrag_engine import graphrag_answer
from app.ai_engine.llm_client import chat_completion
from app.db.models import Costumes


def build_persona(costume: Costumes) -> str:
    return (
        f"你是「{costume.name}」，一件出土于{costume.dynasty}时代的{costume.category or '古代服饰'}文物。"
        f"你的形制特征：{costume.description or '见出土记录'}；面料为{costume.fabric}；"
        f"纹样为{costume.pattern}。以第一人称『我』的口吻与用户对话，"
        f"讲述你的穿着体验、面料质感、礼仪场合与出土溯源。回答有史料依据，不虚构经历。"
    )


def first_person_chat(
    user_message: str,
    costume: Costumes,
    db: Session | None = None,
) -> dict[str, Any]:
    # 先经 GraphRAG 召回史料
    retrieval = graphrag_answer(user_message, costume=costume, db=db)
    messages = [
        {"role": "system", "content": build_persona(costume)},
        {"role": "user", "content": user_message},
    ]
    answer = chat_completion(messages)
    if answer.startswith("[演示模式]") or answer.startswith("[服务暂不可用]"):
        # 降级：用检索到的史料组织第一人称回复，保证演示可看
        answer = (
            f"我是一件{costume.dynasty}时期的{costume.name}。"
            f"据史料记载：{retrieval['context'][:120]}。"
            f"你能这样向我提问，真让我感到千年的时光并不遥远。"
        )
    return {
        "answer": answer,
        "source_ref": retrieval["source_ref"],
        "costume_id": costume.id,
    }
