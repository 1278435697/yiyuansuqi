"""模块2 · 衣溯AI核心档案（AI 第一人称溯源对话 + 知识图谱联动）"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.ai_engine.archive_codes import code_of
from app.ai_engine.first_person_chat import first_person_chat
from app.ai_engine.graphrag_engine import graphrag_answer
from app.db.database import get_db
from app.db.models import Costumes, CostumeRelations, AiConversations, Users
from app.core.security import get_current_user, get_optional_user

router = APIRouter()


class ChatIn(BaseModel):
    costume_id: int | None = None
    message: str


class CostumeIn(BaseModel):
    name: str
    dynasty: str
    category: str = ""
    wearer: str = ""
    source_type: str = "用户创建"
    fabric: str = ""
    pattern: str = ""
    color: str = ""
    description: str = ""
    image_url: str = ""


@router.post("/costumes")
def create_costume(
    body: CostumeIn,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """用户自主创建服饰档案。"""
    name = body.name.strip()
    if not name:
        return {"error": "服饰名称不能为空"}
    if not body.dynasty:
        return {"error": "请选择朝代"}
    c = Costumes(
        name=name, dynasty=body.dynasty, category=body.category,
        wearer=body.wearer, source_type=body.source_type or "用户创建",
        fabric=body.fabric, pattern=body.pattern, color=body.color,
        description=body.description, image_url=body.image_url,
        created_by=user.id,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    return {"id": c.id, "name": c.name, "dynasty": c.dynasty}


@router.delete("/costumes/{costume_id}")
def delete_costume(
    costume_id: int,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """用户删除自主创建的服饰档案（source_type=用户创建）。"""
    c = db.get(Costumes, costume_id)
    if not c:
        return {"error": "档案不存在"}
    if (c.source_type or "") != "用户创建":
        return {"error": "只能删除用户创建的档案"}
    for rel in list(c.relations or []):
        db.delete(rel)
    db.delete(c)
    db.commit()
    return {"ok": True, "id": costume_id}


@router.get("/costumes")
def costume_list(
    dynasty: str | None = None,
    category: str | None = None,
    keyword: str | None = None,
    source_type: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(12, ge=1, le=50),
    db: Session = Depends(get_db),
):
    q = db.query(Costumes)
    if dynasty:
        q = q.filter(Costumes.dynasty == dynasty)
    if category:
        q = q.filter(Costumes.category == category)
    if source_type:
        q = q.filter(Costumes.source_type == source_type)
    if keyword:
        q = q.filter(or_(Costumes.name.like(f"%{keyword}%"),
                         Costumes.description.like(f"%{keyword}%")))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total, "page": page,
        "items": [{
            "id": c.id, "name": c.name, "dynasty": c.dynasty, "category": c.category,
            "wearer": c.wearer, "source_type": c.source_type, "fabric": c.fabric,
            "pattern": c.pattern, "color": c.color,
            "image_url": c.image_url or "",
            "created_by": c.created_by,
            "description": (c.description or "")[:100],
        } for c in items],
    }


@router.get("/costumes/{costume_id}")
def costume_detail(costume_id: int, db: Session = Depends(get_db)):
    c = db.get(Costumes, costume_id)
    if not c:
        return {"error": "档案不存在"}
    relations = [{"type": r.relation_type, "value": r.target_value,
                  "source_ref": r.source_ref} for r in c.relations or []]
    return {
        "id": c.id, "code": code_of("costume", c.id),
        "name": c.name, "dynasty": c.dynasty, "category": c.category,
        "wearer": c.wearer, "source_type": c.source_type, "fabric": c.fabric,
        "pattern": c.pattern, "color": c.color, "shape_json": c.shape_json,
        "description": c.description, "relations": relations, "created_by": c.created_by,
        "relic": {
            "name": c.relic.name, "location": c.relic.location,
            "museum": c.relic.museum, "geo_lat": c.relic.geo_lat, "geo_lng": c.relic.geo_lng,
        } if c.relic else None,
    }


@router.get("/costumes/{costume_id}/relations")
def costume_relations(costume_id: int, db: Session = Depends(get_db)):
    rows = db.query(CostumeRelations).filter_by(costume_id=costume_id).all()
    return {"nodes": [{"type": r.relation_type, "value": r.target_value,
                       "source_ref": r.source_ref} for r in rows]}


@router.post("/chat")
def chat(
    body: ChatIn,
    db: Session = Depends(get_db),
    user: Users | None = Depends(get_optional_user),
):
    costume = db.get(Costumes, body.costume_id)
    if not costume:
        return {"error": "档案不存在"}
    result = first_person_chat(body.message, costume, db)
    # 记录对话
    if user is not None:
        db.add(AiConversations(user_id=user.id, costume_id=costume.id,
                               role="user", content=body.message))
        db.add(AiConversations(user_id=user.id, costume_id=costume.id,
                               role="assistant", content=result["answer"],
                               source_ref=result["source_ref"]))
        db.commit()
    return result


@router.post("/ask")
def ask(body: ChatIn, db: Session = Depends(get_db)):
    """无档案约束的溯源问答。"""
    costume = db.get(Costumes, body.costume_id) if body.costume_id else None
    return graphrag_answer(body.message, costume=costume, db=db)


@router.get("/eras")
def eras(db: Session = Depends(get_db)):
    """档案按朝代分组统计（供筛选器）。"""
    rows = db.query(Costumes.dynasty).distinct().all()
    return {"eras": [{"name": r[0]} for r in rows if r[0]]}


@router.get("/lookup")
def lookup(code: str, db: Session = Depends(get_db)):
    """按编号查找档案，支持模糊匹配。"""
    import re
    c = code.strip()
    if not c:
        return {"found": False, "msg": "编号不能为空"}
    # 尝试直接按 code 字段精确匹配
    row = db.query(Costumes).filter(Costumes.code == c).first()
    if not row:
        # 模糊匹配：去掉"档案-"前缀再试
        c2 = re.sub(r'^(档案|衣制|面料|纹样|配饰)-?', '', c)
        row = db.query(Costumes).filter(Costumes.code.contains(c2)).first()
    if row:
        return {
            "found": True,
            "id": row.id,
            "code": row.code,
            "title": row.name,
            "url": f"/archive?id={row.id}",
        }
    return {"found": False, "msg": "未找到"}
