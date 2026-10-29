import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
out.append("=== curl TryonLayout head ===")
out.append(run("curl -s -o /dev/null -w 'code=%{http_code} size=%{size_download} time=%{time_total}s\\n' http://127.0.0.1/assets/TryonLayout-CVaHsjse.js"))
out.append("=== curl tryon shared ===")
out.append(run("curl -s -o /dev/null -w 'code=%{http_code} size=%{size_download} time=%{time_total}s\\n' http://127.0.0.1/assets/tryon-BuL_vdNA.js"))
out.append("=== TryonLayout content head ===")
out.append(run("head -c 500 /www/wwwroot/yisu/frontend/dist/assets/TryonLayout-CVaHsjse.js"))
out.append("=== tryon shared content head ===")
out.append(run("head -c 500 /www/wwwroot/yisu/frontend/dist/assets/tryon-BuL_vdNA.js"))
cli.close()
open(r"D:\yisu-ai-platform\_chunk_check.txt","w",encoding="utf-8").write("\n".join(out))
