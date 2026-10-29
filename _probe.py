# -*- coding: utf-8 -*-
import io, sys, requests
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
KEY = "ark-e6f78632-05de-4a9a-931a-ea33cc8afa55-47a52"
URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
cands = ["doubao-seed-1.6-vision-250615","doubao-1.5-vision-pro-32k","doubao-vision-pro-32k","doubao-seed-1.6-vision"]
for m in cands:
    try:
        r = requests.post(URL, headers={"Authorization":f"Bearer {KEY}"},
            json={"model":m,"messages":[{"role":"user","content":[{"type":"text","text":"hi"}]}],"max_tokens":10}, timeout=30)
        print(m, "->", r.status_code, r.text[:120])
    except Exception as e:
        print(m, "ERR", e)
