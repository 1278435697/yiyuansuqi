"""把子站 chunk 里所有 assets/ 引用逐个 HEAD，找出 404 —— 这是「装配展品」卡死的最可能触发点。"""
import re
import concurrent.futures as cf
import urllib.request

BASE = 'http://47.93.14.11/museum/'
SRC = r'D:\yisu-ai-platform\.tmp_design\museum_src'

urls = set()
for fn in ('exhibits-Cb5qGZIp.js', 'MuseumView-aROHavN7.js'):
    t = open(SRC + '\\' + fn, encoding='utf-8', errors='replace').read()
    for s in re.findall(r'src:"(assets/[^"]+)"', t):
        urls.add(s)
urls = sorted(urls)
print('待核对资源', len(urls))


def chk(u):
    req = urllib.request.Request(BASE + u, method='HEAD')
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return u, r.status
    except urllib.error.HTTPError as e:
        return u, e.code
    except Exception as e:
        return u, 'ERR ' + type(e).__name__


bad = []
with cf.ThreadPoolExecutor(12) as ex:
    for u, st in ex.map(chk, urls):
        if st != 200:
            bad.append((u, st))
print('非 200 数量:', len(bad))
for b in bad:
    print('  ', b[1], b[0])
