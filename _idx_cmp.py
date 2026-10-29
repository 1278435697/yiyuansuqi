import paramiko, hashlib, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
sftp = cli.open_sftp()
sftp.get("/www/wwwroot/yisu/frontend/dist/assets/index-DQgMLrqq.js", r"D:\yisu-ai-platform\_srv_index.js")
sftp.close()
cli.close()
h = hashlib.md5(open(r"D:\yisu-ai-platform\_srv_index.js","rb").read()).hexdigest()
loc = hashlib.md5(open(r"D:\yisu-ai-platform\frontend\dist\assets\index-DQgMLrqq.js","rb").read()).hexdigest()
out = ["srv_md5=" + h, "local_md5=" + loc, "match=" + str(h == loc)]
src = open(r"D:\yisu-ai-platform\_srv_index.js", encoding='utf-8', errors='replace').read()
out.append("srv_has_tryon_route=" + str("/tryon" in src))
out.append("srv_has_museum_tryon_nav=" + str("/museum/tryon" in src))
open(r"D:\yisu-ai-platform\_idx_cmp.txt","w",encoding="utf-8").write("\n".join(out))
