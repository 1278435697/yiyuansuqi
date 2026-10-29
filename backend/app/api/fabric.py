"""服装面料版块 · 历代面料溯源（原料/工艺/朝代/文物实例）+ 全网搜索 + 用户自主创建"""
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.ai_engine.archive_codes import code_of
from app.db.database import get_db
from app.db.models import Fabrics, Users
from app.core.security import get_current_user
from app.api.websearch import web_search
from app.api.fabric_profiles import FABRIC_PROFILES_MAP
from app.api.craft_profiles import CRAFT_MAP, NAME_ALIAS

router = APIRouter()


class FabricIn(BaseModel):
    name: str
    category: str = ""
    raw_material: str = ""
    dynasty_peak: str = ""
    technique: str = ""
    description: str = ""
    image_url: str = ""
    source_ref: str = ""
    craft: dict = {}             # {history_note, steps:[{label,desc}], images:{}, name}
    poems: list = []             # [{src, text, url}]


@router.get("/list")
def fabric_list(category: str | None = None, q: str | None = None, db: Session = Depends(get_db)):
    """面料列表：支持分类筛选 + 名称关键词检索（答后推荐卡复用）。"""
    query = db.query(Fabrics)
    if category:
        query = query.filter(Fabrics.category == category)
    if q:
        query = query.filter(Fabrics.name.contains(q.strip()))
    items = query.order_by(Fabrics.id).all()
    profile_items = []
    for f in items:
        item = {
            "id": f.id, "code": code_of("fabric", f.id), "name": f.name, "category": f.category,
            "raw_material": f.raw_material, "dynasty_peak": f.dynasty_peak,
            "technique": f.technique, "description": f.description,
            "image_url": f.image_url or "", "source_ref": f.source_ref or "",
            "created_by": f.created_by,
        }
        prof = FABRIC_PROFILES_MAP.get(f.name)
        if prof:
            item["process"] = prof["process"]
            item["process_steps"] = prof.get("process_steps", [])
            item["poems"] = prof["poems"]
        else:
            item["process"] = ""
            item["process_steps"] = []
            item["poems"] = []
        # 面料工艺素材（分步流程 / 工艺示意图 / 史料依据）
        if f.created_by:
            craft = f.craft or None
            item["poems"] = f.poems or []
        else:
            craft = CRAFT_MAP.get(f.name) or CRAFT_MAP.get(NAME_ALIAS.get(f.name, ""))
        item["craft"] = craft or None
        profile_items.append(item)
    return {
        "total": len(items),
        "categories": [r[0] for r in db.query(Fabrics.category).distinct().all() if r[0]],
        "items": profile_items,
    }


@router.post("/")
def create_fabric(
    body: FabricIn,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """用户自主创建面料档案。"""
    name = body.name.strip()
    if not name:
        return {"error": "面料名称不能为空"}
    f = Fabrics(
        name=name, category=body.category, raw_material=body.raw_material,
        dynasty_peak=body.dynasty_peak, technique=body.technique,
        description=body.description, image_url=body.image_url,
        source_ref=body.source_ref or "用户创建", created_by=user.id,
        craft=body.craft or {}, poems=body.poems or [],
    )
    db.add(f)
    db.commit()
    db.refresh(f)
    return {"id": f.id, "name": f.name, "category": f.category}


@router.delete("/{fabric_id}")
def delete_fabric(
    fabric_id: int,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """用户删除自主创建的面料档案（created_by 有值或来源为用户创建）。"""
    f = db.get(Fabrics, fabric_id)
    if not f:
        return {"error": "面料不存在"}
    if not f.created_by and (f.source_ref or "") != "用户创建":
        return {"error": "只能删除用户创建的面料"}
    db.delete(f)
    db.commit()
    return {"ok": True, "id": fabric_id}


@router.get("/web-search")
def fabric_web_search_api(
    q: str = Query(..., min_length=1, max_length=80, description="搜索关键词"),
    n: int = Query(8, ge=1, le=12),
):
    """面料全网搜索（复用 Bing 代理）。"""
    if not q.strip():
        return {"query": q, "results": [], "error": "关键词不能为空"}
    try:
        results = web_search(q.strip(), n)
        return {"query": q.strip(), "total": len(results), "results": results, "error": ""}
    except Exception as e:
        return {"query": q.strip(), "total": 0, "results": [], "error": f"全网搜索暂不可用（{type(e).__name__}），可稍后重试"}
