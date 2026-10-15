# -*- coding: utf-8 -*-
import urllib.request, re, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=15).read().decode("utf-8", "replace")

html = get("https://www.chinasilkmuseum.com/cs/list_164.aspx")
print("LEN:", len(html))
print("HAS_ITEMID:", "itemid" in html)
print("HAS_INFO:", "info_164" in html)
i = html.find("丝连古今")
print("CTX:", re.sub(r"\s+", " ", html[max(0,i-300):i+300]) if i>=0 else "not found")
# 找所有 aspx 链接
links = sorted(set(re.findall(r'href="([^"]*aspx[^"]*)"', html)))
print("LINKS:", links[:15])
