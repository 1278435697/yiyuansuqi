# -*- coding: utf-8 -*-
# 本轮上线：主站 bundle（可拖动悬浮球 + 设计优化 + 衣冠改名）+ 配饰静态子页
# 铁律：远端只增不删；同名文件内容变了要单独放行；index.html 原子换。
# 凭据从 deploy_dist.py 现场解析，绝不落到任何输出里。
import ast, hashlib, io, json, os, sys, time
import paramiko

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\yisu-ai-platform"
LOCAL = os.path.join(ROOT, "frontend", "dist")
REMOTE = "/www/wwwroot/yisu/frontend/dist"
SNAP = os.path.join(ROOT, ".tmp_design", "live_pre.json")
MODE = sys.argv[1] if len(sys.argv) > 1 else "snapshot"

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
    txt = run("cd %s && find . -type f -not -path './museum_bak_*' | sed 's|^\\./||' | xargs md5sum" % REMOTE)
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


if MODE == "snapshot":
    m = remote_md5()
    json.dump(m, open(SNAP, "w"))
    print("线上快照 %d 个文件" % len(m))
    from collections import Counter
    print("按顶层目录:", dict(Counter(top(k) for k in m)))
    print("index.html:", m.get("index.html"))
    print("accessories/index.html:", m.get("accessories/index.html"))
    print("museum 仍在:", sum(1 for k in m if k.startswith("museum/")))

elif MODE == "plan":
    pre = json.load(open(SNAP))
    now = remote_md5()
    print("=== 0. 线上自我一致性（快照以来有没有被动过）===")
    drift = {k for k in set(pre) | set(now) if pre.get(k) != now.get(k)}
    print("漂移文件:", len(drift), sorted(drift)[:10])
    if drift:
        print("线上在我快照之后变了，停止。")
        cli.close(); sys.exit(1)

    loc = local_md5()
    print("\n=== 1. 我的构建 vs 线上 ===")
    print("本地 %d 个，线上 %d 个" % (len(loc), len(now)))
    new_ones = sorted(f for f in loc if f not in now)
    changed = sorted(f for f in loc if f in now and loc[f] != now[f])
    same = [f for f in loc if f in now and loc[f] == now[f]]
    print("新增: %d  同名有变: %d  一致: %d" % (len(new_ones), len(changed), len(same)))
    print("新增按目录:", dict(__import__("collections").Counter(top(f) for f in new_ones)))
    print("有变清单:", changed)
    only_remote = [f for f in now if f not in loc]
    print("线上独有（本次一律不动不删）: %d，其中 museum/ %d" % (len(only_remote), sum(1 for f in only_remote if f.startswith("museum/"))))

    # 同名有变只允许 index.html（要换的入口）和 accessories/index.html（本轮改名），且线上必须等于我认得的基线
    BASE = {"index.html", "accessories/index.html"}
    bad = [f for f in changed if f not in BASE]
    print("\n=== 2. 同名有变的白名单校验 ===")
    print("白名单外的变更:", bad or "无")
    if bad:
        print("有我没预期的同名改动，停止。")
        cli.close(); sys.exit(2)
    acc = "accessories/index.html"
    print("线上 accessories/index.html =", now.get(acc), "（我上轮部署的那份 = 8b2ef4d26327bc2db31103e7a1afcfa0）")
    cli.close()

elif MODE == "apply":
    now = remote_md5()
    loc = local_md5()
    new_ones = sorted(f for f in loc if f not in now)
    changed = sorted(f for f in loc if f in now and loc[f] != now[f])
    BASE = {"index.html", "accessories/index.html"}
    if [f for f in changed if f not in BASE]:
        print("有白名单外的同名变更，停止。"); cli.close(); sys.exit(2)
    sftp = cli.open_sftp()

    print("=== 3. 上传新增（旧站照常服务）===")
    for f in new_ones:
        d = os.path.dirname("%s/%s" % (REMOTE, f))
        run("mkdir -p '%s'" % d)
        sftp.put(os.path.join(LOCAL, f), "%s/%s" % (REMOTE, f))
    print("上传新增 %d 个" % len(new_ones))

    print("\n=== 4. 上传同名有变（配饰页改名）===")
    for f in [x for x in changed if x != "index.html"]:
        sftp.put(os.path.join(LOCAL, f), "%s/%s" % (REMOTE, f))
        print("  覆盖", f)

    sftp.put(os.path.join(LOCAL, "index.html"), "%s/index.html.new" % REMOTE)

    print("\n=== 5. 上传后 md5 回读 ===")
    # 入口 index.html 这时还挂在 .new 上（下一步才原子切换），所以它单独校验
    check = [f for f in new_ones + changed if f != "index.html"]
    after = remote_md5()
    bad = [f for f in check if after.get(f) != loc[f]]
    if bad or after.get("index.html.new") != loc["index.html"]:
        print("校验失败，不切换:", bad[:10]); run("rm -f %s/index.html.new" % REMOTE)
        cli.close(); sys.exit(1)
    print("全部 %d 个文件 md5 一致" % (len(check) + 1))

    print("\n=== 6. 原子切 index.html ===")
    ts = time.strftime("%Y%m%d-%H%M%S")
    bk = "/tmp/yisu_index_bak_%s.html" % ts
    run("cp -a %s/index.html %s" % (REMOTE, bk))
    print(run("mv %s/index.html.new %s/index.html && echo SWAPPED" % (REMOTE, REMOTE)).strip())
    print("旧 index.html 备份:", bk)

    print("\n=== 7. 切换后核对 ===")
    fin = remote_md5()
    print("线上文件数: %d（切换前 %d，只增不减：%s）" % (len(fin), len(now), "OK" if len(fin) >= len(now) else "异常"))
    print("消失的文件:", [f for f in now if f not in fin][:10] or "无")
    print("museum 仍在:", sum(1 for f in fin if f.startswith("museum/")))
    entry = run("grep -o 'assets/index-[A-Za-z0-9_-]*\\.js' %s/index.html | head -1" % REMOTE).strip()
    print("入口 chunk:", entry, run("test -f %s/%s && echo 存在 || echo 缺失" % (REMOTE, entry)).strip())
    print("配饰页导航已是「衣冠」:", run("grep -c '衣冠</a>' %s/accessories/index.html" % REMOTE).strip())
    cli.close()
