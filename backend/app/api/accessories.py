"""服饰与配饰九卷 · 档案数据接口

数据读取住在 app.services.accessory_docs（接口层与 AI 检索层共用同一份 accessories.json）。
"""
from fastapi import APIRouter, HTTPException, Query

from app.services import accessory_docs
from app.services.accessory_docs import CATEGORY_ORDER, abs_paths as _abs_paths

router = APIRouter()


def _load() -> list[dict]:
    try:
        return accessory_docs.load()
    except accessory_docs.AccessoryDataMissing as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


def _brief(e: dict) -> dict:
    return _abs_paths({
        "id": e.get("id"),
        "name": e.get("name"),
        "category": e.get("category"),
        "category_en": e.get("category_en"),
        "display_no": e.get("display_no"),
        "dynasty": e.get("dynasty") or "",
        "tag": e.get("标签") or "",
        "summary": e.get("summary") or e.get("定义") or "",
        "material": e.get("material") or e.get("材质") or "",
        "photo": e.get("photo"),
        "photo_caption": e.get("photo_caption") or "",
        "photo_credit": e.get("photo_credit") or "",
    })


@router.get("/categories")
def category_overview():
    """九卷目录：卷名、英文名、条目数，按展示顺序返回。"""
    items = _load()
    counts: dict[str, int] = {}
    en: dict[str, str] = {}
    for e in items:
        c = e.get("category") or "未分类"
        counts[c] = counts.get(c, 0) + 1
        en.setdefault(c, e.get("category_en") or "")
    unknown = [c for c in counts if c not in CATEGORY_ORDER]
    order = CATEGORY_ORDER + sorted(unknown)
    return {
        "total": len(items),
        "categories": [
            {"name": c, "name_en": en.get(c, ""), "count": counts.get(c, 0)}
            for c in order if c in counts
        ],
    }


@router.get("")
def accessory_list(
    category: str | None = Query(None, description="卷名，如 手饰 / 腰佩"),
    dynasty: str | None = Query(None, description="朝代关键字，子串匹配"),
    q: str | None = Query(None, description="名称、别名、定义、材质的关键词"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    items = _load()
    if category:
        items = [e for e in items if e.get("category") == category]
    if dynasty:
        items = [e for e in items if dynasty in (e.get("dynasty") or "")]
    if q:
        kw = q.strip()
        def hit(e: dict) -> bool:
            blob = "".join(str(e.get(k) or "") for k in ("name", "别名", "定义", "简介", "材质", "标签"))
            return kw in blob
        items = [e for e in items if hit(e)]

    total = len(items)
    return {
        "total": total,
        "category": category or "全部",
        "offset": offset,
        "limit": limit,
        "items": [_brief(e) for e in items[offset:offset + limit]],
    }


@router.get("/{item_id}")
def accessory_detail(item_id: str):
    """单条完整档案，字段与 accessories.json 对齐（含 form_summary / culture_points / feature / interactive）。"""
    for e in _load():
        if e.get("id") == item_id:
            return _abs_paths(e)
    raise HTTPException(status_code=404, detail=f"未找到配饰条目：{item_id}")
