# -*- coding: utf-8 -*-
# 本轮（档案/面料/纹样三页换衣冠皮）合并式上线。
# 铁律：远端只增不删；museum/ 与一切线上独有文件不碰；index.html 原子换并先备份。
# 凭据从仓库既有部署器 deploy_dist.py 现场解析，命令行与输出零明文。
# 用法：python push_accskin.py snapshot|plan|apply
import ast, hashlib, io, json, os, sys, time
from collections import Counter

import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\yisu-ai-platform"
LOCAL = os.path.join(ROOT, "frontend", "dist")
REMOTE = "/www/wwwroot/yisu/frontend/dist"
SNAP = os.path.join(ROOT, ".tmp_design", "live_pre_accskin.json")
MODE = sys.argv[1] if len(sys.argv) > 1 else "snapshot"

# 同名但内容变化的文件白名单：本轮只换了三个视图 + 一层皮 + 四个组件，
# 因此只允许入口 index.html 变化。其余同名变更一律视为意外，停下来看。
BASE = {"index.html"}
# 本轮范围外：accessories/ 四文件线上仍是 cover 版，本地带着第二轮 contain 修复，
# 那是单独待授权的一笔，不跟这次构建一起推。
EXCLUDE = ("accessories/",)


def keep(f):
    return not f.startswith(EXCLUDE)

src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
kw = {k.arg: k.value.value for k in call.keywords}
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(call.args[0].value, port=kw.get("port", 22), username=kw["username"],
            password=kw["password"], timeout=kw.get("timeout", 25))


def run(cmd, t=300):
    return cli.exec_command(cmd, timeout=t)[1].read().decode("utf-8", "replace")


def remote_md5():
    out = {}
    txt = run("cd %s && find . -type f | sed 's|^\\./||' | xargs -d '\\n' md5sum" % REMOTE)
    for l in txt.splitlines():
        if l.strip():
            h, f = l.split(None, 1)
            out[f.strip()] = h
    return out


def local_md5():
    out = {}
    for root, dirs, files in os.walk(LOCAL):
        for f in files:
            p = os.path.join(root, f)
            rel = os.path.relpath(p, LOCAL).replace("\\", "/")
            out[rel] = hashlib.md5(open(p, "rb").read()).hexdigest()
    return out


def top(rel):
    return rel.split("/")[0] if "/" in rel else "(根)"


def diff_summary(loc, now):
    keys_loc = [f for f in loc if keep(f)]
    keys_now = [f for f in now if keep(f)]
    new_ones = sorted(f for f in keys_loc if f not in now)
    changed = sorted(f for f in keys_loc if f in now and loc[f] != now[f])
    same = [f for f in keys_loc if f in now and loc[f] == now[f]]
    only_remote = sorted(f for f in keys_now if f not in loc)
    skipped = sorted(f for f in loc if not keep(f) and f in now and loc[f] != now[f])
    return new_ones, changed, same, only_remote, skipped


if MODE == "snapshot":
    m = remote_md5()
    json.dump(m, open(SNAP, "w"))
    print("线上快照 %d 个文件" % len(m))
    print("按顶层目录:", dict(Counter(top(k) for k in m)))
    print("index.html:", m.get("index.html"))
    print("museum/ 文件数:", sum(1 for k in m if k.startswith("museum/")))
    print("accessories/ 文件数:", sum(1 for k in m if k.startswith("accessories/")))

elif MODE == "plan":
    pre = json.load(open(SNAP))
    now = remote_md5()
    print("=== 0. 线上自我一致性（快照以来有没有被动过）===")
    drift = {k for k in set(pre) | set(now) if pre.get(k) != now.get(k)}
    print("漂移文件:", len(drift), sorted(drift)[:10])
    if drift:
        print("线上在快照之后变了，停止。")
        cli.close(); sys.exit(1)

    loc = local_md5()
    new_ones, changed, same, only_remote, skipped = diff_summary(loc, now)
    print("\n=== 1. 本地构建 vs 线上（已排除范围外目录 %s）===" % ", ".join(EXCLUDE))
    print("本地 %d 个，线上 %d 个" % (len(loc), len(now)))
    print("新增: %d  同名有变: %d  完全一致: %d" % (len(new_ones), len(changed), len(same)))
    print("新增按目录:", dict(Counter(top(f) for f in new_ones)))
    print("线上独有（本次一律不动不删）: %d，其中 museum/ %d" % (
        len(only_remote), sum(1 for f in only_remote if f.startswith("museum/"))))
    print("\n=== 1b. 范围外但内容不同 —— 本轮刻意不推 ===")
    for f in skipped:
        print("  跳过", f)

    print("\n=== 2. 同名有变清单（必须逐个认得）===")
    for f in changed:
        print("  ", f, "白名单内" if f in BASE else "!! 白名单外")
    bad = [f for f in changed if f not in BASE]
    if bad:
        print("有没预期的同名改动，停止。")
        cli.close(); sys.exit(2)

    print("\n=== 3. 新增文件按类型 ===")
    js = [f for f in new_ones if f.endswith(".js")]
    css = [f for f in new_ones if f.endswith(".css")]
    other = [f for f in new_ones if not f.endswith((".js", ".css"))]
    print("js %d / css %d / 其它 %d" % (len(js), len(css), len(other)))
    print("本轮三页相关的新 chunk:")
    for f in new_ones:
        if any(k in os.path.basename(f) for k in ("CostumeArchive", "FabricArchive", "PatternLibrary", "accMeta", "AccCard")):
            print("  +", f)
    print("非 assets/ 的新增（应为空）:", [f for f in other if not f.startswith("assets/")] or "无")

elif MODE == "apply":
    now = remote_md5()
    loc = local_md5()
    new_ones, changed, same, only_remote, skipped = diff_summary(loc, now)
    if [f for f in changed if f not in BASE]:
        print("有白名单外的同名变更，停止。"); cli.close(); sys.exit(2)
    sftp = cli.open_sftp()

    print("=== 4. 上传新增 %d 个（旧站照常服务，不删任何东西）===" % len(new_ones))
    for f in new_ones:
        d = os.path.dirname("%s/%s" % (REMOTE, f))
        run("mkdir -p '%s'" % d)
        sftp.put(os.path.join(LOCAL, f), "%s/%s" % (REMOTE, f))
    print("完成")

    print("\n=== 5. 同名有变（除入口）===")
    for f in [x for x in changed if x != "index.html"]:
        sftp.put(os.path.join(LOCAL, f), "%s/%s" % (REMOTE, f))
        print("  覆盖", f)
    sftp.put(os.path.join(LOCAL, "index.html"), "%s/index.html.new" % REMOTE)

    print("\n=== 6. 上传后 md5 回读 ===")
    check = [f for f in new_ones + changed if f != "index.html"]
    after = remote_md5()
    bad = [f for f in check if after.get(f) != loc[f]]
    if bad or after.get("index.html.new") != loc["index.html"]:
        print("校验失败，不切换:", bad[:10])
        run("rm -f %s/index.html.new" % REMOTE)
        cli.close(); sys.exit(1)
    print("全部 %d 个文件 md5 一致" % (len(check) + 1))

    print("\n=== 7. 原子切 index.html ===")
    ts = time.strftime("%Y%m%d-%H%M%S")
    bk = "/tmp/yisu_index_bak_%s.html" % ts
    run("cp -a %s/index.html %s" % (REMOTE, bk))
    print(run("mv %s/index.html.new %s/index.html && echo SWAPPED" % (REMOTE, REMOTE)).strip())
    print("旧 index.html 备份:", bk)

    print("\n=== 8. 切换后核对（只增不减）===")
    fin = remote_md5()
    print("线上文件数: %d（切换前 %d）→ %s" % (len(fin), len(now), "OK 只增不减" if len(fin) >= len(now) else "异常 变少了"))
    gone = [f for f in now if f not in fin]
    print("消失的文件:", gone[:10] or "无")
    print("museum/ 仍在:", sum(1 for f in fin if f.startswith("museum/")), "（切换前",
          sum(1 for f in now if f.startswith("museum/")), "）")
    print("accessories/ 仍在:", sum(1 for f in fin if f.startswith("accessories/")), "（切换前",
          sum(1 for f in now if f.startswith("accessories/")), "）")
    entry = run("grep -o 'assets/index-[A-Za-z0-9_-]*\\.js' %s/index.html | head -1" % REMOTE).strip()
    print("入口 chunk:", entry, run("test -f %s/%s && echo 存在 || echo 缺失" % (REMOTE, entry)).strip())
    print("入口 CSS:", run("grep -o 'assets/index-[A-Za-z0-9_-]*\\.css' %s/index.html | head -1" % REMOTE).strip())
    cli.close()
