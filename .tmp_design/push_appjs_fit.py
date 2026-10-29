# -*- coding: utf-8 -*-
"""只推 accessories/app.js 一个文件：前置 md5 必须等于我逐行比对过的那份 → cp -a 备份 → 临时文件 + 同目录 mv 就位 → 复核。
凭据从仓库既有部署器就地解析，命令行与输出零明文。"""
import hashlib
import io
import os
import sys
import time

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

REMOTE = '/www/wwwroot/yisu/frontend/dist/accessories/app.js'
LOCAL = r'D:\yisu-ai-platform\frontend\public\accessories\app.js'
# 刚才只读拉回来逐行比对过的那份线上文件的指纹，对不上就说明线上又被人动过，立即停手
EXPECTED_REMOTE = 'cd3a9c5152077f829ef1d4b0eef2354b'
ts = time.strftime('%Y%m%d_%H%M%S')


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def run(cl, cmd, timeout=120):
    code, out, err = cl.run(cmd, timeout=timeout)
    print(f'--- [{code}] {cmd[:110]}')
    if out.strip():
        print(out.strip()[-800:])
    if err.strip():
        print('[stderr]', err.strip()[:400])
    return out


want_local = md5(LOCAL)
print('本地 app.js md5 =', want_local)
cl = Cloud()
try:
    now = run(cl, f'md5sum {REMOTE}').split()[0]
    if now != EXPECTED_REMOTE:
        print(f'线上已变化（{now} != {EXPECTED_REMOTE}），停止，不覆盖。')
        sys.exit(1)
    print('前置校验通过：线上仍是我比对过的那份（只差我要改的那一行）')
    run(cl, f'cp -a {REMOTE} {REMOTE}.bak.{ts} && ls -l {REMOTE}.bak.{ts}')
    cl.sftp.put(LOCAL, f'/tmp/app.js.{ts}')
    run(cl, f'md5sum /tmp/app.js.{ts}')
    run(cl, f'cmp -s /tmp/app.js.{ts} {REMOTE} || mv /tmp/app.js.{ts} {REMOTE}; '
            f'rm -f /tmp/app.js.{ts}; ls -l --time-style=+%F_%T {REMOTE}; md5sum {REMOTE}')
    after = run(cl, f'md5sum {REMOTE}').split()[0]
    print('就位复核：', 'OK' if after == want_local else f'BAD {after}')
    run(cl, 'chown --reference=/www/wwwroot/yisu/frontend/dist/index.html '
            f'{REMOTE}; chmod 644 {REMOTE}; ls -l {REMOTE}')
finally:
    cl.close()
