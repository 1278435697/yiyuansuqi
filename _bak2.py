import paramiko, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
cli = paramiko.SSHClient()
cli.set_missing_host_key_policy(paramiko.AutoAddPolicy())
cli.connect('47.93.14.11', port=22, username='root', password='Han050607@', timeout=25)
def run(c, t=60):
    i,o,e = cli.exec_command(c, timeout=t)
    return (o.read().decode('utf-8','replace') + e.read().decode('utf-8','replace')).strip()
out = []
for bak in ["museum_bak_20261020_110424", "museum_bak_20261019_213442"]:
    out.append("=== " + bak + " assets ===")
    out.append(run(f"ls /www/wwwroot/yisu/frontend/dist/{bak}/assets 2>&1"))
    out.append("--- index.html ---")
    out.append(run(f"grep -o 'src=\"[^\"]*\"' /www/wwwroot/yisu/frontend/dist/{bak}/index.html 2>&1"))
    out.append("--- 返回补丁 count ---")
    out.append(run(f"grep -c 'onClick:e=>' /www/wwwroot/yisu/frontend/dist/{bak}/assets/index-*.js 2>/dev/null"))
    out.append("--- 衣溯AI count ---")
    out.append(run(f"grep -c '衣溯AI' /www/wwwroot/yisu/frontend/dist/{bak}/assets/index-*.js 2>/dev/null"))
    out.append("--- 华夏衣冠志 count ---")
    out.append(run(f"grep -c '华夏衣冠志' /www/wwwroot/yisu/frontend/dist/{bak}/assets/index-*.js 2>/dev/null"))
cli.close()
open(r"D:\yisu-ai-platform\_bak2.txt","w",encoding="utf-8").write("\n".join(out))
