"""Celery 异步任务：AI 图生成 / 视频生成 / 资讯抓取解析"""
from __future__ import annotations

from celery import Celery

from app.core.config import settings
from app.ai_engine.ner_news_parse import run_news_pipeline
from app.ai_engine.multi_modal_revive import generate_revival_image

celery_app = Celery(
    "yisu_ai",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)
celery_app.conf.update(task_serializer="json", result_serializer="json",
                       accept_content=["json"], timezone="Asia/Shanghai")


@celery_app.task(name="render_revival_image")
def task_render_revival_image(costume: dict, params: dict, reference_url: str | None = None) -> dict:
    """异步渲染复原图（避免接口超时）。"""
    return generate_revival_image(costume, params, reference_url)


@celery_app.task(name="parse_news")
def task_parse_news(title: str, content: str) -> dict:
    """异步资讯解析。"""
    return run_news_pipeline(title, content)


@celery_app.task(name="fetch_rss_news")
def task_fetch_rss_news(rss_url: str) -> list[dict]:
    """RSS 抓取（feedparser）。"""
    try:
        import feedparser
        feed = feedparser.parse(rss_url)
        items = []
        for entry in feed.entries[:20]:
            items.append({
                "title": entry.get("title", ""),
                "content": entry.get("summary", entry.get("description", "")),
                "source_url": entry.get("link", ""),
                "publish_time": entry.get("published", ""),
            })
        return items
    except Exception as exc:
        return [{"error": str(exc)}]
