# -*- coding: utf-8 -*-
"""细看动态页条目块结构 + 详情页配图"""
import urllib.request, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")

# 动态页条目块
html = get("https://www.dpm.org.cn/about/dynamic.html")
blocks = re.findall(r'<li[^>]*>.*?</li>', html, re.S)
print("LI_BLOCKS:", len(blocks))
for b in blocks[:3]:
    txt = re.sub(r"\s+", " ", b)[:260]
    print("---", txt)

# 详情页配图
det = get("https://www.dpm.org.cn/classify_detail/379636.html")
og = re.findall(r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)', det)
imgs = re.findall(r'<img[^>]+src="([^"]+)"', det)
print("OG_IMAGE:", og[:2])
print("IMGS:", [i for i in imgs if "static" not in i and "icon" not in i][:4])
# 正文
body = re.sub(r"<[^>]+>", "", det)
body = re.sub(r"\s+", " ", body)
i = body.find("故宫博物院")
print("BODY_AROUND:", body[i:i+400] if i >= 0 else body[:400])
