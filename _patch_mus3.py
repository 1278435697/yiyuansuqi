# -*- coding: utf-8 -*-
import io, sys, os, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

def patch(path, pairs, bak):
    raw = open(path, "rb").read()
    with open(bak, "wb") as f: f.write(raw)
    data = raw.decode("utf-8")
    for old, new in pairs:
        n = data.count(old)
        data = data.replace(old, new)
        print(f"  replace x{n}: {old!r} -> {new!r}")
    open(path, "w", encoding="utf-8", newline="").write(data)
    print("  bytes:", len(raw), "->", len(data.encode("utf-8")))
    return data

dl = r"D:\yisu-ai-platform\_dl"
print("== index-BqJJw04H.js ==")
patch(rf"{dl}\index-BqJJw04H.js", [
    ("衣溯AI · 数字博物馆", "衣溯 · 华夏衣冠志 · 数字博物馆"),
    ("返回衣溯AI主站", "返回衣溯 · 华夏衣冠志主站"),
], rf"{dl}\index-BqJJw04H.js.bak")
print("== MuseumView-aROHavN7.js ==")
patch(rf"{dl}\MuseumView-aROHavN7.js", [
    ("衣溯AI", "衣溯"),
], rf"{dl}\MuseumView-aROHavN7.js.bak")
