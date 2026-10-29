# -*- coding: utf-8 -*-
import io, sys, requests, base64
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
KEY = "ark-e6f78632-05de-4a9a-931a-ea33cc8afa55-47a52"
URL = "https://ark.cn-beijing.volces.com/api/v3/chat/completions"
# 一张很小的测试图（1x1 红点 png）
small = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\nIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\r\n-\xb4\x00\x00\x00\x00IEND\xaeB`\x82').decode()
r = requests.post(URL, headers={"Authorization":f"Bearer {KEY}"},
  json={"model":"doubao-seed-character-260628",
        "messages":[{"role":"user","content":[
          {"type":"text","text":"这张图是什么颜色？"},
          {"type":"image_url","image_url":{"url":f"data:image/png;base64,{small}"}}]}],
        "max_tokens":50}, timeout=60)
print(r.status_code, r.text[:400])
