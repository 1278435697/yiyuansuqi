"""上线 /api/accessories：备份 → 传两个文件 → 语法自检 → 重启 → 冒烟。凭据复用既有部署器，不落副本。"""
import sys
import time

sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

R = '/www/wwwroot/yisu'
VENV_PY = f'{R}/backend/591cde3d08cdc971dd6324b305e8aede_venv/bin/python3'
LOCAL = r'D:\yisu-ai-platform\backend\app'
ts = time.strftime('%Y%m%d_%H%M%S')


def step(cl, cmd, timeout=180):
    code, out, err = cl.run(cmd, timeout=timeout)
    print(f'--- [{code}] {cmd[:120]}')
    if out.strip():
        print(out.strip()[-1200:])
    if err.strip():
        print('[stderr]', err.strip()[-800:])
    return code, out, err


cl = Cloud()
try:
    # 1. 前置检查：数据文件到位、venv 可用
    step(cl, f"ls -l {R}/frontend/dist/accessories/accessories.json; {VENV_PY} -V")

    # 2. 备份线上 main.py（accessories.py 线上原本不存在，无需备份）
    step(cl, f"cp {R}/backend/app/main.py {R}/backend/app/main.py.bak.{ts} && ls -l {R}/backend/app/main.py.bak.{ts}")

    # 3. 先传 accessories.py，再传 main.py：顺序反了会有一段 import 失败窗口
    cl.sftp.put(LOCAL + r'\api\accessories.py', f'{R}/backend/app/api/accessories.py')
    print('uploaded accessories.py')
    step(cl, f"{VENV_PY} -m py_compile {R}/backend/app/api/accessories.py && echo COMPILE_OK")

    cl.sftp.put(LOCAL + r'\main.py', f'{R}/backend/app/main.py')
    print('uploaded main.py')
    step(cl, f"{VENV_PY} -m py_compile {R}/backend/app/main.py && echo COMPILE_OK; "
             f"md5sum {R}/backend/app/main.py")

    # 4. 重启
    step(cl, 'systemctl restart yisu-backend.service; sleep 6; systemctl is-active yisu-backend.service')

    # 5. 冒烟：新接口 + 既有接口
    for path in ('/api/accessories/categories',
                 '/api/accessories?category=%E5%A4%B4%E9%A5%B0&limit=2',
                 '/api/accessories/头饰-02',
                 '/api/home/stats'):
        step(cl, f"curl -s -o /tmp/acc_probe -w '%{{http_code}} %{{size_download}}B' "
                 f"http://127.0.0.1:8765{path}; head -c 260 /tmp/acc_probe; echo")

    step(cl, 'journalctl -u yisu-backend.service -n 15 --no-pager | tail -15')
finally:
    cl.close()
