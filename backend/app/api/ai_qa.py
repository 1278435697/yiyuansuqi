"""模块6 · AI 智能溯源问答（AI 初答 + 社区勘误共治）"""
from datetime import datetime

import requests
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai_engine.graphrag_engine import graphrag_answer, graphrag_chat, graphrag_chat_stream
from app.ai_engine.query_terms import build_dictionary, dynasties_in, extract_terms
from app.ai_engine.retrieval import retrieve
from app.core.config import settings
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Questions, Answers, Users

router = APIRouter()


class QuestionIn(BaseModel):
    title: str
    content: str
    dynasty_tags: str = ""


class AnswerIn(BaseModel):
    content: str


class ChatIn(BaseModel):
    question: str
    history: list[dict] = []
    image_base64: str = ""   # 可选：截图/照片（data:image/...;base64, 纯 base64 均可）


def _describe_outfit_image(image_b64: str) -> str:
    """调用豆包视觉模型描述服饰图片，返回结构化文字描述。失败返回空串。"""
    if not image_b64:
        return ""
    url = image_b64 if image_b64.startswith("data:image") else f"data:image/jpeg;base64,{image_b64}"
    api_key = settings.LLM_API_KEY
    if not api_key or api_key.startswith("sk-your"):
        return ""
    try:
        resp = requests.post(
            f"{settings.LLM_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": settings.LLM_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": (
                                "你是华夏服饰史研究员。请观察这张服饰/文物截图，用 120 字以内客观描述："
                                "服饰类别（深衣/袍/襦裙/补服/冠帽等）、颜色与面料质感、纹样题材（龙凤/缠枝/云纹等）、"
                                "可见形制特征（交领/圆领/宽袖/系带等）、疑似朝代。只描述可见事实，不编造。"
                            )},
                            {"type": "image_url", "image_url": {"url": url}},
                        ],
                    }
                ],
                "temperature": 0.2,
                "max_tokens": 300,
            },
            timeout=45,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"].strip()
    except Exception as exc:
        return f"[图片识别暂不可用] {exc}"


@router.post("/chat")
def ai_chat(body: ChatIn, db: Session = Depends(get_db)):
    """多轮溯源对话：豆包大模型生成，支持连续追问；带截图时先视觉识别再 RAG。"""
    q = (body.question or "").strip()
    if not q and not body.image_base64:
        raise HTTPException(400, "问题不能为空")
    # 有图：先视觉识别，把描述作为上下文拼进问题
    image_note = ""
    if body.image_base64:
        image_note = _describe_outfit_image(body.image_base64)
        if image_note and not image_note.startswith("["):
            q = f"{q}\n[参考截图识别] {image_note}\n请结合这张截图/照片回答。" if q else f"请识别并介绍这张服饰截图：{image_note}"
    rag = graphrag_chat(q, body.history or [], db=db)
    return {
        "answer": rag["answer"],
        "source_ref": rag["source_ref"],
        "sources": rag["sources"],
        "image_note": image_note,
        "note": "AI 溯源对话：回答优先依据衣溯史料知识库；带截图时已先做视觉识别。仅供参考。",
    }


@router.post("/chat/stream")
def ai_chat_stream(body: ChatIn, db: Session = Depends(get_db)):
    """流式 SSE 对话：先视觉识别（如有图），再逐 token 推送 RAG 回答。"""
    import json as _json

    q = (body.question or "").strip()
    if not q and not body.image_base64:
        raise HTTPException(400, "问题不能为空")
    if body.image_base64:
        note = _describe_outfit_image(body.image_base64)
        if note and not note.startswith("["):
            q = f"{q}\n[参考截图识别] {note}\n请结合这张截图/照片回答。" if q else f"请识别并介绍这张服饰截图：{note}"
    else:
        note = ""

    def gen():
        # 先推图识别结果（前端可在等待时展示）
        if note:
            yield f"event: meta\ndata: {_json.dumps({'image_note': note}, ensure_ascii=False)}\n\n"
        for ev, data in graphrag_chat_stream(q, body.history or [], db=db):
            if ev == "meta":
                yield f"event: meta\ndata: {data}\n\n"
            elif ev == "delta":
                yield f"event: delta\ndata: {_json.dumps(data, ensure_ascii=False)}\n\n"
            else:
                yield "event: done\ndata: {}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.post("/questions")
def create_question(
    body: QuestionIn,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """提问：AI 基于 RAG 知识库先行回答，社区随后补充勘误。"""
    rag = graphrag_answer(body.title + " " + body.content, db=db)
    q = Questions(
        user_id=user.id, title=body.title, content=body.content,
        dynasty_tags=body.dynasty_tags, ai_answer=rag["answer"],
        ai_source_ref=rag["source_ref"],
    )
    db.add(q)
    db.commit()
    db.refresh(q)
    return {
        "id": q.id, "title": q.title, "ai_answer": q.ai_answer,
        "ai_source_ref": q.ai_source_ref,
        "note": "以上为 AI 初步回答，仅供参考；社区勘误与补充回答将随后展示。",
    }


@router.get("/questions")
def question_list(
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    dynasty: str | None = None, db: Session = Depends(get_db),
):
    q = db.query(Questions)
    if dynasty:
        q = q.filter(Questions.dynasty_tags.like(f"%{dynasty}%"))
    total = q.count()
    items = q.order_by(Questions.create_time.desc()).offset((page - 1) * page_size).limit(page_size).all()
    ids = {x.user_id for x in items if x.user_id}
    unames = {u.id: u.username for u in db.query(Users).filter(Users.id.in_(ids)).all()}
    return {"total": total, "page": page, "items": [{
        "id": x.id, "title": x.title, "content": (x.content or "")[:120],
        "dynasty_tags": x.dynasty_tags, "ai_answer": x.ai_answer[:80] if x.ai_answer else "",
        "ai_source_ref": x.ai_source_ref, "answer_count": len(x.id and [1]),
        "user_id": x.user_id,
        "user_name": unames.get(x.user_id) or "匿名用户",
        "create_time": x.create_time.isoformat() if x.create_time else None,
    } for x in items]}


@router.delete("/questions/{qid}")
def delete_question(qid: int, db: Session = Depends(get_db),
                    user: Users = Depends(get_current_user)):
    """删除溯源问答问题（仅提问者本人或管理员），级联删除回答与同步的社区帖。"""
    from app.db.models import ForumPosts
    q = db.get(Questions, qid)
    if not q:
        raise HTTPException(404, "问题不存在")
    if q.user_id != user.id and user.role != "admin":
        raise HTTPException(403, "仅提问者本人或管理员可删除")
    # 级联删除同步到社区的讨论帖
    post = db.query(ForumPosts).filter(
        ForumPosts.title == q.title,
        ForumPosts.content.like("%本讨论源自溯源问答%"),
    ).first()
    if post:
        if post.board:
            post.board.post_count = max((post.board.post_count or 1) - 1, 0)
        db.delete(post)
    # 删除社区回答
    db.query(Answers).filter_by(question_id=qid).delete()
    db.delete(q)
    db.commit()
    return {"ok": True, "deleted_question": qid}


@router.get("/questions/{qid}")
def question_detail(qid: int, db: Session = Depends(get_db)):
    q = db.get(Questions, qid)
    if not q:
        return {"error": "问题不存在"}
    answers = db.query(Answers).filter_by(question_id=qid).all()
    return {
        "id": q.id, "title": q.title, "content": q.content,
        "dynasty_tags": q.dynasty_tags, "ai_answer": q.ai_answer,
        "ai_source_ref": q.ai_source_ref,
        "answers": [{
            "id": a.id, "user_id": a.user_id, "content": a.content,
            "is_ai_answer": a.is_ai_answer, "source_ref": a.source_ref,
            "vote_count": a.vote_count,
            "create_time": a.create_time.isoformat() if a.create_time else None,
        } for a in answers],
    }


@router.post("/questions/{qid}/to_post")
def question_to_post(qid: int, db: Session = Depends(get_db),
                     user: Users = Depends(get_current_user)):
    """把溯源问答转为社区讨论帖（问答↔社区联动）。"""
    from app.db.models import ForumBoards, ForumPosts
    q = db.get(Questions, qid)
    if not q:
        raise HTTPException(404, "问题不存在")
    board = db.query(ForumBoards).filter(ForumBoards.name.like("%形制溯源%")).first() \
        or db.query(ForumBoards).first()
    if not board:
        raise HTTPException(500, "社区板块未初始化")
    # 防重复：同一问题只转帖一次
    dup = db.query(ForumPosts).filter(
        ForumPosts.title == q.title,
        ForumPosts.content.like("%本讨论源自溯源问答%"),
    ).first()
    if dup:
        return {"post_id": dup.id, "board_name": dup.board.name if dup.board else board.name, "duplicated": True}
    content = f"【本讨论源自溯源问答】\n\n**问题：**{q.title}\n\n**AI 溯源回答：**\n{q.ai_answer}"
    if q.content:
        content += f"\n\n**补充描述：**{q.content}"
    p = ForumPosts(board_id=board.id, user_id=user.id, title=q.title,
                   content=content, dynasty_tags=q.dynasty_tags or "")
    db.add(p)
    board.post_count = (board.post_count or 0) + 1
    db.commit()
    db.refresh(p)
    return {"post_id": p.id, "board_name": board.name}


@router.post("/questions/{qid}/answers")
def add_answer(
    qid: int, body: AnswerIn,
    db: Session = Depends(get_db), user: Users = Depends(get_current_user),
):
    a = Answers(question_id=qid, user_id=user.id, content=body.content)
    db.add(a)
    db.commit()
    db.refresh(a)
    return {"id": a.id, "content": a.content, "is_ai_answer": False}


@router.post("/answers/{aid}/verify")
def ai_verify_answer(aid: int, db: Session = Depends(get_db)):
    """AI 纠错标记者：检测社区回答与知识库冲突。"""
    a = db.get(Answers, aid)
    if not a:
        return {"error": "回答不存在"}
    rag = graphrag_answer(a.content, db=db)
    # 简单冲突检测：回答包含知识库中明确否定的表述
    conflict = "朝代混搭" in a.content or "影楼" in a.content.lower()
    return {
        "answer_id": aid,
        "conflict_detected": conflict,
        "verdict": "回答与知识库存在冲突，建议复核" if conflict else "回答与知识库基本一致",
        "reference": rag["source_ref"],
    }


# ===== 答后推荐检索（四类站内资料卡 + 推荐追问） =====

_CARD_KEYS = ("type", "id", "code", "title", "subtitle", "image_url", "link", "external", "exact")
_ASK_ANGLES = {
    "costume": ["形制", "面料", "出土溯源", "常见搭配"],
    "pattern": ["寓意", "常见搭配", "盛行朝代"],
    "fabric": ["工艺流程", "代表纹样", "原料"],
}


def _asks(cards: list[dict]) -> list[str]:
    """推荐追问只从已命中的站内实体生成，保证每个问题背后都有资料可读，且不额外调模型。

    资讯标题是整句话、配饰九卷没有预设追问角度，两类都不拿来当追问主体。
    """
    out: list[str] = []
    for card in [c for c in cards if c["type"] in _ASK_ANGLES][:2]:
        for angle in _ASK_ANGLES[card["type"]][:2]:
            ask = f"{card['title']}的{angle}是什么？"
            if ask not in out:
                out.append(ask)
    return out[:4]


@router.get("/recommend")
def recommend(
    q: str = "",
    limit: int = Query(8, ge=1, le=12),
    db: Session = Depends(get_db),
):
    """答后推荐检索：与对话召回同一入口（app.ai_engine.retrieval.retrieve），卡片只给导航字段。"""
    question = (q or "").strip()
    if not question:
        return {"keywords": [], "dynasties": [], "cards": [], "asks": []}
    items = retrieve(question, db, per_type=3, limit=limit)
    cards = [{key: item[key] for key in _CARD_KEYS} for item in items]
    return {"keywords": extract_terms(question, build_dictionary(db)),
            "dynasties": dynasties_in(question), "cards": cards, "asks": _asks(cards)}

