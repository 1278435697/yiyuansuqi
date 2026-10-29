# 只读取证：线上现有 chunk 里到底有没有那几笔「今天改的、但不是本轮的」内容
import ast, io, os, sys
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
print("线上 SplitReveal CSS 的 object-fit 取值:",
      run("grep -o 'object-fit:[a-z]*' %s/assets/SplitReveal-*.css | sort | uniq -c" % REMOTE) or "(无文件)")
print("线上 AiQaPage JS 是否含 code-ref:",
      run("grep -c 'code-ref' %s/assets/AiQaPage-*.js" % REMOTE) or "(无)")
print("线上 AiQaPage JS 是否含 src-row:",
      run("grep -c 'src-row' %s/assets/AiQaPage-*.js" % REMOTE) or "(无)")
print("线上 index CSS 是否已有 acc-card:",
      run("grep -c 'acc-card' %s/assets/index-*.css | tail -3" % REMOTE) or "(无)")
print("线上入口 index.html 引用的入口 JS:",
      run("grep -o 'assets/index-[A-Za-z0-9_-]*\.js' %s/index.html | head -1" % REMOTE))
cli.close()
