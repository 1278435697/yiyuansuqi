# -*- coding: utf-8 -*-
# 对比本地 backend 与云端 backend 差异（文件级：大小 + mtime 秒）
import paramiko, io, sys, os
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
LOCAL_ROOT = r"C:\Users\lenovo\Desktop\yisu-ai-platform\backend"
REMOTE_ROOT = "/www/wwwroot/yisu/backend"

def local_files():
    out = {}
    for base, dirs, files in os.walk(LOCAL_ROOT):
        if "__pycache__" in base or ".git" in base:
            continue
        for f in files:
            if not f.endswith(".py"):
                continue
            p = os.path.join(base, f)
            rel = os.path.relpath(p, LOCAL_ROOT).replace("\\", "/")
            out[rel] = os.path.getsize(p)
    return out

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def remote_files():
    out = {}
    def walk(path):
        sftp = cli.open_sftp()
        try:
            for ent in sftp.listdir_attr(path):
                name = ent.filename
                full = path + "/" + name
                if ent.st_mode and (ent.st_mode & 0o170000) == 0o040000:  # dir
                    if name in ("__pycache__", ".git", "venv", "591cde3d08cdc971dd6324b305e8aede_venv", "node_modules"):
                        continue
                    walk(full)
                elif name.endswith(".py"):
                    out[full[len(REMOTE_ROOT):].lstrip("/")] = (ent.st_size, ent.st_mtime)
        finally:
            sftp.close()
    walk(REMOTE_ROOT)
    return out

lf = local_files()
rf = remote_files()
only_local = sorted(set(lf) - set(rf))
only_remote = sorted(set(rf) - set(lf))
diff = sorted([k for k in set(lf) & set(rf) if lf[k] != rf[k][0]])
print("== 本地有、云端没有 ==")
for k in only_local: print("  +", k, lf[k])
print("== 云端有、本地没有 ==")
for k in only_remote: print("  -", k, rf[k])
print("== 两边都有但大小不同 ==")
for k in diff: print("  ~", k, lf[k], "vs", rf[k][0])
print(f"== 汇总：本地 {len(lf)} 个 / 云端 {len(rf)} 个 / 差异 {len(only_local)+len(only_remote)+len(diff)} ==")
cli.close()
print("=== DONE ===")
