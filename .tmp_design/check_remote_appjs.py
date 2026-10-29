"""只读核对：线上 accessories/app.js 与我改前的版本是否一致（确认没人直改过服务器产物），不做任何写入。"""
import difflib
import sys
from pathlib import Path

sys.path.insert(0, r'D:\yisu-ai-platform')
from cloud_deploy_tryon import Cloud  # noqa: E402

R = '/www/wwwroot/yisu/frontend/dist/accessories/app.js'
LOCAL_HEAD = Path(r'D:\yisu-ai-platform\frontend\public\accessories\app.js')
TMP = Path(r'D:\yisu-ai-platform\.tmp_design\audit\remote_app.js')
TMP.parent.mkdir(exist_ok=True)

cl = Cloud()
try:
    cl.sftp.get(R, str(TMP))
    code, out, err = cl.run(f"md5sum {R}; wc -c {R}; ls -l --time-style=+%F_%T {R}")
    print(out.strip())
finally:
    cl.close()

remote = TMP.read_text(encoding='utf-8').splitlines()
print('线上文件行数', len(remote))
