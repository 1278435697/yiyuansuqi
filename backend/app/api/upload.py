"""通用图片上传：图片存服务器磁盘 uploads/，返回可访问 URL（部署到云服务器即云端存储）。"""
import os
import uuid
from datetime import datetime

from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.db.database import get_db

router = APIRouter()

# 上传根目录：backend/uploads
BASE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "uploads")
IMAGES_DIR = os.path.join(BASE_DIR, "images")
os.makedirs(IMAGES_DIR, exist_ok=True)

ALLOWED_TYPES = {"image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"}
EXT_MAP = {
    "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif",
    "image/webp": ".webp", "image/bmp": ".bmp",
}
MAX_SIZE = 8 * 1024 * 1024  # 8MB


@router.post("/image")
async def upload_image(
    request: Request,
    file: UploadFile = File(...),
    user=Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """上传图片，返回可访问 URL。目录按月分桶，文件名随机防冲突。"""
    ctype = file.content_type or ""
    if ctype not in ALLOWED_TYPES:
        raise HTTPException(400, "仅支持 JPG/PNG/GIF/WebP/BMP 图片")
    data = await file.read()
    if not data:
        raise HTTPException(400, "文件为空")
    if len(data) > MAX_SIZE:
        raise HTTPException(400, "图片超过 8MB 限制")

    month_dir = os.path.join(IMAGES_DIR, datetime.now().strftime("%Y%m"))
    os.makedirs(month_dir, exist_ok=True)
    fname = f"{uuid.uuid4().hex}{EXT_MAP.get(ctype, '.jpg')}"
    path = os.path.join(month_dir, fname)
    with open(path, "wb") as f:
        f.write(data)

    rel = f"/uploads/images/{datetime.now().strftime('%Y%m')}/{fname}"
    url = str(request.base_url).rstrip("/") + rel
    return {"url": url, "path": rel}
