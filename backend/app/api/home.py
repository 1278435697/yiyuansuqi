"""模块1 · 文博资讯溯源首页"""
import json

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai_engine.archive_codes import code_of
from app.ai_engine.ner_news_parse import run_news_pipeline
from app.ai_engine.news_fetcher import dress_match
from app.db.database import get_db
from app.db.models import News, Costumes, Patterns, Relics, ForumPosts, Users
from app.core.security import get_current_user

router = APIRouter()


@router.post("/news/fetch")
def fetch_news_now(db: Session = Depends(get_db), user: Users = Depends(get_current_user)):
    """手动触发文博资讯实时抓取（管理员）。抓故宫博物院官网最新资讯/公告入库。"""
    if user.role != "admin":
        from fastapi import HTTPException
        raise HTTPException(403, "仅管理员可手动刷新资讯")
    from app.ai_engine.news_fetcher import run as news_fetch_run
    code = news_fetch_run()
    return {"ok": code == 0, "detail": "资讯已刷新" if code == 0 else "抓取失败，请查看后端日志"}


@router.get("/stats")
def home_stats(db: Session = Depends(get_db)):
    """首页数据概览：档案 / 纹样 / 出土文物 / 社区帖 数量。"""
    return {
        "costumes": db.query(Costumes).count(),
        "patterns": db.query(Patterns).count(),
        "relics": db.query(Relics).count(),
        "posts": db.query(ForumPosts).count(),
    }


def _ai_qs(raw: str) -> list:
    if not raw:
        return []
    try:
        v = json.loads(raw)
        return v if isinstance(v, list) else [raw]
    except Exception:
        return [raw]


class NewsParseIn(BaseModel):
    title: str
    content: str


@router.get("/news")
def news_list(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    dynasty: str | None = None,
    keyword: str | None = None,
    days: int | None = Query(None, ge=1, le=400),
    db: Session = Depends(get_db),
):
    def _dress_ok(n: News) -> bool:
        # 丝绸博物馆主题天然匹配；其他来源必须命中服饰主题判定
        if n.source == "中国丝绸博物馆":
            return True
        return dress_match((n.title or "") + (n.summary or ""))

    q = db.query(News)
    if dynasty:
        q = q.filter(News.dynasty_tags.like(f"%{dynasty}%"))
    if keyword:
        q = q.filter(News.title.like(f"%{keyword}%"))
    if days:
        from datetime import datetime, timedelta
        q = q.filter(News.publish_time >= datetime.now() - timedelta(days=days))
    # 取最新 400 条统一过服饰过滤，total 为过滤后真实数量（避免翻页到底却空页）
    all_rows = q.order_by(desc(News.publish_time)).limit(400).all()
    dress_rows = [n for n in all_rows if _dress_ok(n)]
    total = len(dress_rows)
    items = dress_rows[(page - 1) * page_size: page * page_size]
    # 今日焦点：独立于分页，固定返回最新 3 条焦点资讯（同样过服饰过滤）
    focus = db.query(News).filter(News.is_focus.is_(True)) \
             .order_by(desc(News.publish_time)).limit(6).all()
    focus = [n for n in focus if _dress_ok(n)][:3]
    return {
        "total": total, "page": page, "page_size": page_size,
        "focus": [{
            "id": n.id, "title": n.title, "summary": n.summary, "source": n.source,
            "source_url": n.source_url, "dynasty_tags": n.dynasty_tags.split(",") if n.dynasty_tags else [],
            "entity_tags": n.entity_tags.split(",") if n.entity_tags else [],
            "ai_questions": _ai_qs(n.ai_questions),
            "cover_image": n.cover_image or "",
            "is_focus": n.is_focus, "publish_time": n.publish_time.isoformat() if n.publish_time else None,
        } for n in focus],
        "items": [{
            "id": n.id, "title": n.title, "summary": n.summary, "source": n.source,
            "source_url": n.source_url, "dynasty_tags": n.dynasty_tags.split(",") if n.dynasty_tags else [],
            "entity_tags": n.entity_tags.split(",") if n.entity_tags else [],
            "ai_questions": _ai_qs(n.ai_questions),
            "cover_image": n.cover_image or "",
            "is_focus": n.is_focus, "publish_time": n.publish_time.isoformat() if n.publish_time else None,
        } for n in items],
    }


@router.get("/news/{news_id}")
def news_detail(news_id: int, db: Session = Depends(get_db)):
    n = db.get(News, news_id)
    if not n:
        return {"error": "资讯不存在"}
    return {
        "id": n.id, "code": code_of("news", n.id),
        "title": n.title, "summary": n.summary, "content": n.content,
        "source": n.source, "source_url": n.source_url,
        "dynasty_tags": n.dynasty_tags.split(",") if n.dynasty_tags else [],
        "entity_tags": n.entity_tags.split(",") if n.entity_tags else [],
        "costume_ids": [int(x) for x in n.costume_ids.split(",") if x] if n.costume_ids else [],
        "cover_image": n.cover_image or "",
        "ai_questions": _ai_qs(n.ai_questions),
        "publish_time": n.publish_time.isoformat() if n.publish_time else None,
    }


@router.get("/hot-tags")
def hot_tags(db: Session = Depends(get_db)):
    """热门朝代标签云（统计资讯朝代标签出现频次）。"""
    from collections import Counter
    counter: Counter = Counter()
    for n in db.query(News).all():
        for tag in (n.dynasty_tags or "").split(","):
            if tag:
                counter[tag] += 1
    return {"tags": [{"name": k, "count": v} for k, v in counter.most_common(12)]}


@router.get("/trend-keywords")
def trend_keywords(db: Session = Depends(get_db)):
    """本周关键词趋势（演示：按朝代分布生成序列）。"""
    dynasties = ["秦汉", "隋唐", "宋", "明", "清"]
    data = []
    for d in dynasties:
        cnt = db.query(News).filter(News.dynasty_tags.like(f"%{d}%")).count()
        data.append({"name": d, "value": cnt})
    return {"data": data}


@router.post("/news/parse")
def parse_news(body: NewsParseIn):
    """手工录入资讯并触发 AI 解析（演示入口）。"""
    return run_news_pipeline(body.title, body.content)


@router.get("/costume-links")
def costume_links(db: Session = Depends(get_db)):
    """首页侧边栏推荐档案。"""
    items = db.query(Costumes).order_by(Costumes.id).limit(8).all()
    return {"items": [{"id": c.id, "name": c.name, "dynasty": c.dynasty,
                       "category": c.category, "description": (c.description or "")[:60]} for c in items]}


# ---------------------------------------------------------------- 全网搜索
from app.api.websearch import web_search as _bing_web_search


@router.get("/news-search")
def web_search(keyword: str = Query(..., min_length=1, max_length=80), limit: int = Query(8, ge=1, le=12)):
    """全网资讯搜索：Bing 实时网页检索（免 Key），支持任意关键词。"""
    kw = keyword.strip()
    if not kw:
        return {"keyword": kw, "total": 0, "items": [], "note": "关键词不能为空"}
    try:
        results = _bing_web_search(kw, limit)
        items = [{
            "title": r["title"],
            "url": r["url"],
            "source": r["source"],
            "snippet": r.get("snippet", ""),
        } for r in results]
        return {"keyword": kw, "total": len(items), "items": items,
                "note": "全网搜索（Bing 实时检索），结果仅供参考"}
    except Exception as e:
        return {"keyword": kw, "total": 0, "items": [],
                "note": f"全网搜索暂不可用（{type(e).__name__}），可稍后重试"}
