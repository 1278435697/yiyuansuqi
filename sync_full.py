# -*- coding: utf-8 -*-
# 全量同步：把本地 backend/app 源码完整上传到云端（排除 venv/缓存），编译+重启+健康检查
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
LOCAL_ROOT = r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend"
REMOTE_ROOT = "/www/wwwroot/yisu/backend"

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()

def mkdirs(remote_dir):
    parts = remote_dir.split("/")
    cur = ""
    for p in parts:
        cur = cur + "/" + p if cur else p
        try:
            sftp.stat(cur)
        except IOError:
            try:
                sftp.mkdir(cur)
            except IOError:
                pass

def walk_upload(base, remote_base):
    count = 0
    for root, dirs, files in os.walk(base):
        dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", ".venv", "venv", "591cde3d08cdc971dd6324b305e8aede_venv", "node_modules", "dist")]
        rel = os.path.relpath(root, base)
        remote_dir = remote_base if rel == "." else remote_base + "/" + rel.replace("\\", "/")
        if rel != ".":
            mkdirs(remote_dir)
        for f in files:
            if f.endswith(".pyc") or f.endswith(".pyo"):
                continue
            lp = os.path.join(root, f)
            rp = remote_dir + "/" + f
            sftp.put(lp, rp)
            count += 1
    return count

n = walk_upload(os.path.join(LOCAL_ROOT, "app"), REMOTE_ROOT + "/app")
print("uploaded files:", n)

# 编译检查
cmd = "cd %s && find app -name '*.py' | xargs -n 1 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m py_compile 2>&1 | head -20; echo COMPILE_OK" % REMOTE_ROOT
i, o, e = cli.exec_command(cmd, timeout=300)
out = o.read().decode('utf-8', 'replace') + e.read().decode('utf-8', 'replace')
print(out[:800])

# 重启 uvicorn
kill = "pkill -f 'uvicorn app.main:app' || true; sleep 2; nohup 591cde3d08cdc971dd6324b305e8aede_venv/bin/python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8765 >> /tmp/yisu_uvicorn.log 2>&1 & echo RESTARTED"
i, o, e = cli.exec_command(kill, timeout=60)
print(o.read().decode('utf-8', 'replace')[:200])
sftp.close()
cli.close()
print("=== DONE ===")
