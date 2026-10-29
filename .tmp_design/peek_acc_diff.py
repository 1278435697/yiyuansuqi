# 只读取证：把线上 accessories 四个文件拉下来，与本地 dist 逐行比对，不写任何东西
import ast, hashlib, io, os, sys, difflib
import paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\yisu-ai-platform"
LOCAL = os.path.join(ROOT, "frontend", "dist", "accessories")
REMOTE_DIR = "/www/wwwroot/yisu/frontend/dist/accessories"
FILES = ["index.html", "styles.css", "app.js", "data.js"]
src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
kw = {k.arg: k.value.value for k in call.keywords}
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(call.args[0].value, port=kw.get("port",22), username=kw["username"], password=kw["password"], timeout=25)
sftp = cli.open_sftp()
tmp = os.path.join(ROOT, ".tmp_design", "acc_remote_now"); os.makedirs(tmp, exist_ok=True)
for f in FILES:
    rp = os.path.join(tmp, f)
    sftp.get("%s/%s" % (REMOTE_DIR, f), rp)
    a = io.open(rp, encoding="utf-8", errors="replace").read().splitlines()
    lp = os.path.join(LOCAL, f)
    b = io.open(lp, encoding="utf-8", errors="replace").read().splitlines()
    d = [l for l in difflib.unified_diff(a, b, "线上", "本地", lineterm="") if l.startswith(("+","-")) and not l.startswith(("+++","---"))]
    print("== %-14s 线上 %d 行 / 本地 %d 行 / 差异 %d 行  md5 %s vs %s" % (
        f, len(a), len(b), len(d), hashlib.md5(open(rp,'rb').read()).hexdigest()[:8],
        hashlib.md5(open(lp,'rb').read()).hexdigest()[:8]))
    for l in d[:8]: print("    ", l[:200])
    if len(d) > 8: print("     … 其余 %d 行" % (len(d)-8))
st = cli.exec_command("ls -l --time-style=+'%%Y-%%m-%%d %%H:%%M' %s" % REMOTE_DIR)[1].read().decode()
print("\n== 线上文件时间戳 ==\n" + st)
sftp.close(); cli.close()
