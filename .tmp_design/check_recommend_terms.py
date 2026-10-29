"""离线核对：用生产四库的真实专名当词典，看推荐抽词在典型问句上会命中什么。
只读线上 API 列表，不写任何数据。
"""
import io
import json
import sys
import urllib.request

sys.path.insert(0, r"D:\yisu-ai-platform\backend")
from app.ai_engine.query_terms import dynasties_in, extract_terms  # noqa: E402

BASE = "http://47.93.14.11/api"


def get(path):
    with urllib.request.urlopen(BASE + path, timeout=30) as r:
        return json.load(r)


names = [c["name"] for c in get("/archive/costumes?page_size=50")["items"]]
names += [p["name"] for p in get("/pattern-library/items")["items"]]
names += [f["name"] for f in get("/fabrics/list")["items"]]

QUESTIONS = [
    "马面裙和百褶裙有什么区别？",
    "唐代贵妇参加宴会穿什么？",
    "宋代的褙子一般用什么面料？",
    "联珠团窠纹和云雷纹哪个更早？",
    "定陵出土的妆花缎是什么工艺？",
    "曲裾深衣怎么穿？",
    "汉服和影楼装的区别",
    "今天天气怎么样",
]

lines = [f"词典规模: {len(names)} 条（档案+纹样+面料）", ""]
for q in QUESTIONS:
    lines.append(f"问句：{q}")
    lines.append(f"  朝代 {dynasties_in(q)}")
    lines.append(f"  抽词 {extract_terms(q, names)}")
    lines.append("")
io.open(r"D:\yisu-ai-platform\.tmp_design\audit\recommend_terms.txt", "w",
        encoding="utf-8").write("\n".join(lines))
print("ok")
