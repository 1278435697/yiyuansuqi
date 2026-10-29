# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
dl = r"D:\yisu-ai-platform\_dl"
def patch(path, pairs):
    data = open(path, encoding='utf-8').read()
    for old, new in pairs:
        n = data.count(old)
        data = data.replace(old, new)
        print("  replace x%d: %r -> %r" % (n, old, new))
    open(path, "w", encoding="utf-8", newline="").write(data)

print("== index.html ==")
patch(rf"{dl}\index.html", [("衣溯AI · 华夏服饰溯源与复原平台", "衣溯 · 华夏衣冠志 · 数字博物馆")])
print("== exhibits ==")
patch(rf"{dl}\exhibits-Cb5qGZIp.js", [("衣溯AI 主站文物影像库", "衣溯 主站文物影像库"), ("衣溯AI主站文物影像库", "衣溯主站文物影像库")])
print("== manifest ==")
patch(rf"{dl}\assets.manifest.json", [("衣溯AI主站文物影像库", "衣溯主站文物影像库")])

cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
sftp = cli.open_sftp()
for f, r in [("index.html", "/www/wwwroot/yisu/frontend/dist/museum/index.html"),
             ("exhibits-Cb5qGZIp.js", "/www/wwwroot/yisu/frontend/dist/museum/assets/exhibits-Cb5qGZIp.js"),
             ("assets.manifest.json", "/www/wwwroot/yisu/frontend/dist/museum/assets/assets.manifest.json")]:
    sftp.put(rf"{dl}\{f}", r)
    print("UP", f)
sftp.close()
def run(c):
    i,o,e = cli.exec_command(c, timeout=60)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
out.append("residual_all=" + run("grep -rl '衣溯AI' /www/wwwroot/yisu/frontend/dist/museum 2>/dev/null | wc -l"))
out.append("title=" + run("grep -o '<title>[^<]*</title>' /www/wwwroot/yisu/frontend/dist/museum/index.html"))
cli.close()
open(r"D:\yisu-ai-platform\_title_fix.txt","w",encoding="utf-8").write("\n".join(out))
