# -*- coding: utf-8 -*-
import re, io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
dl = r"D:\yisu-ai-platform\_dl"
for f in ["index-BqJJw04H.js", "MuseumView-aROHavN7.js"]:
    data = open(rf"{dl}\{f}", encoding="utf-8").read()
    hits = [m.start() for m in re.finditer(r'衣溯[^ \u3001，。]*AI|AI[^ \u3001，。]*衣溯', data)]
    print(f, "residual AI-brand hits:", len(hits), hits[:5])
    # 确认返回逻辑仍在
    print("  back-logic:", "history.go" in data, "| brand-ok:", "衣溯 · 华夏衣冠志 · 数字博物馆" in data if "index" in f else "衣溯AI" not in data)
