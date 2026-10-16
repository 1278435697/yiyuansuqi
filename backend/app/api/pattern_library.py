"""纹样资料库版块 · 十大分类 321 条纹样（文化寓意/朝代脉络/属性/文物图/常见搭配）"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import PatternLibrary

router = APIRouter()


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
    items = query.order_by(PatternLibrary.category, PatternLibrary.seq, PatternLibrary.id).all()
    result = []
    for p in items:
        imgs = p.images or []
        result.append({
            "id": p.id,
            "name": p.name,
            "category": p.category,
            "dynasty": p.dynasty or "",
            "meaning": p.meaning or "",
            "image_url": imgs[0]["url"] if imgs else "",
            "image_count": len(imgs),
        })
    return {"total": len(items), "items": result}


@router.get("/{pattern_id}")
def pattern_detail(pattern_id: int, db: Session = Depends(get_db)):
    """纹样详情：全字段。"""
    p = db.get(PatternLibrary, pattern_id)
    if not p:
        return {"error": "纹样不存在"}
    return {
        "id": p.id,
        "code": p.code or 0,
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
    }
