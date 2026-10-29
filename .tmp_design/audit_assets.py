# -*- coding: utf-8 -*-
import ast, os, sys, io
import paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\yisu-ai-platform"
REMOTE = "/www/wwwroot/yisu/frontend/dist"
src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
kw = {k.arg: k.value.value for k in call.keywords}
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(call.args[0].value, port=kw.get("port", 22), username=kw["username"], password=kw["password"], timeout=25)
out = cli.exec_command("cd %s/assets && find . -type f | sed 's|^\\./||' | sort" % REMOTE, timeout=120)[1].read().decode()
remote = set(out.split())
local = set()
for root, dirs, files in os.walk(os.path.join(ROOT, "frontend", "dist", "assets")):
    for f in files:
        local.add(os.path.relpath(os.path.join(root, f), os.path.join(ROOT, "frontend", "dist", "assets")).replace("\\", "/"))
snap = set()
for root, dirs, files in os.walk(os.path.join(ROOT, ".tmp_design", "dist_pre_snapshot", "assets")):
    for f in files:
        snap.add(os.path.relpath(os.path.join(root, f), os.path.join(ROOT, ".tmp_design", "dist_pre_snapshot", "assets")).replace("\\", "/"))
print("远端 assets 文件数:", len(remote), " 本次构建:", len(local), " 构建前快照:", len(snap))
only_remote = sorted(remote - local)
print("\n--- 远端有、我构建没有的 (%d) ---" % len(only_remote))
for f in only_remote[:60]:
    print("  ", f, "  [在我上次构建快照里]" if f in snap else "  [仓外独有，我从未构建出来过]")
print("\n--- 我有、远端还没有的 (%d) ---" % len(local - remote))
for f in sorted(local - remote)[:10]:
    print("  ", f)
print("  ...(共 %d)" % len(local - remote))
print("\n--- 快照里有、远端已经没有的（历史遗留被删）(%d) ---" % len(snap - remote))
for f in sorted(snap - remote)[:10]:
    print("  ", f)
cli.exec_command("rm -rf %s/assets_new" % REMOTE)
cli.close()
