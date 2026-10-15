"""全网搜索代理：档案页/首页搜索联动外部搜索（Bing 免 Key HTML 解析）
提供 GET /api/archive/web-search?q=...&n=8
"""
import re
import time
from urllib.parse import quote, unquote, urlparse

import requests
from fastapi import APIRouter, Query

router = APIRouter()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _decode_bing_url(href: str) -> str:
    """Bing 可能返回 /ck/a?...&u=<base64url> 的跳转链接，提取真实 URL。"""
    if "/ck/a" not in href:
        return href
    m = re.search(r"[?&]u=a1([^&]+)", href)
    if m:
        try:
            raw = m.group(1)
            raw += "=" * ((4 - len(raw) % 4) % 4)
            return unquote(__import__("base64").urlsafe_b64decode(raw).decode("utf-8", "ignore"))
        except Exception:
            return href
    return href


def _clean(text: str) -> str:
    text = re.sub(r"<[^>]+>", "", text or "")
    text = re.sub(r"&[a-z]+;", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _domain(url: str) -> str:
    try:
        return urlparse(url).netloc.replace("www.", "")
    except Exception:
        return ""


# 服饰主题词：结果标题/摘要命中任一主题词才视为"对口"资讯
_TOPIC_WORDS = [
    "服饰", "衣服", "衣裳", "衣冠", "穿着", "穿搭", "着装", "打扮", "妆", "头饰",
    "首饰", "裙", "袍", "衫", "裾", "袄", "襦", "冠", "帽", "帔", "披帛", "幞头",
    "鞋", "履", "面料", "布料", "织物", "织造", "刺绣", "绣", "纹样", "图案", "补子",
    "深衣", "曲裾", "直裾", "褙子", "马面裙", "袄裙", "道袍", "直裰", "朝服", "冕服",
    "龙袍", "旗袍", "旗装", "凤冠", "霞帔", "十二章", "云纹", "龙纹", "丝绸", "锦",
    "绢", "纱", "罗", "缎", "绡", "绣衣", "华服", "礼服", "常服", "便服",
]

# 朝代词：用于排序加分（不是过滤必要条件）
_DYNASTY_WORDS = [
    "先秦", "秦汉", "魏晋", "南北朝", "隋唐", "上古", "夏商",
    "春秋", "战国", "周代", "汉代", "汉朝", "唐代", "唐朝", "宋代", "宋朝",
    "元代", "元朝", "明代", "明朝", "清代", "清朝", "隋代", "隋朝",
    "汉", "唐", "宋", "元", "明", "清",
]


def _filter_relevant(query: str, results: list, n: int) -> list:
    """按服饰主题词过滤泛化结果：命中的保留并按相关性排序，泛化词条剔除。

    过滤后不足 2 条时退回原始结果，避免误杀导致空列表。"""
    if not results:
        return results
    def score(r: dict) -> int:
        text = (r["title"] + " " + r.get("snippet", "")).lower()
        s = sum(1 for w in _TOPIC_WORDS if w in text)
        if s and any(d in text for d in _DYNASTY_WORDS):
            s += 2  # 主题词+朝代词同时命中，优先
        return s
    kept = [r for r in results if score(r) > 0]
    kept.sort(key=score, reverse=True)
    if len(kept) >= 2:
        return kept[:n]
    return results


# 查询疑问/虚词：压缩查询词时剔除
_STOPWORDS = [
    "什么样", "什么", "怎么", "如何", "为什么", "有没有", "是否", "哪些", "哪个",
    "怎样", "多少", "几种", "区别", "差异", "之间", "是不是", "可否",
    "吗", "呢", "吧", "啊", "呀", "的", "了", "是", "与", "和", "在", "中",
    "上", "下", "着", "过", "请", "问", "一下", "一个", "这个", "那个",
    "它", "叫", "是叫", "被", "把", "用", "穿", "日常",
]


def _smart_query(query: str) -> str:
    """把口语长句压缩成 Bing 友好的短语：朝代+服饰主题词组合。

    例：'唐代女子日常穿什么服饰？' -> '唐代 服饰'
        '它为什么叫响云纱？'        -> '响云纱'
    仅在内部用于搜索请求，页面仍展示用户原文关键词。"""
    s = query
    for w in _STOPWORDS:
        s = s.replace(w, " ")
    parts = [p for p in re.split(r"[\s,，。？！!?、；;:：·\"'“”‘’【】\[\]]+", s) if len(p) >= 2]
    text = "".join(parts)
    if not text:
        return query
    dynasty = next((d for d in sorted(_DYNASTY_WORDS, key=len, reverse=True) if d in text), None)
    topic = next((t for t in _TOPIC_WORDS if t in text), None)
    if dynasty and topic:
        return f"{dynasty} {topic}"
    if topic:
        for p in sorted(parts, key=len, reverse=True):
            if topic in p:
                return p
        return topic
    if dynasty:
        return dynasty
    return " ".join(parts[:3])


def web_search(query: str, n: int = 8) -> list:
    """调用 Bing 网页搜索并解析结构化结果（智能压缩查询 + 相关性过滤）。"""
    smart = _smart_query(query)
    url = f"https://www.bing.com/search?q={quote(smart)}&mkt=zh-CN&setlang=zh-hans&count={n}"
    resp = requests.get(url, headers=HEADERS, timeout=12)
    resp.raise_for_status()
    html = resp.text
    results = []
    for item in re.findall(r'<li class="b_algo".*?</li>', html, re.S)[:n]:
        try:
            hm = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', item, re.S)
            if not hm:
                continue
            link = _decode_bing_url(hm.group(1))
            title = _clean(hm.group(2))
            if not title or not link.startswith("http"):
                continue
            sm = re.search(r'<p[^>]*>(.*?)</p>', item, re.S)
            snippet = _clean(sm.group(1)) if sm else ""
            dm = re.search(r'class="b_attribution"[^>]*>(.*?)<', item, re.S)
            source = _clean(dm.group(1)) if dm else _domain(link)
            # 去掉搜索引擎自身/空结果
            if "bing.com" in link or "microsoft" in link:
                continue
            results.append({
                "title": title,
                "url": link,
                "source": source or _domain(link),
                "snippet": snippet[:180],
            })
        except Exception:
            continue
    return _filter_relevant(query, results, n)


@router.get("/web-search")
def web_search_api(
    q: str = Query(..., min_length=1, max_length=80, description="搜索关键词"),
    n: int = Query(8, ge=1, le=12),
):
    if not q.strip():
        return {"query": q, "results": [], "error": "关键词不能为空"}
    try:
        results = web_search(q.strip(), n)
        time.sleep(0.3)  # 基础限流
        return {"query": q.strip(), "total": len(results), "results": results, "error": ""}
    except Exception as e:  # 网络不可达/超时等：返回空并给提示，不打断站内检索
        return {"query": q.strip(), "total": 0, "results": [], "error": f"全网搜索暂不可用（{type(e).__name__}），可稍后重试"}
