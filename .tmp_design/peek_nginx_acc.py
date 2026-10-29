# -*- coding: utf-8 -*-
"""只读勘察线上 nginx 站点配置：/accessories 相关 location、html 缓存头在哪条规则里、与仓库副本差多少。不写任何东西。"""
import io
import sys

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

cl = Cloud()
try:
    for cmd in [
        "ls -l /www/server/panel/vhost/nginx/ 2>/dev/null | head",
        "grep -rn 'accessories' /www/server/panel/vhost/nginx/ | head -20",
        "grep -rn 'Cache-Control' /www/server/panel/vhost/nginx/ | head -20",
        "grep -n 'location' /www/server/panel/vhost/nginx/yisu.conf 2>/dev/null | head -40",
    ]:
        code, out, err = cl.run(cmd, timeout=60)
        print(f'--- [{code}] {cmd}')
        print(out.strip()[:1600] or '(无输出)')
        if err.strip():
            print('[stderr]', err.strip()[:200])
finally:
    cl.close()
