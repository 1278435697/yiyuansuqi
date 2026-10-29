import ast, io, os, sys, re
import paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
ROOT = r"D:\yisu-ai-platform"
REMOTE = "/www/wwwroot/yisu/frontend/dist"
src = open(os.path.join(ROOT, "deploy_dist.py"), encoding="utf-8").read()
line = next(l for l in src.splitlines() if l.startswith("cli.connect("))
call = ast.parse(line.strip(), mode="eval").body
kw = {k.arg: k.value.value for k in call.keywords}
cli = paramiko.SSHClient(); cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect(call.args[0].value, port=kw.get("port",22), username=kw["username"], password=kw["password"], timeout=25)
def run(c, t=120):
    return cli.exec_command(c, timeout=t)[1].read().decode("utf-8","replace").strip()
entry = run("grep -o 'assets/index-[A-Za-z0-9_-]*\.js' %s/index.html | head -1" % REMOTE)
print("入口 JS:", entry)
for name in ["AiQaPage", "SplitReveal", "NewsDetail", "CostumeArchive", "FabricArchive", "PatternLibrary"]:
    hit = run("grep -o '%s-[A-Za-z0-9_-]*\.js' %s/%s | sort -u | head -3" % (name, REMOTE, entry))
    print("  入口里引用 %s ->" % name, hit or "(未直接引用，可能在其它 chunk)")
css = run("grep -o 'assets/index-[A-Za-z0-9_-]*\.css' %s/index.html | head -1" % REMOTE)
print("入口 CSS:", css, "含 acc-card:", run("grep -c 'acc-card' %s/%s" % (REMOTE, css)))
sr = run("grep -o 'SplitReveal-[A-Za-z0-9_-]*\.css' %s/%s | sort -u | head -2" % (REMOTE, entry))
print("SplitReveal CSS 引用:", sr or "(在 chunk 内动态引用)")
cli.close()
