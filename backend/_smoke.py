# -*- coding: utf-8 -*-
"""后端接口冒烟测试"""
import json, sys, io
import requests

BASE = "http://127.0.0.1:8001"
out = io.open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)

def check(name, fn):
    try:
        r = fn()
        out.write(f"[OK] {name}: {json.dumps(r, ensure_ascii=False)[:120]}\n")
    except Exception as e:
        out.write(f"[FAIL] {name}: {e}\n")

check("health", lambda: requests.get(f"{BASE}/health", timeout=8).json())
check("news", lambda: requests.get(f"{BASE}/api/home/news", params={"page":1,"page_size":2}, timeout=8).json()["items"][0]["title"])
check("eras", lambda: requests.get(f"{BASE}/api/simulator/eras", timeout=8).json()["items"][0]["name"])
check("templates", lambda: requests.get(f"{BASE}/api/workshop/templates", timeout=8).json()["items"][0]["name"])
check("timeline", lambda: requests.get(f"{BASE}/api/timeline", timeout=8).json()["items"][0]["era"])
check("relics", lambda: requests.get(f"{BASE}/api/geomap/relics", timeout=8).json()["items"][0]["name"])
check("costumes", lambda: requests.get(f"{BASE}/api/archive/costumes", timeout=8).json()["items"][0]["name"])
check("costume_chat", lambda: requests.post(f"{BASE}/api/archive/costume/7/chat", json={"question":"你穿在身上是什么感觉？"}, timeout=8).json()["reply"][:60])
check("simulate", lambda: requests.post(f"{BASE}/api/simulator/simulate", json={"era":"song","params":{"ritual":70,"craft":55,"climate":40,"aesthetic":60,"exchange":45}}, timeout=8).json()["narrative"][:60])
check("pattern_validate", lambda: requests.post(f"{BASE}/api/workshop/validate", json={"dynasty":"宋","params":{"len":80,"sleeve":70,"waist":40,"collar":50}}, timeout=8).json()["ok"])
check("news_parse", lambda: requests.post(f"{BASE}/api/home/news/parse", data={"title":"马王堆素纱单衣数字化","content":"湖南博物院以AI数字孪生复原西汉丝袍，展现马王堆丝织文物之美。"}, timeout=8).json()["entity_tags"])
check("heritage_profile", lambda: requests.get(f"{BASE}/api/heritage/profile", timeout=8).json().get("total_interactions", "guest"))
out.write("SMOKE DONE\n")
