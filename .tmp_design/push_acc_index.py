# -*- coding: utf-8 -*-
"""只推 accessories/index.html：先拉回线上版逐行比对，差异必须只有 ?v= 那一行（否则停手）→ 备份 → 就位 → 复核。
命令行与输出零明文，凭据由仓库既有部署器就地解析。"""
import difflib
import hashlib
import io
import sys
import time
from pathlib import Path

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

REMOTE = '/www/wwwroot/yisu/frontend/dist/accessories/index.html'
LOCAL = Path(r'D:\yisu-ai-platform\frontend\public\accessories\index.html')
TMP = Path(r'D:\yisu-ai-platform\.tmp_design\audit\remote_acc_index.html')
ts = time.strftime('%Y%m%d_%H%M%S')


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def run(cl, cmd, timeout=120):
    code, out, err = cl.run(cmd, timeout=timeout)
    print(f'--- [{code}] {cmd[:110]}')
    if out.strip():
        print(out.strip()[-700:])
    if err.strip():
        print('[stderr]', err.strip()[:300])
    return out


cl = Cloud()
try:
    cl.sftp.get(REMOTE, str(TMP))
    print(run(cl, f'md5sum {REMOTE}; ls -l --time-style=+%F_%T {REMOTE}'))
    remote = TMP.read_text(encoding='utf-8').splitlines()
    local = LOCAL.read_text(encoding='utf-8').splitlines()
    diff = [l for l in difflib.unified_diff(remote, local, '线上', '本地', lineterm='', n=0)]
    changed = [l for l in diff if l[:1] in '+-' and not l.startswith(('+++', '---'))]
    print('差异行：')
    for l in changed:
        print('   ' + l.strip())
    if len(changed) != 2:
        print('线上与本地差异不止版本号这一处，停止，不覆盖。')
        sys.exit(1)
    print('校验通过：唯一差异就是 app.js 的 ?v= 版本号')
    run(cl, f'cp -a {REMOTE} {REMOTE}.bak.{ts} && ls -l {REMOTE}.bak.{ts}')
    cl.sftp.put(str(LOCAL), f'/tmp/acc_index.{ts}.html')
    print('本地 md5 =', md5(LOCAL))
    run(cl, f'cmp -s /tmp/acc_index.{ts}.html {REMOTE} || mv /tmp/acc_index.{ts}.html {REMOTE}; '
            f'rm -f /tmp/acc_index.{ts}.html; md5sum {REMOTE}; ls -l --time-style=+%F_%T {REMOTE}')
    after = run(cl, f'md5sum {REMOTE}').split()[0]
    print('就位复核：', 'OK' if after == md5(LOCAL) else f'BAD {after}')
    run(cl, f'chown --reference=/www/wwwroot/yisu/frontend/dist/index.html {REMOTE}; chmod 644 {REMOTE}')
finally:
    cl.close()
