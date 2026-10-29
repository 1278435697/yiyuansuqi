"""纹样资料库版块 · 十大分类 321 条纹样（文化寓意/朝代脉络/属性/文物图/常见搭配）+ 用户自主添加"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.ai_engine.archive_codes import code_of
from app.db.database import get_db
from app.db.models import PatternLibrary, Users
from app.core.security import get_current_user

router = APIRouter()


class PatternIn(BaseModel):
    name: str
    category: str = ""
    dynasty: str = ""
    meaning: str = ""
    image_url: str = ""          # 封面图
    images: list = []            # [{url, caption}]
    dynasties: list = []         # 朝代脉络 [{period, desc}]
    meanings: list = []          # 寓意分条
    props: dict = {}             # {常用颜色,常用布料,适用衣物,应用部位,使用场景}
    pairs: list = []             # 常见搭配
    applied: str = ""


@router.get("/categories")
def pattern_categories(db: Session = Depends(get_db)):
    """十大分类及其数量。"""
    rows = (
        db.query(PatternLibrary.category)
        .filter(PatternLibrary.category != "")
        .distinct()
        .all()
    )
    cats = []
    for (c,) in rows:
        n = db.query(PatternLibrary).filter_by(category=c).count()
        cats.append({"name": c, "count": n})
    cats.sort(key=lambda x: -x["count"])
    return {"total": db.query(PatternLibrary).count(), "categories": cats}


@router.get("/items")
def pattern_items(
    category: str | None = None,
    q: str | None = None,
    db: Session = Depends(get_db),
):
    """纹样列表：支持分类筛选 + 名称关键词搜索。"""
    query = db.query(PatternLibrary)
    if category:
        query = query.filter(PatternLibrary.category == category)
    if q:
        query = query.filter(PatternLibrary.name.contains(q.strip()))
    items = query.order_by(PatternLibrary.code.asc(), PatternLibrary.id).all()
    result = []
    for p in items:
        imgs = p.images or []
        result.append({
            "id": p.id,
            "code": p.code or 0,
            "name": p.name,
            "category": p.category,
            "dynasty": p.dynasty or "",
            "meaning": p.meaning or "",
            "image_url": imgs[0]["url"] if imgs else "",
            "image_count": len(imgs),
            "created_by": p.created_by or 0,
        })
    return {"total": len(items), "items": result}


@router.post("/")
def create_pattern(
    body: PatternIn,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """用户自主添加纹样。"""
    name = body.name.strip()
    if not name:
        return {"error": "纹样名称不能为空"}
    cat = body.category.strip() or "自定义"
    seq = (
        db.query(PatternLibrary)
        .filter(PatternLibrary.category == cat)
        .count()
        + 1
    )
    images = []
    if body.image_url and body.image_url.strip():
        images = [{"url": body.image_url.strip(), "caption": name + " · 用户上传"}]
    elif body.images:
        images = [i for i in body.images if i and i.get("url")]
    dynasties = [d for d in (body.dynasties or []) if d and d.get("period")]
    dynasty = body.dynasty or (dynasties[0].get("period", "") if dynasties else "")
    max_code = db.query(func.max(PatternLibrary.code)).scalar() or 0
    p = PatternLibrary(
        code=max_code + 1, name=name, category=cat, seq=seq,
        dynasty=dynasty or "", meaning=body.meaning or "",
        images=images, dynasties=dynasties, meanings=body.meanings or [],
        props=body.props or {}, pairs=body.pairs or [],
        compose="", similar="", applied=body.applied or "",
        created_by=user.id,
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"id": p.id, "name": p.name, "category": p.category}


@router.delete("/{pattern_id}")
def delete_pattern(
    pattern_id: int,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """用户删除自主添加的纹样（created_by 有值）。"""
    p = db.get(PatternLibrary, pattern_id)
    if not p:
        return {"error": "纹样不存在"}
    if not p.created_by:
        return {"error": "只能删除用户添加的纹样"}
    if p.created_by != user.id and user.role != "admin":
        return {"error": "只能删除自己添加的纹样"}
    db.delete(p)
    db.commit()
    return {"ok": True, "id": pattern_id}


@router.get("/{pattern_id}")
def pattern_detail(pattern_id: int, db: Session = Depends(get_db)):
    """纹样详情：全字段。"""
    p = db.get(PatternLibrary, pattern_id)
    if not p:
        return {"error": "纹样不存在"}
    return {
        "id": p.id,
        "code": p.code or 0,
        "code_ref": code_of("pattern", p.id, p.code),
        "name": p.name,
        "category": p.category,
        "seq": p.seq or 0,
        "dynasty": p.dynasty or "",
        "meaning": p.meaning or "",
        "images": p.images or [],
        "dynasties": p.dynasties or [],
        "meanings": p.meanings or [],
        "props": p.props or {},
        "pairs": p.pairs or [],
        "compose": p.compose or "",
        "similar": p.similar or "",
        "applied": p.applied or "",
        "created_by": p.created_by or 0,
    }
