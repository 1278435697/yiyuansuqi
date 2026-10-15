"""模块5 · 交互式服饰版型制作工坊（核心亮点）

2D 纸样编辑 + 史料约束实时校验 + AI 多模态复原 + 3D 试穿预览
"""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai_engine.multi_modal_revive import generate_revival_image
from app.ai_engine.pattern_checker import validate_pattern
from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import (
    Costumes, PatternTemplates, PatternConstraintRules,
    UserDraftPatterns, RevivalWorks, Users,
)

router = APIRouter()


class DraftCreate(BaseModel):
    template_id: int | None = None
    costume_id: int | None = None
    draft_name: str = "未命名复原稿"
    outline_data: str = ""
    params: dict[str, float] = {}
    fabric: str = ""
    pattern_id: int | None = None


class RenderBody(BaseModel):
    draft_id: int
    reference_url: str | None = None


@router.get("/templates")
def list_templates(dynasty: str | None = None, db: Session = Depends(get_db)):
    q = db.query(PatternTemplates)
    if dynasty:
        q = q.filter(PatternTemplates.dynasty == dynasty)
    items = q.all()
    return {"items": [{
        "id": t.id, "name": t.name, "dynasty": t.dynasty,
        "costume_id": t.costume_id, "param_constraints": t.param_constraints,
        "source_ref": t.source_ref, "cover_url": t.cover_url,
    } for t in items]}


@router.get("/templates/{template_id}")
def template_detail(template_id: int, db: Session = Depends(get_db)):
    t = db.get(PatternTemplates, template_id)
    if not t:
        return {"error": "模板不存在"}
    import json
    return {
        "id": t.id, "name": t.name, "dynasty": t.dynasty,
        "pattern_json": json.loads(t.pattern_json) if t.pattern_json else {},
        "param_constraints": json.loads(t.param_constraints) if t.param_constraints else {},
        "source_ref": t.source_ref,
    }


class ValidateIn(BaseModel):
    dynasty: str
    params: dict[str, float] = Field(default_factory=dict)


@router.post("/validate")
def validate(body: ValidateIn, db: Session = Depends(get_db)):
    """史料约束实时校验。"""
    return validate_pattern(body.dynasty, body.params, db)


@router.get("/constraint-rules")
def constraint_rules(db: Session = Depends(get_db)):
    rows = db.query(PatternConstraintRules).all()
    return {"items": [{
        "id": r.id, "dynasty": r.dynasty, "costume_type": r.costume_type,
        "rule_json": r.rule_json, "reference_source": r.reference_source,
    } for r in rows]}


@router.post("/drafts")
def save_draft(
    body: DraftCreate,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    draft = UserDraftPatterns(
        user_id=user.id, template_id=body.template_id, costume_id=body.costume_id,
        draft_name=body.draft_name, outline_data=body.outline_data,
        params=str(body.params), fabric=body.fabric, pattern_id=body.pattern_id,
    )
    db.add(draft)
    db.commit()
    db.refresh(draft)
    return {"id": draft.id, "draft_name": draft.draft_name}


@router.get("/drafts")
def my_drafts(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    items = db.query(UserDraftPatterns).filter_by(user_id=user.id) \
             .order_by(UserDraftPatterns.update_time.desc()).all()
    return {"items": [{
        "id": d.id, "draft_name": d.draft_name, "template_id": d.template_id,
        "costume_id": d.costume_id, "outline_data": d.outline_data,
        "params": d.params, "fabric": d.fabric, "preview_url": d.preview_url,
        "update_time": d.update_time.isoformat() if d.update_time else None,
    } for d in items]}


@router.get("/drafts/{draft_id}")
def draft_detail(draft_id: int, db: Session = Depends(get_db),
                 user: Users = Depends(get_current_user)):
    d = db.get(UserDraftPatterns, draft_id)
    if not d or d.user_id != user.id:
        return {"error": "草稿不存在"}
    import json
    return {
        "id": d.id, "draft_name": d.draft_name, "costume_id": d.costume_id,
        "template_id": d.template_id,
        "outline_data": json.loads(d.outline_data) if d.outline_data else {},
        "params": json.loads(d.params) if d.params else {},
        "fabric": d.fabric,
    }


@router.post("/drafts/{draft_id}/render")
def render_draft(
    draft_id: int,
    body: RenderBody,
    db: Session = Depends(get_db),
    user: Users = Depends(get_current_user),
):
    """基于草稿参数触发 AI 复原渲染，生成溯源档案卡。"""
    d = db.get(UserDraftPatterns, draft_id)
    if not d or d.user_id != user.id:
        return {"error": "草稿不存在"}
    import json
    params = json.loads(d.params) if d.params else {}
    costume = db.get(Costumes, d.costume_id) if d.costume_id else None
    costume_dict = {
        "dynasty": costume.dynasty if costume else "未知",
        "name": costume.name if costume else "服饰",
        "fabric": d.fabric or (costume.fabric if costume else ""),
        "pattern": costume.pattern if costume else "",
    }
    result = generate_revival_image(costume_dict, params, body.reference_url)
    work = RevivalWorks(
        user_id=user.id, costume_id=d.costume_id, draft_id=draft_id,
        image_url=result.get("image_url", ""), video_url=result.get("video_url", ""),
        confidence=result.get("confidence", 0), source_card=result.get("source_card", ""),
        params=json.dumps(params, ensure_ascii=False),
    )
    db.add(work)
    d.preview_url = result.get("image_url", "")
    db.commit()
    db.refresh(work)
    return {"work_id": work.id, **result}


@router.get("/works/{work_id}")
def work_detail(work_id: int, db: Session = Depends(get_db)):
    w = db.get(RevivalWorks, work_id)
    if not w:
        return {"error": "作品不存在"}
    return {
        "id": w.id, "costume_id": w.costume_id, "draft_id": w.draft_id,
        "image_url": w.image_url, "video_url": w.video_url, "audio_url": w.audio_url,
        "pattern_svg": w.pattern_svg, "color_palette": w.color_palette,
        "confidence": w.confidence, "source_card": w.source_card, "params": w.params,
        "is_public": w.is_public,
    }
