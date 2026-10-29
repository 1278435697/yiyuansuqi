"""从生产 access log 里挖博物馆这一段的请求与失败，只读。"""
import sys

sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

CMDS = [
    ('近 4000 行里的非 2xx/3xx', r"tail -4000 /www/wwwlogs/abc.com.log | awk '$9>=400{print $7, $9}' | sort | uniq -c | sort -rn | head -25"),
    ('museum 请求数', r"tail -4000 /www/wwwlogs/abc.com.log | grep -c museum"),
    ('最近 30 条 museum 请求', r"tail -4000 /www/wwwlogs/abc.com.log | grep museum | awk '{print $7, $9, $10}' | tail -30"),
    ('museum/assets/exhibits 目录实况', r"find /www/wwwroot/yisu/frontend/dist/museum/assets/exhibits -maxdepth 1 | head -15; find /www/wwwroot/yisu/frontend/dist/museum/assets -type f | wc -l"),
]

cl = Cloud()
try:
    for label, cmd in CMDS:
        code, out, err = cl.run(cmd, timeout=180)
        print('\n## ' + label)
        print(out.strip()[:2500] or '(空)')
        if err.strip():
            print('[stderr]', err.strip()[:300])
finally:
    cl.close()
