"""把 3D 博物馆子站的入口与主 chunk 拉到本地读逻辑（子站源码不在仓库里，只能从线上取）。只读生产。"""
import sys

sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

R = '/www/wwwroot/yisu/frontend/dist/museum'
OUT = r'D:\yisu-ai-platform\.tmp_design\museum_src'
import os
os.makedirs(OUT, exist_ok=True)

cl = Cloud()
try:
    code, out, _ = cl.run(f'ls -1 {R}/assets/*.js {R}/assets/*.json {R}/index.html', timeout=120, echo=False)
    files = [l.strip() for l in out.splitlines() if l.strip()]
    for f in files:
        rel = f.split('/assets/')[-1] if '/assets/' in f else 'index.html'
        cl.sftp.get(f, os.path.join(OUT, rel))
    cl.run(f'ls -l {R}/assets/exhibits/tang | head -12', timeout=120)
    cl.run(f"find {R}/assets/exhibits -type f | awk -F. '{{print $NF}}' | sort | uniq -c", timeout=120)
    cl.run(f"du -sh {R}/assets/exhibits; find {R}/assets/exhibits -type f | wc -l", timeout=120)
finally:
    cl.close()
print('saved:', sorted(os.listdir(OUT)))
