"""模块9 · 文化传承生成模块（个性化学习方案 + 科普卡片 + 承诺/分享）"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai_engine.llm_client import chat_completion
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import Users, UserCostumeLog, Costumes, RevivalWorks

router = APIRouter()


class CardIn(BaseModel):
    title: str = ""
    text: str = ""
    theme: str = "古风"


@router.get("/profile")
def heritage_profile(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """基于用户互动行为生成个性化画像。"""
    logs = db.query(UserCostumeLog).filter_by(user_id=user.id).all()
    works = db.query(RevivalWorks).filter_by(user_id=user.id).count()
    top_costume_ids = {}
    for log in logs:
        top_costume_ids[log.costume_id] = top_costume_ids.get(log.costume_id, 0) + 1
    top_ids = sorted(top_costume_ids, key=top_costume_ids.get, reverse=True)[:3]
    top_costumes = []
    for cid in top_ids:
        c = db.get(Costumes, cid)
        if c:
            top_costumes.append({"id": c.id, "name": c.name, "dynasty": c.dynasty})
    return {
        "username": user.username,
        "total_interactions": len(logs),
        "revival_works": works,
        "focus_costumes": top_costumes,
    }


@router.post("/generate-plan")
def generate_plan(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """个性化服饰文化学习方案。"""
    profile = heritage_profile(db=db, user=user)
    focus = "、".join(c["name"] for c in profile["focus_costumes"]) or "历代服饰"
    messages = [
        {"role": "system", "content": "你是传统文化学习规划师，输出简明可执行的服饰史学习方案，分三阶段。"},
        {"role": "user", "content": f"用户对{focus}感兴趣，已有{profile['total_interactions']}次溯源学习互动，"
                                     f"复原作品{profile['revival_works']}件。请生成两周学习方案。"},
    ]
    plan = chat_completion(messages, max_tokens=800)
    if plan.startswith("["):
        plan = (
            f"第1阶段（3天）：通读{focus}相关档案与史料引用，建立形制认知；\n"
            f"第2阶段（4天）：使用版型工坊亲手复原一件{focus}，体会裁剪逻辑；\n"
            f"第3阶段（7天）：参与社区讨论并生成科普分享卡片，巩固知识输出。"
        )
    return {"plan": plan, "focus": profile["focus_costumes"]}


@router.post("/generate-card")
def generate_card(body: CardIn, db: Session = Depends(get_db),
                  user: Users = Depends(get_current_user)):
    """生成可分享的科普卡片文案。"""
    theme_hint = "古风典雅，适合国风文化分享" if body.theme == "古风" else "现代简约"
    messages = [
        {"role": "system", "content": f"你是国风科普编辑。生成120字以内的分享卡片文案，{theme_hint}，结尾带一句文化传承寄语。"},
        {"role": "user", "content": body.title + "\n" + body.text},
    ]
    text = chat_completion(messages, max_tokens=300)
    if text.startswith("["):
        text = f"「{body.title}」——{body.text[:60]}……衣冠承古，溯源知新。"
    return {
        "card": {
            "title": body.title,
            "text": text,
            "username": user.username,
            "theme": body.theme,
            "watermark": "衣溯AI · 史料溯源生成",
        }
    }


@router.post("/commitment")
def generate_commitment(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """个人保护承诺生成器（项目书行动转化：此处为文化传承承诺）。"""
    profile = heritage_profile(db=db, user=user)
    focus = "、".join(c["name"] for c in profile["focus_costumes"]) or "华夏服饰文化"
    commitment = (
        f"我承诺：持续通过衣溯AI学习{focus}的形制与史料，"
        "在网络科普中坚持『无出处不传播』，"
        "亲手参与至少一次服饰复原创作，并向身边人分享一次正统服饰文化。"
    )
    return {"commitment": commitment, "focus": focus}
