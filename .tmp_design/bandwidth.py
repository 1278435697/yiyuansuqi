"""量一下子站展品图的总体积与并发下载吞吐：判断「卡在装配」到底是传输慢还是永久等待。只读。"""
import re
import time
import urllib.request
import concurrent.futures as cf

BASE = 'http://47.93.14.11/museum/'
t = open(r'D:\yisu-ai-platform\.tmp_design\museum_src\exhibits-Cb5qGZIp.js', encoding='utf-8', errors='replace').read()
urls = sorted(set(re.findall(r'src:"(assets/[^"]+)"', t)))
print('展品图', len(urls), '张')


def get(u):
    req = urllib.request.Request(BASE + u)
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=180) as r:
            data = r.read()
            return u, len(data), time.time() - t0, r.status
    except Exception as e:
        return u, 0, time.time() - t0, 'ERR ' + type(e).__name__


for workers in (1, 6):
    tot = 0
    el = []
    t0 = time.time()
    with cf.ThreadPoolExecutor(workers) as ex:
        for u, size, dt, st in ex.map(get, urls):
            tot += size
            el.append(dt)
    wall = time.time() - t0
    print(f'并发 {workers}: {tot/1048576:.1f} MB / {wall:.1f}s = {tot*8/wall/1e6:.2f} Mbps；单张最慢 {max(el):.1f}s；状态异常 {0}')
