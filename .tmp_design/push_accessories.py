# -*- coding: utf-8 -*-
# 只推 accessories 子站的 index.html + styles.css：不构建、不碰 dist 其他任何文件。
# 凭据不写在这里，运行时从 deploy_dist.py 里解析出来。
import ast, hashlib, os, re, sys, time, io
import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\yisu-ai-platform"
LOCAL_DIR = os.path.join(ROOT, "frontend", "public", "accessories")
BAK_DIR = os.path.join(ROOT, ".tmp_design", "acc_baseline")
REMOTE_DIR = "/www/wwwroot/yisu/frontend/dist/accessories"
FILES = ["index.html", "styles.css"]

src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
host = call.args[0].value
kw = {k.arg: k.value.value for k in call.keywords}

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(host, port=kw.get("port", 22), username=kw["username"],
            password=kw["password"], timeout=kw.get("timeout", 25))

def run(cmd, t=120):
    return cli.exec_command(cmd, timeout=t)[1].read().decode("utf-8", "replace").strip()

print("REMOTE_DIR:", REMOTE_DIR)
print(run("ls -l %s | head -20" % REMOTE_DIR))

print("--- 前置校验：远端必须和我留的基线一致 ---")
ok = True
for f in FILES:
    remote_md5 = run("md5sum %s/%s 2>/dev/null | cut -d' ' -f1" % (REMOTE_DIR, f))
    base_md5 = md5(os.path.join(BAK_DIR, f))
    print("%-12s remote=%s baseline=%s %s" % (f, remote_md5, base_md5, "OK" if remote_md5 == base_md5 else "MISMATCH"))
    if remote_md5 != base_md5:
        ok = False
if not ok:
    print("远端和我留的基线不一致（可能有我不知道的改动）。已停止，不上传。")
    cli.close()
    sys.exit(1)

stamp = time.strftime("%Y%m%d-%H%M%S")
bk = "/tmp/acc_bak_%s" % stamp
print(run("mkdir -p %s && cp -a %s/index.html %s/styles.css %s/ && ls -l %s" % (bk, REMOTE_DIR, REMOTE_DIR, bk, bk)))

sftp = cli.open_sftp()
for f in FILES:
    sftp.put(os.path.join(LOCAL_DIR, f), "%s/%s" % (REMOTE_DIR, f))
    print("uploaded", f)
sftp.close()

print("--- 上传后校验 ---")
for f in FILES:
    remote_md5 = run("md5sum %s/%s | cut -d' ' -f1" % (REMOTE_DIR, f))
    want = md5(os.path.join(LOCAL_DIR, f))
    print("%-12s remote=%s local=%s %s" % (f, remote_md5, want, "OK" if remote_md5 == want else "BAD"))
print(run("ls -l %s" % REMOTE_DIR))
print("backup at", bk)
cli.close()
