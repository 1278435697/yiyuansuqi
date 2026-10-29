# -*- coding: utf-8 -*-
# 上线主站 bundle —— 纯增量，不删远端任何文件。
# 只上传「新 chunk」和「同名但内容变了」的文件，最后原子换 index.html。
import ast, hashlib, io, os, sys, time
import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\yisu-ai-platform"
LOCAL = os.path.join(ROOT, "frontend", "dist")
REMOTE = "/www/wwwroot/yisu/frontend/dist"

src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
kw = {k.arg: k.value.value for k in call.keywords}

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(call.args[0].value, port=kw.get("port", 22), username=kw["username"],
            password=kw["password"], timeout=kw.get("timeout", 25))


def run(cmd, t=180):
    return cli.exec_command(cmd, timeout=t)[1].read().decode("utf-8", "replace").strip()


def walk(base):
    out = {}
    for root, dirs, files in os.walk(base):
        for f in files:
            rel = os.path.relpath(os.path.join(root, f), base).replace("\\", "/")
            out[rel] = hashlib.md5(open(os.path.join(root, f), "rb").read()).hexdigest()
    return out


print("=== 1. 现场核对（线上必须还是我构建前那份）===")
top_before = run("ls -1 %s" % REMOTE).split("\n")
r_idx = run("md5sum %s/index.html | cut -d' ' -f1" % REMOTE)
s_idx = hashlib.md5(open(os.path.join(ROOT, ".tmp_design", "dist_pre_snapshot", "index.html"), "rb").read()).hexdigest()
print("线上 index.html == 我构建前快照:", "yes" if r_idx == s_idx else "NO")
if r_idx != s_idx:
    print("线上不是我以为的那份，停止。")
    cli.close(); sys.exit(1)

print("\n=== 2. 逐文件比对远端 assets ===")
local = walk(os.path.join(LOCAL, "assets"))
remote_md5 = {}
for line_ in run("cd %s/assets && find . -type f | sed 's|^\\./||' | xargs md5sum" % REMOTE, t=300).split("\n"):
    if line_.strip():
        h, f = line_.split(None, 1)
        remote_md5[f] = h
print("本地 %d 个，远端 %d 个" % (len(local), len(remote_md5)))
new_ones = [f for f in local if f not in remote_md5]
changed = [f for f in local if f in remote_md5 and local[f] != remote_md5[f]]
untouched = [f for f in local if f in remote_md5 and local[f] == remote_md5[f]]
print("远端没有、需要新增: %d" % len(new_ones))
print("同名但内容变了、需要覆盖: %d  %s" % (len(changed), changed))
print("完全一致、跳过: %d" % len(untouched))
print("远端独有、本次不动也不删: %d" % len([f for f in remote_md5 if f not in local]))

if changed:
    print("\n有同名文件内容变了，会即时影响线上正在跑的页面 —— 先停，等你确认。")
    cli.close(); sys.exit(2)

print("\n=== 3. 上传新增 chunk（旧站照常服务）===")
sftp = cli.open_sftp()
for f in new_ones:
    sftp.put(os.path.join(LOCAL, "assets", f), "%s/assets/%s" % (REMOTE, f))
print("上传完成 %d 个" % len(new_ones))
sftp.put(os.path.join(LOCAL, "index.html"), "%s/index.html.new" % REMOTE)

print("\n=== 4. 校验上传结果 ===")
bad = [f for f in new_ones if run("md5sum %s/assets/%s | cut -d' ' -f1" % (REMOTE, f)) != local[f]]
want_idx = hashlib.md5(open(os.path.join(LOCAL, "index.html"), "rb").read()).hexdigest()
if bad or run("md5sum %s/index.html.new | cut -d' ' -f1" % REMOTE) != want_idx:
    print("校验失败，未切换:", bad)
    run("rm -f %s/index.html.new" % REMOTE)
    cli.close(); sys.exit(1)
print("新增 chunk 与 index.html.new md5 全部一致")

print("\n=== 5. 原子切 index.html ===")
ts = time.strftime("%Y%m%d-%H%M%S")
bk = "/tmp/yisu_index_bak_%s.html" % ts
print(run("cp -a %s/index.html %s && mv %s/index.html.new %s/index.html && echo SWAPPED" % (REMOTE, bk, REMOTE, REMOTE)))
print("旧 index.html 备份:", bk)

print("\n=== 6. 切换后核对 ===")
top_after = run("ls -1 %s" % REMOTE).split("\n")
print("顶层集合变化:", set(top_after) ^ set(top_before) or "无")
print("assets 文件数:", run("find %s/assets -type f | wc -l" % REMOTE), "(切换前 %d)" % len(remote_md5))
entry = run("grep -o 'assets/index-[A-Za-z0-9_-]*\\.js' %s/index.html | head -1" % REMOTE)
print("入口 chunk:", entry, run("test -f %s/%s && echo 存在 || echo 缺失" % (REMOTE, entry)))
print("新逻辑已在线上:", run("grep -c 'yisu-preloader-seen' %s/%s" % (REMOTE, entry)))

print("\n=== 7. 引用完整性：本次构建产出的每个文件是否都在服务器上 ===")
listing = run("cd %s/assets && find . -type f | sed 's|^\\./||'" % REMOTE, t=120).split("\n")
have = set(x.strip() for x in listing if x.strip())
missing = [f for f in local if f not in have]
print("本次构建 %d 个产物，服务器缺失 %d 个 %s" % (len(local), len(missing), missing))
cli.close()
