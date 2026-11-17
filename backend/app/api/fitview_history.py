"""FitView 试穿记录云端化。

/fitview 独立页原先把 2D 换装图记录写在浏览器 IndexedDB，换浏览器/换设备就看不到。
这里给登录用户提供一份服务端存储：图片落 uploads/fitview/，记录进 fitview_generations，
按 user_id 隔离，同一账号在任何设备都能读到同一条历史。
"""
import base64
import os
import re
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db
from app.db.models import FitviewGeneration, Users

router = APIRouter()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FIT_DIR = os.path.join(BASE_DIR, "uploads", "fitview")
os.makedirs(FIT_DIR, exist_ok=True)

_DATA_URL = re.compile(r"^data:image/(png|jpe?g|webp|gif);base64,")
_EXT = {"png": ".png", "jpg": ".jpg", "jpeg": ".jpg", "webp": ".webp", "gif": ".gif"}
MAX_IMG_BYTES = 12 * 1024 * 1024
MAX_VIEWS = 4


class ViewIn(BaseModel):
    outfit_name: str = ""
    outfit_id: str = ""
    views: list[str] = []
    triangles: int = 0
    tryon_only: int = 1


def _store_image(src: str, month: str) -> str:
    """dataURL 落盘为静态文件并返回相对 URL；已是 http(s) 地址的直接保留。"""
    if not src:
        return ""
    if not src.startswith("data:"):
        return src if src.startswith(("http://", "https://", "/")) else ""
    m = _DATA_URL.match(src)
    if not m:
        raise HTTPException(400, "换装图格式不支持")
    raw = src[m.end():]
    try:
        data = base64.b64decode(raw, validate=False)
    except Exception:
        raise HTTPException(400, "换装图 base64 解析失败")
    if not data:
        raise HTTPException(400, "换装图内容为空")
    if len(data) > MAX_IMG_BYTES:
        raise HTTPException(400, "单张换装图超过 12MB")
    day_dir = os.path.join(FIT_DIR, month)
    os.makedirs(day_dir, exist_ok=True)
    kind = m.group(1).lower()
    kind = "jpg" if kind == "jpeg" else kind
    fname = f"{uuid.uuid4().hex}{_EXT.get(kind, '.png')}"
    with open(os.path.join(day_dir, fname), "wb") as f:
        f.write(data)
    return f"/uploads/fitview/{month}/{fname}"


def _row(g: FitviewGeneration) -> dict:
    return {
        "id": g.id,
        "outfitId": g.outfit_id or "",
        "outfitName": g.outfit_name or "2D 换装",
        "views": g.views or [],
        "triangles": g.triangles or 0,
        "tryonOnly": bool(g.tryon_only),
        "createdAt": int(g.created_at.timestamp() * 1000) if g.created_at else 0,
        "cloud": True,
    }


@router.post("")
def save_generation(body: ViewIn, db: Session = Depends(get_db),
                    user: Users = Depends(get_current_user)):
    """保存一次试穿产出（2D 换装三视图 或 3D 模型），返回云端记录。"""
    if not body.views:
        raise HTTPException(400, "缺少换装图")
    month = datetime.now().strftime("%Y%m")
    urls = [_store_image(v, month) for v in body.views[:MAX_VIEWS]]
    urls = [u for u in urls if u]
    if not urls:
        raise HTTPException(400, "换装图保存失败")

    row = FitviewGeneration(
        user_id=user.id,
        outfit_id=(body.outfit_id or "")[:64],
        outfit_name=(body.outfit_name or "2D 换装")[:128],
        views=urls,
        triangles=max(0, int(body.triangles or 0)),
        tryon_only=1 if body.tryon_only else 0,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return {"item": _row(row)}


@router.get("")
def list_generations(limit: int = 60, db: Session = Depends(get_db),
                     user: Users = Depends(get_current_user)):
    """当前账号的全部试穿记录，新的在前。"""
    q = (db.query(FitviewGeneration)
         .filter(FitviewGeneration.user_id == user.id)
         .order_by(FitviewGeneration.created_at.desc(), FitviewGeneration.id.desc())
         .limit(max(1, min(limit, 200)))
         .all())
    return {"items": [_row(g) for g in q], "total": len(q)}


@router.delete("/{gid}")
def delete_generation(gid: int, db: Session = Depends(get_db),
                      user: Users = Depends(get_current_user)):
    """删除自己的一条记录（文件保留在 uploads，便于排查）。"""
    row = (db.query(FitviewGeneration)
           .filter(FitviewGeneration.id == gid, FitviewGeneration.user_id == user.id)
           .first())
    if not row:
        raise HTTPException(404, "记录不存在")
    db.delete(row)
    db.commit()
    return {"ok": True}
