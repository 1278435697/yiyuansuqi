# -*- coding: utf-8 -*-
# 本轮（图片一律不裁切）衣冠子站四个文件的合并式推送：先拉远端逐行 diff 给你看，
# 确认只有我改的行才上传；备份在 /tmp；不重启、不碰 dist 其他任何文件。
import ast, hashlib, io, os, sys, time, difflib
import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\yisu-ai-platform"
LOCAL = os.path.join(ROOT, "frontend", "public", "accessories")
REMOTE_DIR = "/www/wwwroot/yisu/frontend/dist/accessories"
FILES = ["index.html", "styles.css", "app.js", "data.js"]

src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
host = call.args[0].value
kw = {k.arg: k.value.value for k in call.keywords}


def md5p(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()


cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(host, port=kw.get("port", 22), username=kw["username"],
            password=kw["password"], timeout=kw.get("timeout", 25))


def run(cmd, t=180):
    return cli.exec_command(cmd, timeout=t)[1].read().decode("utf-8", "replace").strip()


tmp = os.path.join(ROOT, ".tmp_design", "remote_now")
os.makedirs(tmp, exist_ok=True)
sftp = cli.open_sftp()

print("=== 1) 拉取远端当前四个文件，与本地逐行比对 ===")
plan = []
for f in FILES:
    rp = os.path.join(tmp, f)
    sftp.get("%s/%s" % (REMOTE_DIR, f), rp)
    a = io.open(rp, encoding="utf-8", errors="replace").read().splitlines()
    b = io.open(os.path.join(LOCAL, f), encoding="utf-8", errors="replace").read().splitlines()
    diff = [l for l in difflib.unified_diff(a, b, lineterm="") if l.startswith(("+", "-")) and not l.startswith(("+++", "---"))]
    same = md5p(rp) == md5p(os.path.join(LOCAL, f))
    print("%-12s 远端md5=%s 本地md5=%s %s 差异行=%d" % (f, md5p(rp)[:8], md5p(os.path.join(LOCAL, f))[:8], "一致(跳过)" if same else "将上传", len(diff)))
    for l in diff[:12]:
        print("     " + l[:160])
    if len(diff) > 12:
        print("     … 其余 %d 行（data.js 是 29 处 cover→contain）" % (len(diff) - 12))
    if not same:
        plan.append(f)

if not plan:
    print("远端已与本地一致，无需上传。")
    sftp.close(); cli.close(); sys.exit(0)

stamp = time.strftime("%Y%m%d_%H%M%S")
bk = "/tmp/acc_bak_%s" % stamp
print("\n=== 2) 备份远端 %s ===" % bk)
print(run("mkdir -p %s && cp -a %s && ls -l %s" % (bk, " ".join("%s/%s" % (REMOTE_DIR, f) for f in plan), bk)))

print("\n=== 3) 上传 ===")
for f in plan:
    tmp_remote = "/tmp/acc_new_%s_%s" % (stamp, f)
    sftp.put(os.path.join(LOCAL, f), tmp_remote)
    chk = run("cmp -s %s %s && echo SAME || echo DIFF" % (tmp_remote, "%s/%s" % (REMOTE_DIR, f)))
    print("%-12s 上传前与远端比较=%s" % (f, chk))
    print("%-12s mv=%s" % (f, run("mv %s %s/%s && echo OK" % (tmp_remote, REMOTE_DIR, f))))

print("\n=== 4) 校验 + 属主权限对齐 ===")
for f in plan:
    want = md5p(os.path.join(LOCAL, f))
    got = run("md5sum %s/%s | cut -d' ' -f1" % (REMOTE_DIR, f))
    print("%-12s remote=%s local=%s %s" % (f, got[:12], want[:12], "OK" if got == want else "BAD"))
print(run("chown --reference=%s/index.html %s && chmod 644 %s && ls -l %s" % (
    REMOTE_DIR, " ".join("%s/%s" % (REMOTE_DIR, f) for f in plan),
    " ".join("%s/%s" % (REMOTE_DIR, f) for f in plan), REMOTE_DIR)))
sftp.close()
print("\n备份在", bk)
cli.close()
