"""模块8 · 用户中心与权限体系（注册/登录/JWT/个人数据/管理员）"""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.security import (
    create_token, hash_password, verify_password,
    get_current_user, require_admin,
)
from app.db.database import get_db
from app.db.models import (
    Users, AiConversations, UserDraftPatterns, RevivalWorks,
    ForumPosts, Collections, Questions,
)

router = APIRouter()


class RegisterIn(BaseModel):
    username: str
    password: str
    email: str = ""


class LoginIn(BaseModel):
    username: str
    password: str


@router.post("/register")
def register(body: RegisterIn, db: Session = Depends(get_db)):
    if db.query(Users).filter_by(username=body.username).first():
        raise HTTPException(400, "用户名已存在")
    if body.email and db.query(Users).filter_by(email=body.email).first():
        raise HTTPException(400, "邮箱已被注册")
    u = Users(username=body.username, email=body.email,
              password_hash=hash_password(body.password))
    db.add(u)
    db.commit()
    db.refresh(u)
    return {"id": u.id, "username": u.username,
            "token": create_token(u.id, u.role), "role": u.role}


@router.post("/login")
def login(body: LoginIn, db: Session = Depends(get_db)):
    u = db.query(Users).filter_by(username=body.username).first()
    if not u or not verify_password(body.password, u.password_hash):
        raise HTTPException(401, "用户名或密码错误")
    return {"id": u.id, "username": u.username, "role": u.role,
            "token": create_token(u.id, u.role), "avatar": u.avatar}


@router.get("/me")
def me(user: Users = Depends(get_current_user)):
    return {"id": user.id, "username": user.username, "email": user.email,
            "role": user.role, "avatar": user.avatar,
            "create_time": user.create_time.isoformat() if user.create_time else None}


class AvatarIn(BaseModel):
    avatar: str


class UsernameIn(BaseModel):
    username: str


@router.post("/me/username")
def update_username(body: UsernameIn, db: Session = Depends(get_db),
                    user: Users = Depends(get_current_user)):
    """修改用户名（全局唯一，登录名同步变更）。"""
    name = (body.username or "").strip()
    if not name:
        raise HTTPException(400, "用户名不能为空")
    if len(name) < 2 or len(name) > 20:
        raise HTTPException(400, "用户名长度需为 2-20 个字符")
    if db.query(Users).filter(Users.username == name, Users.id != user.id).first():
        raise HTTPException(400, "该用户名已被占用")
    user.username = name
    db.commit()
    return {"id": user.id, "username": user.username}


@router.post("/me/avatar")
def update_avatar(body: AvatarIn, db: Session = Depends(get_db),
                  user: Users = Depends(get_current_user)):
    """上传头像：接受云端 URL（/uploads/... 或 http(s)://...）或 base64 dataURL（≤600KB）。"""
    avatar = (body.avatar or "").strip()
    if not avatar:
        raise HTTPException(400, "头像数据为空")
    is_url = avatar.startswith("/uploads/") or avatar.startswith("http://") or avatar.startswith("https://")
    is_data = avatar.startswith("data:image/")
    if not is_url and not is_data:
        raise HTTPException(400, "头像须为图片 URL 或 dataURL")
    if is_data and len(avatar) > 600_000:
        raise HTTPException(400, "头像文件过大，请压缩后重试（≤500KB）")
    user.avatar = avatar
    db.commit()
    return {"avatar": user.avatar}


@router.get("/me/stats")
def my_stats(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """个人中心概览统计。"""
    from app.db.models import UserCostumeLog, UserDraftPatterns, RevivalWorks, ForumPosts, Collections, Questions
    return {
        "logs": db.query(UserCostumeLog).filter_by(user_id=user.id).count(),
        "drafts": db.query(UserDraftPatterns).filter_by(user_id=user.id).count(),
        "works": db.query(RevivalWorks).filter_by(user_id=user.id).count(),
        "posts": db.query(ForumPosts).filter_by(user_id=user.id).count(),
        "collections": db.query(Collections).filter_by(user_id=user.id).count(),
        "questions": db.query(Questions).filter_by(user_id=user.id).count(),
    }


@router.get("/me/logs")
def my_logs(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    from app.db.models import UserCostumeLog, Costumes
    items = db.query(UserCostumeLog).filter_by(user_id=user.id) \
             .order_by(UserCostumeLog.create_time.desc()).limit(50).all()
    out = []
    for x in items:
        name = None
        if x.costume_id:
            c = db.get(Costumes, x.costume_id)
            name = c.name if c else None
        out.append({
            "costume_id": x.costume_id, "costume_name": name,
            "action_type": x.action_type,
            "create_time": x.create_time.isoformat() if x.create_time else None,
        })
    return {"items": out}


@router.get("/me/drafts")
def my_drafts(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    items = db.query(UserDraftPatterns).filter_by(user_id=user.id) \
             .order_by(UserDraftPatterns.update_time.desc()).all()
    return {"items": [{"id": d.id, "draft_name": d.draft_name,
                       "costume_id": d.costume_id, "preview_url": d.preview_url,
                       "update_time": d.update_time.isoformat() if d.update_time else None}
                      for d in items]}


@router.get("/me/works")
def my_works(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    items = db.query(RevivalWorks).filter_by(user_id=user.id) \
             .order_by(RevivalWorks.create_time.desc()).all()
    out = []
    for w in items:
        name = None
        if w.costume_id:
            c = db.get(Costumes, w.costume_id)
            name = c.name if c else None
        out.append({"id": w.id, "costume_id": w.costume_id, "costume_name": name,
                    "image_url": w.image_url, "confidence": w.confidence,
                    "is_public": w.is_public,
                    "create_time": w.create_time.isoformat() if w.create_time else None})
    return {"items": out}


@router.get("/me/posts")
def my_posts(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    items = db.query(ForumPosts).filter_by(user_id=user.id) \
             .order_by(ForumPosts.create_time.desc()).all()
    return {"items": [{"id": p.id, "title": p.title, "like_count": p.like_count,
                       "reply_count": p.reply_count, "dynasty_tags": p.dynasty_tags,
                       "board_name": p.board.name if p.board else "",
                       "create_time": p.create_time.isoformat() if p.create_time else None}
                      for p in items]}


@router.get("/me/collections")
def my_collections(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    items = db.query(Collections).filter_by(user_id=user.id).all()
    out = []
    for c in items:
        post = db.get(ForumPosts, c.post_id) if c.post_id else None
        out.append({"post_id": c.post_id, "costume_id": c.costume_id,
                    "work_id": c.work_id, "folder_name": c.folder_name,
                    "post_title": post.title if post else None,
                    "post_time": post.create_time.isoformat() if post and post.create_time else None})
    return {"items": out}


@router.get("/me/questions")
def my_questions(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    items = db.query(Questions).filter_by(user_id=user.id) \
             .order_by(Questions.create_time.desc()).all()
    return {"items": [{"id": q.id, "title": q.title, "create_time": q.create_time.isoformat()
                       if q.create_time else None} for q in items]}


# ===== 管理员接口 =====

@router.get("/admin/users")
def admin_users(db: Session = Depends(get_db), _: Users = Depends(require_admin)):
    items = db.query(Users).all()
    return {"items": [{"id": u.id, "username": u.username, "role": u.role,
                       "email": u.email} for u in items]}


@router.post("/admin/users/{user_id}/role")
def admin_set_role(user_id: int, role: str,
                   db: Session = Depends(get_db), admin: Users = Depends(require_admin)):
    u = db.get(Users, user_id)
    if not u:
        raise HTTPException(404, "用户不存在")
    # 保护：superadmin 不能被降级或改角色
    if u.role == "superadmin":
        raise HTTPException(403, "总管账号受保护，不可修改")
    # 只有 superadmin 才能提升 admin；普通 admin 只能管理普通用户
    if role == "admin" and u.role != "admin" and admin.role != "superadmin":
        raise HTTPException(403, "只有总管才能任命管理员")
    u.role = "admin" if role == "admin" else "user"
    db.commit()
    return {"id": u.id, "role": u.role}


@router.get("/admin/audit/posts")
def admin_audit_posts(db: Session = Depends(get_db), _: Users = Depends(require_admin)):
    items = db.query(ForumPosts).order_by(ForumPosts.create_time.desc()).limit(100).all()
    return {"items": [{"id": p.id, "title": p.title, "author": p.author.username,
                       "content": (p.content or "")[:100]} for p in items]}


@router.post("/admin/audit/posts/{post_id}/delete")
def admin_delete_post(post_id: int, db: Session = Depends(get_db),
                      _: Users = Depends(require_admin)):
    """管理员删除违规帖子（级联清理回复/点赞/收藏/转发记录）。"""
    from app.db.models import ForumReplies, Likes, Collections, Reposts
    p = db.get(ForumPosts, post_id)
    if not p:
        raise HTTPException(404, "帖子不存在")
    db.query(ForumReplies).filter_by(post_id=post_id).delete()
    db.query(Likes).filter_by(target_type="post", target_id=post_id).delete()
    db.query(Collections).filter_by(post_id=post_id).delete()
    db.query(Reposts).filter_by(original_post_id=post_id).delete()
    db.query(Reposts).filter_by(new_post_id=post_id).delete()
    board = p.board
    if board:
        board.post_count = max(0, (board.post_count or 0) - 1)
    db.delete(p)
    db.commit()
    return {"deleted": post_id}
