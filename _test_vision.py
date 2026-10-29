# -*- coding: utf-8 -*-
import io, sys, requests, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
# 用一张汉服公开图测试视觉识别
img_url = "https://aka.doubaocdn.com/s/I4w4kIlLZt"
r = requests.get(img_url, timeout=30)
b64 = base64.b64encode(r.content).decode()
data_url = f"data:image/png;base64,{b64}"
resp = requests.post("http://47.93.14.11/api/aiqa/chat",
                     json={"question": "这是什么服饰？", "history": [], "image_base64": data_url},
                     timeout=90)
print("HTTP", resp.status_code)
j = resp.json()
print("image_note:", j.get("image_note","")[:200])
print("answer:", (j.get("answer","") or "")[:300])
