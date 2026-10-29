# -*- coding: utf-8 -*-
import io, sys, paramiko
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
remote = "/www/wwwroot/yisu/frontend/dist/museum/assets"
dl = r"D:\yisu-ai-platform\_dl"
sftp = cli.open_sftp()
for f in ["index-BqJJw04H.js", "MuseumView-aROHavN7.js"]:
    run(f"cp {remote}/{f} /tmp/{f}.bak_brandfix")
    sftp.put(rf"{dl}\{f}", f"{remote}/{f}")
    print("UP_OK", f)
sftp.close()
out = []
out.append("brand1=" + run(f"grep -c '衣溯 · 华夏衣冠志 · 数字博物馆' {remote}/index-BqJJw04H.js"))
out.append("oldbrand_index=" + run(f"grep -c '衣溯AI' {remote}/index-BqJJw04H.js"))
out.append("oldbrand_view=" + run(f"grep -c '衣溯AI' {remote}/MuseumView-aROHavN7.js"))
out.append("back_logic=" + run(f"grep -c 'history.go' {remote}/index-BqJJw04H.js"))
cli.close()
open(r"D:\yisu-ai-platform\_up_mus3.txt","w",encoding="utf-8").write("\n".join(out))
