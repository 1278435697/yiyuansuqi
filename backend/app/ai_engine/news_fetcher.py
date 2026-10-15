# -*- coding: utf-8 -*-
"""
衣溯AI · 文博资讯实时抓取器（服饰主题版）
数据源（权威文博官网，聚焦传统服饰/纺织/丝路文化）：
  1) 中国丝绸博物馆 https://www.chinasilkmuseum.com/cs/list_164.aspx
     —— 国家一级博物馆，丝绸/服饰/织造主题，列表页自带标题+日期+缩略图
  2) 故宫博物院 https://www.dpm.org.cn/（首页+动态页，仅保留服饰相关资讯）

用法：
  python news_fetcher.py            # 正式运行：抓取并写入数据库
  python news_fetcher.py --dry-run  # 只抓取打印，不写库
"""
import re
import sys
import datetime
import urllib.request

# ---------- 数据源 ----------
SILK_LIST = "https://www.chinasilkmuseum.com/cs/list_164.aspx"
SILK_BASE = "https://www.chinasilkmuseum.com"
GUGONG_HOME = "https://www.dpm.org.cn/"
GUGONG_DYNAMIC = "https://www.dpm.org.cn/about/dynamic.html"
GUGONG_BASE = "https://www.dpm.org.cn"

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36"
MAX_NEW = 80          # 每轮最多入库条数
FOCUS_KEEP = 3        # 每轮最新 N 条设为「今日焦点」
HALF_YEAR = datetime.timedelta(days=183)  # 近半年过滤：只保留近半年新闻
RUN_WEB = False       # 权威源策略：全网搜索不再作为日常更新来源，仅丝博/故宫等权威源有新增才更新

# 全网服饰新闻补源关键词组（Bing 近半年检索；主题=服饰+饰品+面料）
WEB_DRESS_QUERIES = (
    "传统服饰 展览", "汉服 文物 考古", "出土 服饰 考古", "丝绸 考古 发现",
    "刺绣 非遗 展览", "织锦 展览", "马面裙 文物", "古代服饰 复原",
    "中国丝绸博物馆 展览", "丝绸之路 服饰 展览", "云锦 展览",
    "缂丝 文物", "民族服饰 展", "服饰 文物 出土", "纺织品 文物保护",
    "唐代 服饰 文物", "明代 服饰 展览", "龙袍 展览", "苏绣 展览",
    "蜀锦 服饰", "旗袍 展览 博物馆", "服饰文化 展", "织绣 展览",
    "衣冠 文物 展览", "汉服 文化 活动",
    # 饰品 / 佩饰
    "古代首饰 文物 出土", "发簪 文物 博物馆", "玉佩 考古 出土",
    "金饰 古代 出土", "步摇 文物", "荷包 刺绣 文物", "香囊 古代 文物",
    "首饰 博物馆 展览", "佩饰 考古 出土", "凤冠霞帔 文物", "珠饰 考古",
    "银簪 银钗 文物", "古代 佩玉 展览",
    # 面料 / 织染
    "香云纱 非遗", "宋锦 展览", "蓝印花布 非遗", "扎染 蜡染 非遗",
    "蜀锦 织造", "妆花缎 文物", "织金锦 展览", "提花织物 考古",
)

# 纯公告类标题关键词（无信息量）
BAN_WORDS = (
    "公告", "声明", "暂停", "延期", "闭馆", "施工",
    "停止开放", "恢复开放", "开放时间", "招聘", "须知",
    "中标", "招标", "成交",
)

# ---------- 服饰/饰品/面料主题判定 ----------
# 强词：双字服饰词 / 短语，命中任意一个即视为主题相关（如"服饰""圆领袍""马面裙""玉佩"）
STRONG_WORDS = (
    "汉服", "深衣", "襦裙", "马面裙", "补子", "妆花", "云锦", "刺绣",
    "旗袍", "唐装", "龙袍", "凤冠", "朝服", "礼服", "素纱", "衣冠",
    "服饰", "衣橱", "织造", "织锦", "丝绸", "丝路", "纺织", "缂丝",
    "衣裳", "服饰文化", "传统服饰", "民族服饰", "服饰复原", "服装",
    "织机", "织绣", "绣品", "绣花", "衣料", "布料", "织物", "面料",
    "印染", "染织", "提花", "织金", "织染", "绫罗", "锦缎", "服饰研究",
    "圆领袍", "直裾", "曲裾", "对襟", "交领", "右衽", "襕衫", "褙子",
    "袄裙", "织锦", "百子衣", "出土服饰", "服饰文物", "纺织品文物",
    # 饰品 / 佩饰
    "首饰", "头饰", "佩饰", "饰品", "饰物", "发簪", "簪钗", "步摇",
    "玉佩", "佩玉", "玉饰", "金饰", "银饰", "冠饰", "带钩", "璎珞",
    "耳坠", "耳环", "项饰", "项链", "串饰", "荷包", "香囊", "妆饰",
    "珠饰", "挂饰", "腰佩", "玉带", "佩带", "佩件", "臂钏", "玉镯",
    "金簪", "银簪", "玉簪", "金钗", "银钗", "翠钿", "花钿", "簪花",
    "点翠", "珐琅首饰", "金银首饰", "首饰盒",
    # 面料 / 织染
    "香云纱", "宋锦", "蜀锦", "妆花缎", "扎染", "蜡染", "蓝印花布",
    "织金锦", "提花缎", "织锦缎", "缂织", "纺织非遗", "织染工艺",
)
# 专属单字：基本只出现在服饰/饰品语境，命中任意一个即视为主题相关
GARMENT_CHARS = (
    "袍", "裙", "裳", "冕", "襦", "袄", "裾", "褙", "帔",
    "绦", "袂", "衫", "裤", "裈",
    "簪", "钗", "钏", "镯", "钿", "珥", "璎",
)
# 织物/丝织单字：可能误命中地名成语（罗→佛罗伦萨、锦→锦绣山河），需命中 2 个以上
FABRIC_CHARS = (
    "锦", "绢", "罗", "绫", "纱", "缎", "缂", "绒", "毡", "绸", "绣",
)


def dress_match(text: str) -> bool:
    """判定一段文本是否属于服饰主题（故宫源过滤用；丝博源天然匹配不过滤）。"""
    if not text:
        return False
    if any(w in text for w in STRONG_WORDS):
        return True
    if any(w in text for w in GARMENT_CHARS):
        return True
    return sum(w in text for w in FABRIC_CHARS) >= 2


# 兼容旧引用：DRESS_WORDS = 全部词
DRESS_WORDS = STRONG_WORDS + GARMENT_CHARS + FABRIC_CHARS


def _get(url: str, timeout: int = 15) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        raw = resp.read()
    return raw.decode("utf-8", errors="replace")


def fetch_silk_list():
    """抓中国丝绸博物馆馆内新闻列表（前8页），标题+日期+缩略图，近半年内。"""
    seen, items = set(), []
    now = datetime.datetime.now()
    for page in range(1, 9):
        url = SILK_LIST if page == 1 else f"{SILK_LIST}?page={page}"
        try:
            html = _get(url)
        except Exception:
            continue
        # 条目块：图 + 标题链接 + 日期
        for m in re.finditer(
            r'<h3[^>]*>\s*<a[^>]+href=[\'"]([^\'"]+)[\'"][^>]*>\s*([^<]{4,120})\s*</a>',
            html,
        ):
            link, title = m.group(1), re.sub(r"\s+", " ", m.group(2)).strip()
            if not re.search(r"[\u4e00-\u9fff]", title) or len(title) < 6:
                continue
            # 该链接之后的日期
            dm = re.search(r"20\d{2}-\d{2}-\d{2}", html[m.end():m.end() + 500])
            date = None
            if dm:
                try:
                    date = datetime.datetime.strptime(dm.group(0), "%Y-%m-%d")
                except Exception:
                    date = None
            # 该链接之前的缩略图（最近一个 img）
            prev = html[max(0, m.start() - 600):m.start()]
            imgm = list(re.finditer(r'<img[^>]+src="([^"]+)"', prev))
            cover = ""
            if imgm:
                src = imgm[-1].group(1)
                if src.startswith("/"):
                    cover = SILK_BASE + src
                elif src.startswith("http"):
                    cover = src
            key = title[:30] + link[:60]
            if key in seen:
                continue
            seen.add(key)
            if any(w in title for w in BAN_WORDS):
                continue
            # 近半年过滤：有日期且超过半年则跳过；无日期保留
            if date and date < now - HALF_YEAR:
                continue
            items.append({
                "title": title,
                "url": link if link.startswith("http") else SILK_BASE + link,
                "date": date,
                "cover": cover,
                "source": "中国丝绸博物馆",
            })
    return items


def fetch_gugong_list():
    """抓故宫首页+动态页，仅保留服饰相关资讯。"""
    seen, items = set(), []
    for page in (GUGONG_HOME, GUGONG_DYNAMIC):
        try:
            html = _get(page)
        except Exception:
            continue
        for m in re.finditer(
            r'<a[^>]+href="(/?(?:classify_detail)/\d+\.html)"[^>]*>(?:<[^>]+>)*([^<]{4,90})',
            html,
        ):
            href = m.group(1)
            title = re.sub(r"\s+", " ", m.group(2)).strip()
            if not re.search(r"[\u4e00-\u9fff]", title) or len(title) < 6:
                continue
            if href in seen:
                continue
            seen.add(href)
            if any(w in title for w in BAN_WORDS):
                continue
            if not dress_match(title):
                continue
            url = GUGONG_BASE + (href if href.startswith("/") else "/" + href)
            date = None
            dm = re.search(r"20\d{2}年\d{1,2}月\d{1,2}日?", html[m.end():m.end() + 400])
            if dm:
                d = re.sub(r"[年月日]", "-", dm.group(0)).rstrip("-")
                try:
                    date = datetime.datetime.strptime(d[:10], "%Y-%m-%d")
                except Exception:
                    date = None
            items.append({"title": title, "url": url, "date": date, "cover": "", "source": "故宫博物院"})
    return items


# 全网服饰新闻补源：排除百科/电商/问答/字典/游戏/品牌官网等非资讯来源
WEB_BAD_DOMAINS = (
    "baike.baidu.com", "zh.wikipedia.org", "zh.wikisource.org",
    "alibaba.com", "1688.com", "jd.com", "tmall.com", "taobao.com",
    "amazon.cn", "zhihu.com", "douban.com", "bilibili.com", "youtube.com",
    "ds.163.com", "chagushici.com", "gushici.net", "hanyuguoxue.com",
    "wenku.baidu.com", "zgbk.com", "hm.com.cn", "uniqlo.cn", "meikansocks.com",
    "sheygo.com", "zidian.gushici.net",
    # 现代珠宝/时尚品牌商城官网（非文博资讯）
    "lukfook.com", "lukfook.com.hk", "louisvuitton.com", "swarovski.com",
    "tiffany.com", "cartier.com", "chowtaifook.com", "chowsangsang.com",
    "pandora.net", "laofengxiang.com", "sixgod.com", "zhoubaofu.com",
    "chendafu.com", "周大福", "周生生",
)
WEB_BAD_TITLES = (
    "百科", "价格", "排行", "批发", "多少钱", "图片大全",
    "厂家", "供应", "采购", "报价", "怎么样",
    "怎么读", "的意思", "字典", "词典", "攻略", "副本", "拼音", "读音", "文库", "古诗",
    "官网", "官方商城", "珠宝商城", "钻石", "K金", "足金",
    # 地名/机构误命中防护
    "织金县", "织金洞", "织金人民政府", "人民政府门户", "人民政府网",
    "农场", "智慧农业", "农业", "种植", "养殖", "农机",
    "国际标准化组织", "文化遗产保护技术委员会", "ISO年会", "标准化技术委员会",
)


def fetch_web_dress():
    """全网服饰新闻补源：Bing 近半年检索 25 组服饰关键词，服饰主题过滤后入库。

    返回条目 source 为来源域名、无真实日期时 publish_time 由调用方置为当前时间。
    """
    import time as _time
    from urllib.parse import quote
    try:
        import requests
    except Exception:
        return []
    seen, items = set(), []
    now = datetime.datetime.now()
    for kw in WEB_DRESS_QUERIES:
        try:
            # qft=interval%3d"180" 限定 Bing 近半年结果
            url = (
                "https://www.bing.com/search?q=" + quote(kw) +
                "&mkt=zh-CN&setlang=zh-hans&count=8&qft=interval%3d%22180%22"
            )
            resp = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9"}, timeout=12)
            html = resp.text
        except Exception:
            _time.sleep(0.8)
            continue
        for item in re.findall(r'<li class="b_algo".*?</li>', html, re.S)[:8]:
            try:
                hm = re.search(r'<h2[^>]*><a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', item, re.S)
                if not hm:
                    continue
                href, raw_title = hm.group(1), re.sub(r"<[^>]+>", "", hm.group(2)).strip()
                title = re.sub(r"\s+", " ", raw_title)
                # 解码 Bing /ck/a 跳转
                if "/ck/a" in href:
                    m = re.search(r"[?&]u=a1([^&]+)", href)
                    if m:
                        import base64
                        try:
                            v = m.group(1) + "=" * ((4 - len(m.group(1)) % 4) % 4)
                            href = __import__("urllib.parse", fromlist=["unquote"]).unquote(
                                base64.urlsafe_b64decode(v).decode("utf-8", "ignore"))
                        except Exception:
                            pass
                if "bing.com" in href or "microsoft" in href:
                    continue
                sm = re.search(r'<p[^>]*>(.*?)</p>', item, re.S)
                snippet = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", sm.group(1))).strip() if sm else ""
                # 服饰主题过滤
                if not dress_match(title + " " + snippet):
                    continue
                if any(w in title for w in BAN_WORDS):
                    continue
                key = title[:40]
                if key in seen:
                    continue
                seen.add(key)
                # 从摘要提取日期（如 2026年8月12日 / 2026-08-12），无则 None（入库时置 now）
                date = None
                dm = re.search(r"(20\d{2}[-年]\d{1,2}(?:[-月]\d{1,2})?日?)", title + " " + snippet)
                if dm:
                    d = re.sub(r"[年月]", "-", dm.group(1)).replace("日", "").rstrip("-")
                    try:
                        date = datetime.datetime.strptime(d[:10], "%Y-%m-%d")
                    except Exception:
                        date = None
                domain = re.sub(r"^www\.", "", (href.split("/")[2] if "://" in href else href))
                if any(d in domain for d in WEB_BAD_DOMAINS):
                    continue
                if any(w in title for w in WEB_BAD_TITLES):
                    continue
                items.append({
                    "title": title[:200],
                    "url": href[:255],
                    "date": date,
                    "cover": "",
                    "source": domain[:30],
                    "snippet": snippet[:500],
                })
            except Exception:
                continue
        _time.sleep(1.0)  # 限流
    return items


def fetch_detail(url: str, title: str):
    """取详情页发布日期 + 摘要 + 首图封面 + 完整正文。失败/风控则兜底。返回 (date, summary, cover, full_body)。"""
    try:
        html = _get(url, timeout=10)
    except Exception:
        return None, title, "", ""
    # 微信风控/验证页：正文不可用，摘要兜底用标题
    if "当前环境异常" in html or "完成验证后" in html or "verify" in html[:2000].lower():
        return None, title, "", ""
    date = None
    dm = re.search(r"20\d{2}[-/年]\d{1,2}[-/月]\d{1,2}", html)
    if dm:
        d = re.sub(r"[年月]", "-", dm.group(0)).replace("/", "-")
        try:
            date = datetime.datetime.strptime(d[:10], "%Y-%m-%d")
        except Exception:
            date = None
    cover = ""
    for m in re.finditer(r'<img[^>]+src="([^"]+)"', html):
        src = m.group(1)
        if ("/Uploads/image/" in src or "uploadfiles" in src.lower()) \
                and "static" not in src and "icon" not in src:
            cover = src if src.startswith("http") else "https://www.dpm.org.cn" + src
            break
    txt = re.sub(r"<script[\s\S]*?</script>|<style[\s\S]*?</style>", "", html)
    # 正文优先用 <p> 段落（微信推文/故宫详情页正文均为 <p>）
    paras = []
    for p in re.findall(r"<p[^>]*>(.*?)</p>", txt, re.S):
        seg = re.sub(r"<[^>]+>", " ", p)
        seg = re.sub(r"\s+", " ", seg).strip()
        if len(seg) < 10:
            continue
        if re.match(
            r"^(首页|导览|展览|教育|探索|学术|文创|关于|无障碍|在线订票|交通路线|参观须知|全景故宫|我要留言|阅读原文|点赞|在看|关闭|上一页|下一页|确\s*定|更\s*多|返回|网站维护|联系方式|京ICP备|京公网安备|版权所有|网站建设).*$",
            seg,
        ):
            continue
        if re.search(r"京ICP备|京公网安备|©|网站维护|网站建设|备案号|Copyright", seg):
            continue
        paras.append(seg)
    body = " ".join(paras[:14])
    if len(body) < 12:
        # 兜底：按标题定位取文段
        txt2 = re.sub(r"<[^>]+>", " ", txt)
        txt2 = re.sub(r"\s+", " ", txt2)
        i = txt2.find(title[:12])
        body = txt2[i + len(title[:12]):] if i >= 0 else ""
        body = re.sub(r"(首页|导览|展览|教育|探索|学术|文创|关于|无障碍|在线订票|交通路线|参观须知|全景故宫|我要留言).*$", "", body)
        body = body.strip(" -|")
        body = re.sub(r"确\s*定|查\s*看\s*详\s*情|更\s*多|返回", " ", body)
        body = re.sub(r"\s+", " ", body).strip()
    full_body = " ".join(paras)
    if len(full_body) < 40:
        full_body = body
    summary = body[:500]
    if len(summary) < 12:
        summary = title
    return date, summary, cover, full_body[:4000]


def _ai_summary(title: str, source: str, date, content: str = "") -> str:
    """正文缺失或需独立摘要时，用大模型生成 200-300 字资讯简介（失败返回空串）。"""
    try:
        from app.ai_engine.llm_client import chat_completion
        body_ref = (content or "").strip()[:600]
        prompt = (
            "你是衣溯AI的文博资讯编辑。请为下面这条博物馆资讯写一段 200-300 字的简介，"
            "内容客观准确、信息充足，涵盖事件时间、地点、主承办方、展出内容中与服饰、饰品、"
            "面料、织造、丝绸、文物相关的细节，不要编造事实，不要以标题开头，直接输出简介正文。\n\n"
            f"标题：{title}\n来源：{source}\n发布时间：{date.date() if date else '未知'}"
        )
        if body_ref:
            prompt += f"\n正文摘录：{body_ref}"
        s = chat_completion([
            {"role": "system", "content": "你是严谨的文博资讯编辑，输出简洁准确的资讯简介。"},
            {"role": "user", "content": prompt},
        ], temperature=0.3, max_tokens=600)
        s = (s or "").strip()
        if not s or "服务暂不可用" in s or "无法" in s[:20] or "仅包含" in s[:40] or "请补充" in s:
            return ""
        if len(s) >= 30:
            return s[:600]
    except Exception:
        pass
    return ""


def run():
    import logging
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    silk_items = fetch_silk_list()
    gugong_items = fetch_gugong_list()
    web_items = fetch_web_dress() if RUN_WEB else []
    items = silk_items + gugong_items + web_items
    print(f"[fetch] 丝博 {len(silk_items)} + 故宫服饰 {len(gugong_items)} + 全网服饰 {len(web_items)} = {len(items)} 条")
    if "--dry-run" in sys.argv:
        for it in items[:MAX_NEW]:
            d, s, c, _ = fetch_detail(it["url"], it["title"])
            print(
                f"  - [{it['title'][:30]}] {d.date() if d else it['date'].date() if it['date'] else '?'} "
                f"| img={'Y' if (c or it['cover']) else 'N'} | {s[:35]}"
            )
        print(f"[dry-run] 共 {len(items)} 条，前 {min(MAX_NEW, len(items))} 条如上（未写库）")
        return 0

    sys.path.insert(0, "/www/wwwroot/yisu/backend")
    from app.db.database import SessionLocal
    from app.db.models import News

    db = SessionLocal()
    added = 0
    try:
        exists_titles = set(x[0] for x in db.query(News.title).all())
        exists_urls = set(x[0] for x in db.query(News.source_url).all())
        new_items = [
            it for it in items
            if it["title"] not in exists_titles and it["url"] not in exists_urls
        ][:MAX_NEW]
        # 重置故宫/丝博来源的旧「今日焦点」
        for src in ("故宫博物院", "中国丝绸博物馆"):
            db.query(News).filter(News.source == src, News.is_focus.is_(True)).update(
                {"is_focus": False}
            )
        now = datetime.datetime.now()
        # 统一近半年过滤：有真实日期且超过半年的剔除
        items = [it for it in new_items if not (it.get("date") and it["date"] < now - HALF_YEAR)]
        for it in items:
            src = it["source"]
            if it.get("snippet"):
                # 全网源：尝试抓详情页封面图与更完整摘要；失败则用搜索摘要
                try:
                    date2, summary2, cover2, full2 = fetch_detail(it["url"], it["title"])
                    if (cover2 or summary2 and len(summary2) > len(it["snippet"])):
                        date, summary, cover, full = date2 or it["date"], summary2[:500], cover2 or it["cover"], full2
                    else:
                        date, summary, cover, full = it["date"], it["snippet"][:500], it["cover"], full2 or it["snippet"][:500]
                except Exception:
                    date, summary, cover, full = it["date"], it["snippet"][:500], it["cover"], it["snippet"][:500]
            else:
                date, summary, cover, full = fetch_detail(it["url"], it["title"])
            # 正文缺失（微信链接风控等）时用 AI 生成简介
            if len(summary) < 20 or summary == it["title"]:
                ai = _ai_summary(it["title"], src, date or it["date"], full)
                if ai:
                    summary = ai
            # 摘要与正文区分：正文足量且摘要只是正文截断时，用 AI 独立生成 200-300 字摘要
            if full and len(full) > 200 and (summary == it["title"] or not summary or summary in full):
                ai = _ai_summary(it["title"], src, date or it["date"], full)
                if ai:
                    summary = ai
            n = News(
                title=it["title"][:200],
                summary=summary[:500],
                content=full[:4000],
                source=src,
                source_url=it["url"][:255],
                dynasty_tags="",
                entity_tags="",
                costume_ids="",
                ai_questions="",
                cover_image=(cover or it["cover"])[:255],
                is_focus=False,
                # 无真实发布日期的条目不设时间，避免被当作"最新"霸榜（排序时 NULL 沉底）
                publish_time=date or it["date"] or None,
            )
            db.add(n)
            added += 1
        db.commit()
        # 最新 N 条设为今日焦点（排除公告）
        from sqlalchemy import or_
        ban_conds = [~News.title.contains(w) for w in BAN_WORDS]
        fresh = (
            db.query(News)
            .filter(News.source.in_(["故宫博物院", "中国丝绸博物馆"]), *ban_conds)
            .order_by(News.publish_time.desc(), News.id.desc())
            .limit(FOCUS_KEEP)
            .all()
        )
        for f in fresh:
            f.is_focus = True
        db.commit()
        print(
            f"[db] 新增 {added} 条，最新 {len(fresh)} 条设为今日焦点："
            + ("；".join(f.title[:18] for f in fresh))
        )
    except Exception as e:
        db.rollback()
        print("[db] ERROR:", e)
        return 1
    finally:
        db.close()
    return 0


if __name__ == "__main__":
    sys.exit(run())
