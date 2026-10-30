"""模块7 · 国风文化共治社区（点赞/收藏/转发/二级嵌套回复 + 防刷）"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.ratelimit import check_rate_limit
from app.core.security import get_current_user, get_optional_user
from app.db.database import get_db
from app.db.models import (
    Users, ForumBoards, ForumPosts, ForumReplies,
    Likes, Collections, Reposts, RevivalWorks,
)

router = APIRouter()


class PostCreate(BaseModel):
    board_id: int | None = None  # 不传则按内容自动分类
    title: str
    content: str
    image_url: str = ""
    dynasty_tags: str = ""
    costume_ids: str = ""
    work_id: int | None = None


class ReplyCreate(BaseModel):
    content: str
    parent_reply_id: int | None = None


class RepostCreate(BaseModel):
    comment: str = ""


# 帖子自动分类规则：按顺序匹配关键词，命中即归入对应板块
BOARD_RULES = [
    ("形制溯源", ["形制", "深衣", "曲裾", "直裾", "褙子", "大袖衫", "交领", "右衽", "左衽",
                  "领型", "袖型", "马王堆", "款式", "剪裁", "衣制", "服制", "袍服", "衫子",
                  "襦裙", "冕服", "补服", "道袍", "直裰", "盔甲", "打褶"]),
    ("复原作品", ["复原", "复刻", "成衣", "打版", "版型", "裁制", "试穿", "缝制", "制作教程",
                  "制作过程", "3d", "三维", "复原作品"]),
    ("纹样文创", ["纹样", "刺绣", "图案", "花纹", "织锦", "云纹", "龙纹", "凤纹", "十二章",
                  "花鸟", "吉祥", "文创", "周边", "印花", "妆花", "补子", "肚兜", "荷包"]),
    ("保护行动", ["保护", "非遗", "传承", "修复", "文保", "守护", "抢救", "申遗", "行动"]),
    ("史料求助", ["史料", "文献", "古籍", "舆服志", "考证", "请教", "求助", "求教", "出处",
                  "记载", "来源", "依据", "求证", "区别", "如何分辨", "怎么区分", "是什么"]),
]


def auto_board_id(db: Session, title: str, content: str, tags: str) -> int:
    """根据标题/内容/标签自动匹配社区板块，返回板块 id。"""
    text = f"{title or ''} {content or ''} {tags or ''}".lower()
    for name, kws in BOARD_RULES:
        if any(k.lower() in text for k in kws):
            b = db.query(ForumBoards).filter(ForumBoards.name == name).first()
            if b:
                return b.id
    b = db.query(ForumBoards).first()
    return b.id if b else 1


@router.get("/boards")
def boards(db: Session = Depends(get_db)):
    items = db.query(ForumBoards).all()
    return {"items": [{"id": b.id, "name": b.name, "description": b.description,
                       "post_count": b.post_count} for b in items]}


@router.get("/posts")
def post_list(
    board_id: int | None = None,
    page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
    keyword: str | None = None,
    status: str | None = None,  # 管理员传 pending 看待审
    db: Session = Depends(get_db),
    user: Users | None = Depends(get_optional_user),
):
    q = db.query(ForumPosts)
    if board_id:
        q = q.filter(ForumPosts.board_id == board_id)
    if keyword:
        q = q.filter(ForumPosts.title.like(f"%{keyword}%"))
    is_admin = bool(user and getattr(user, "role", "") in ("admin", "superadmin"))
    if is_admin and status:
        q = q.filter(ForumPosts.status == status)
    else:
        # 普通用户：只看已审核通过的；管理员不指定 status 时看全部
        if not is_admin:
            q = q.filter(ForumPosts.status == "approved")
    total = q.count()
    items = q.order_by(ForumPosts.is_pinned.desc(), ForumPosts.create_time.desc()) \
             .offset((page - 1) * page_size).limit(page_size).all()
    return {"total": total, "page": page, "items": [{
        "id": p.id, "board_id": p.board_id, "title": p.title,
        "content": (p.content or "")[:160], "image_url": p.image_url,
        "author": p.author.username,
        "author_id": p.author.id, "dynasty_tags": p.dynasty_tags,
        "work_id": p.work_id, "is_pinned": p.is_pinned, "status": p.status,
        "like_count": p.like_count, "collect_count": p.collect_count,
        "repost_count": p.repost_count, "reply_count": p.reply_count,
        "create_time": p.create_time.isoformat() if p.create_time else None,
    } for p in items]}


@router.get("/posts/{post_id}")
def post_detail(post_id: int, db: Session = Depends(get_db),
                user: Users | None = Depends(get_optional_user)):
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    # 未审核帖子：仅作者本人或管理员可见
    if p.status != "approved":
        is_admin = bool(user and getattr(user, "role", "") in ("admin", "superadmin"))
        if not (is_admin or (user and p.user_id == user.id)):
            raise HTTPException(403, "该帖子正在审核中，暂不可见")
    replies = db.query(ForumReplies).filter_by(post_id=post_id) \
                .order_by(ForumReplies.create_time.asc()).all()
    work = db.get(RevivalWorks, p.work_id) if p.work_id else None
    return {
        "id": p.id, "title": p.title, "content": p.content, "image_url": p.image_url,
        "author": p.author.username, "author_id": p.user_id,
        "board_name": p.board.name if p.board else "",
        "dynasty_tags": p.dynasty_tags, "is_pinned": p.is_pinned, "status": p.status,
        "like_count": p.like_count, "collect_count": p.collect_count,
        "repost_count": p.repost_count, "reply_count": p.reply_count,
        "work": {"id": work.id, "image_url": work.image_url,
                 "confidence": work.confidence} if work else None,
        "create_time": p.create_time.isoformat() if p.create_time else None,
        "replies": [{
            "id": r.id, "user_id": r.user_id,
            "username": r.author.username if r.author else f"用户#{r.user_id}",
            "content": r.content,
            "parent_reply_id": r.parent_reply_id, "like_count": r.like_count,
            "create_time": r.create_time.isoformat() if r.create_time else None,
        } for r in replies],
    }


@router.post("/posts")
def create_post(body: PostCreate, db: Session = Depends(get_db),
                user: Users = Depends(get_current_user)):
    if not check_rate_limit(f"ratelimit:{user.id}:post", limit=10, window=60):
        raise HTTPException(429, "发帖过于频繁，请稍后再试")
    board_id = body.board_id or auto_board_id(db, body.title, body.content or "", body.dynasty_tags or "")
    p = ForumPosts(
        board_id=board_id, user_id=user.id, title=body.title,
        content=body.content, image_url=body.image_url,
        dynasty_tags=body.dynasty_tags,
        costume_ids=body.costume_ids, work_id=body.work_id,
        status="approved",
    )
    db.add(p)
    board = db.get(ForumBoards, board_id)
    if board:
        board.post_count += 1
    db.commit()
    db.refresh(p)
    return {"id": p.id, "title": p.title, "board_id": board_id, "status": p.status}


@router.post("/posts/{post_id}/offline")
def offline_post(post_id: int, db: Session = Depends(get_db),
                 user: Users = Depends(get_current_user)):
    """管理员下架不合格帖子。"""
    if getattr(user, "role", "") not in ("admin", "superadmin"):
        raise HTTPException(403, "需要管理员权限")
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    p.status = "rejected"
    db.commit()
    return {"id": p.id, "status": "rejected"}


@router.post("/posts/{post_id}/online")
def online_post(post_id: int, db: Session = Depends(get_db),
                user: Users = Depends(get_current_user)):
    """管理员恢复已下架帖子。"""
    if getattr(user, "role", "") not in ("admin", "superadmin"):
        raise HTTPException(403, "需要管理员权限")
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    p.status = "approved"
    db.commit()
    return {"id": p.id, "status": "approved"}


@router.post("/posts/{post_id}/pin")
def pin_post(post_id: int, db: Session = Depends(get_db),
             user: Users = Depends(get_current_user)):
    """管理员置顶帖子。"""
    if getattr(user, "role", "") not in ("admin", "superadmin"):
        raise HTTPException(403, "需要管理员权限")
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    p.is_pinned = True
    db.commit()
    return {"id": p.id, "is_pinned": True}


@router.post("/posts/{post_id}/unpin")
def unpin_post(post_id: int, db: Session = Depends(get_db),
               user: Users = Depends(get_current_user)):
    """管理员取消置顶。"""
    if getattr(user, "role", "") not in ("admin", "superadmin"):
        raise HTTPException(403, "需要管理员权限")
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    p.is_pinned = False
    db.commit()
    return {"id": p.id, "is_pinned": False}


@router.post("/posts/{post_id}/apply-online")
def apply_online(post_id: int, db: Session = Depends(get_db),
                 user: Users = Depends(get_current_user)):
    """作者申请重新上架被下架的帖子（进入待审核状态）。"""
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    if p.user_id != user.id and getattr(user, "role", "") not in ("admin", "superadmin"):
        raise HTTPException(403, "只能申请自己的帖子")
    if p.status != "rejected":
        raise HTTPException(400, "仅被下架的帖子可申请重新上架")
    p.status = "pending"
    db.commit()
    return {"id": p.id, "status": "pending", "message": "申请已提交，请等待管理员审核"}


@router.delete("/posts/{post_id}")
def delete_post(post_id: int, db: Session = Depends(get_db),
                user: Users = Depends(get_current_user)):
    """删除自己的帖子（级联清理回复/点赞/收藏/转发，仅作者本人可删）。"""
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    if p.user_id != user.id:
        raise HTTPException(403, "只能删除自己发布的帖子")
    # 级联删除关联数据
    db.query(ForumReplies).filter_by(post_id=post_id).delete(synchronize_session=False)
    db.query(Likes).filter_by(target_type="post", target_id=post_id).delete(synchronize_session=False)
    db.query(Collections).filter_by(post_id=post_id).delete(synchronize_session=False)
    from sqlalchemy import or_
    db.query(Reposts).filter(
        or_(Reposts.original_post_id == post_id, Reposts.new_post_id == post_id)
    ).delete(synchronize_session=False)
    board = p.board
    if board:
        board.post_count = max(0, (board.post_count or 0) - 1)
    db.delete(p)
    db.commit()
    return {"deleted": True, "id": post_id}


@router.post("/posts/{post_id}/replies")
def create_reply(post_id: int, body: ReplyCreate,
                 db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    if not check_rate_limit(f"ratelimit:{user.id}:reply", limit=30, window=60):
        raise HTTPException(429, "回复过于频繁，请稍后再试")
    post = db.get(ForumPosts, post_id)
    if not post:
        raise HTTPException(404, "帖子不存在")
    r = ForumReplies(post_id=post_id, user_id=user.id, content=body.content,
                     parent_reply_id=body.parent_reply_id)
    db.add(r)
    post.reply_count = (post.reply_count or 0) + 1
    db.commit()
    db.refresh(r)
    return {"id": r.id, "content": r.content}


@router.post("/posts/{post_id}/like")
def toggle_like(post_id: int, db: Session = Depends(get_db),
                user: Users = Depends(get_current_user)):
    """点赞（UNIQUE 联合约束防重复 + Redis 限流，重复请求自动返回已取消）。"""
    if not check_rate_limit(f"ratelimit:{user.id}:like", limit=30, window=60):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    existing = db.query(Likes).filter_by(user_id=user.id, target_type="post",
                                         target_id=post_id).first()
    post = db.get(ForumPosts, post_id)
    if not post:
        raise HTTPException(404, "帖子不存在")
    if existing:
        db.delete(existing)
        post.like_count = max(0, (post.like_count or 0) - 1)
        db.commit()
        return {"liked": False, "like_count": post.like_count}
    db.add(Likes(user_id=user.id, target_type="post", target_id=post_id))
    post.like_count = (post.like_count or 0) + 1
    db.commit()
    return {"liked": True, "like_count": post.like_count}


@router.post("/posts/{post_id}/collect")
def toggle_collect(post_id: int, folder_name: str = "默认收藏",
                   db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    if not check_rate_limit(f"ratelimit:{user.id}:collect", limit=30, window=60):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    existing = db.query(Collections).filter_by(user_id=user.id, post_id=post_id).first()
    post = db.get(ForumPosts, post_id)
    if not post:
        raise HTTPException(404, "帖子不存在")
    if existing:
        db.delete(existing)
        post.collect_count = max(0, (post.collect_count or 0) - 1)
        db.commit()
        return {"collected": False, "collect_count": post.collect_count}
    db.add(Collections(user_id=user.id, post_id=post_id, folder_name=folder_name))
    post.collect_count = (post.collect_count or 0) + 1
    db.commit()
    return {"collected": True, "collect_count": post.collect_count}


@router.post("/posts/{post_id}/repost")
def repost(post_id: int, body: RepostCreate,
           db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """站内转发生成新帖引用原帖（Redis 限流 + 数据库唯一索引防刷）。"""
    if not check_rate_limit(f"ratelimit:{user.id}:repost", limit=20, window=60):
        raise HTTPException(429, "操作过于频繁，请稍后再试")
    original = db.get(ForumPosts, post_id)
    if not original:
        raise HTTPException(404, "帖子不存在")
    new_post = ForumPosts(
        board_id=original.board_id, user_id=user.id,
        title=f"转发：{original.title}", content=f"原帖：{original.title}\n\n{body.comment}",
        dynasty_tags=original.dynasty_tags, costume_ids=original.costume_ids,
    )
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    db.add(Reposts(user_id=user.id, original_post_id=post_id, new_post_id=new_post.id,
                   comment=body.comment))
    original.repost_count = (original.repost_count or 0) + 1
    db.commit()
    return {"new_post_id": new_post.id, "repost_count": original.repost_count}


@router.get("/my/interactions")
def my_interactions(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """个人互动记录（点赞/收藏/转发）。"""
    liked = db.query(Likes).filter_by(user_id=user.id).all()
    collected = db.query(Collections).filter_by(user_id=user.id).all()
    reposted = db.query(Reposts).filter_by(user_id=user.id).all()
    return {
        "liked_posts": [l.target_id for l in liked if l.target_type == "post"],
        "collected": [c.post_id for c in collected if c.post_id],
        "reposted": [r.original_post_id for r in reposted],
    }
