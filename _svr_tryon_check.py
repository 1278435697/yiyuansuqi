import paramiko
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
out.append("=== index.html head ===")
out.append(run("head -c 600 /www/wwwroot/yisu/frontend/dist/index.html"))
out.append("=== tryon chunks on server ===")
out.append(run("ls /www/wwwroot/yisu/frontend/dist/assets | grep -i tryon"))
out.append("=== index chunk mtime/size ===")
out.append(run("ls -l --time-style=+%Y-%m-%d_%H:%M /www/wwwroot/yisu/frontend/dist/assets/index-*.js | head"))
cli.close()
open(r"D:\yisu-ai-platform\_svr_tryon.txt","w",encoding="utf-8").write("\n".join(out))
