# -*- coding: utf-8 -*-
"""演示模式全接口冒烟测试（python _smoke_demo.py）"""
import json, sys, io, time
import requests

BASE = "http://127.0.0.1:8765"
out = io.open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

def check(name, fn):
    try:
        r = fn()
        out.write(f"[OK] {name}: {json.dumps(r, ensure_ascii=False)[:130]}\n")
    except Exception as e:
        out.write(f"[FAIL] {name}: {e}\n")

# 登录拿到 token（模块8）
tok = requests.post(f"{BASE}/api/user/login",
                    json={"username": "admin", "password": "yisu2026"}, timeout=8).json()["token"]
H = {"Authorization": f"Bearer {tok}"}

# 模块1 首页
check("news", lambda: requests.get(f"{BASE}/api/home/news", params={"page":1,"page_size":3}, timeout=8).json()["items"][0]["title"])
check("hot-tags", lambda: requests.get(f"{BASE}/api/home/hot-tags", timeout=8).json()["tags"][0]["name"])
check("news-parse", lambda: requests.post(f"{BASE}/api/home/news/parse", json={"title":"马王堆素纱单衣数字化","content":"湖南博物院以AI数字孪生复原西汉丝袍，展现马王堆丝织文物之美。"}, timeout=8).json()["entity_tags"])
# 模块2 档案+对话
check("costumes", lambda: requests.get(f"{BASE}/api/archive/costumes", params={"page":1,"page_size":5}, timeout=8).json()["items"][0]["name"])
check("costume-detail", lambda: requests.get(f"{BASE}/api/archive/costumes/7", timeout=8).json()["name"])
check("chat", lambda: requests.post(f"{BASE}/api/archive/chat", json={"costume_id":7,"message":"你穿在身上是什么感觉？"}, timeout=8).json()["answer"][:60])
check("ask", lambda: requests.post(f"{BASE}/api/archive/ask", json={"costume_id":None,"message":"马面裙有什么形制特点？"}, timeout=8).json()["answer"][:60])
# 模块3 时间轴
check("timeline", lambda: requests.get(f"{BASE}/api/timeline/timeline", timeout=8).json()["stages"][0]["dynasty"])
# 模块4 地图
check("relics", lambda: requests.get(f"{BASE}/api/geomap/relics", timeout=8).json()["items"][0]["name"])
check("geo-stats", lambda: requests.get(f"{BASE}/api/geomap/geo-stats", timeout=8).json()["by_dynasty"][0]["name"])
# 模块5 工坊
check("templates", lambda: requests.get(f"{BASE}/api/workshop/templates", timeout=8).json()["items"][0]["name"])
check("validate", lambda: requests.post(f"{BASE}/api/workshop/validate", json={"dynasty":"宋","params":{"len":80,"sleeve":70,"waist":40,"collar":50}}, timeout=8).json()["passed"])
# 模块6 问答（带 token）
check("create-question", lambda: requests.post(f"{BASE}/api/aiqa/questions", json={"title":"明代马面裙与清代旗装的裙式差异？","content":"求问形制与工艺差异","dynasty_tags":"明,清"}, headers=H, timeout=8).json()["ai_answer"][:60])
check("questions", lambda: requests.get(f"{BASE}/api/aiqa/questions", timeout=8).json()["items"][0]["title"])
# 模块7 社区
check("boards", lambda: requests.get(f"{BASE}/api/community/boards", timeout=8).json()["items"][0]["name"])
check("posts", lambda: requests.get(f"{BASE}/api/community/posts", timeout=8).json()["items"][0]["title"])
# 模块8 用户
uname = "test" + str(int(time.time() * 1000))
check("register", lambda: requests.post(f"{BASE}/api/user/register", json={"username":uname,"password":"test1234","email":f"{uname}@yisu.ai"}, timeout=8).json()["username"])
check("login", lambda: tok[:20])
# 模块9 传承
check("heritage-profile", lambda: requests.get(f"{BASE}/api/heritage/profile", headers=H, timeout=8).json().get("total_interactions", 0))
# 模拟器
check("simulate", lambda: requests.post(f"{BASE}/api/simulator/simulate", json={"era":"song","params":{"ritual":70,"craft":55,"climate":40,"aesthetic":60,"exchange":45}}, timeout=8).json()["narrative"][:50])
out.write("SMOKE DONE\n")
