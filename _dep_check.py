import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
out.append("=== assets 是否存在 app-IltAN4UR.js ===")
out.append(run("ls -l /www/wwwroot/yisu/frontend/dist/assets/app-IltAN4UR.js 2>&1"))
out.append("=== 服务器公网 curl app chunk ===")
out.append(run("curl -s -o /dev/null -w 'code=%{http_code}\\n' http://47.93.14.11/assets/app-IltAN4UR.js"))
out.append("=== 服务器公网 curl TryonLayout ===")
out.append(run("curl -s -o /dev/null -w 'code=%{http_code}\\n' http://47.93.14.11/assets/TryonLayout-CVaHsjse.js"))
out.append("=== nginx 主站 root/location ===")
out.append(run("grep -n -E 'root|location|alias' /www/server/panel/vhost/nginx/yisu.conf | head -30"))
cli.close()
open(r"D:\yisu-ai-platform\_dep_check.txt","w",encoding="utf-8").write("\n".join(out))
