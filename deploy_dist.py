# -*- coding: utf-8 -*-
# 部署前端 dist 到云端：先清旧 assets 缓存文件，再全量上传
import paramiko, io, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

LOCAL = r"C:\Users\lenovo\Desktop\yisu-ai-platform\frontend\dist"
REMOTE = "/www/wwwroot/yisu/frontend/dist"

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=120):
    i,o,e = cli.exec_command(c, timeout=t)
    return o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')

# 1. 备份并清空远端 assets + index.html（防止旧 hash 文件残留导致缓存假象）
print(run("mkdir -p /tmp/dist_old_$(date +%%s) && cp -r %s/* /tmp/dist_old_$(date +%%s)/ 2>/dev/null; rm -rf %s/assets %s/index.html && mkdir -p %s/assets" % (REMOTE, REMOTE, REMOTE, REMOTE)).strip() or "(clean ok)")

sftp = cli.open_sftp()
n = 0
for root, dirs, files in os.walk(LOCAL):
    rel = os.path.relpath(root, LOCAL)
    rdir = REMOTE if rel == "." else REMOTE + "/" + rel.replace("\\", "/")
    try:
        sftp.stat(rdir)
    except IOError:
        run("mkdir -p " + rdir)
    for f in files:
        lp = os.path.join(root, f)
        rp = rdir + "/" + f
        sftp.put(lp, rp)
        n += 1
sftp.close()
print("上传文件数:", n)
print(run("ls %s/assets | head -20" % REMOTE))
cli.close()
print("=== DONE ===")
