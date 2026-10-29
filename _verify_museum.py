import paramiko
host="47.93.14.11"; user="root"; pw="Han050607@"
ssh=paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pw, timeout=30)
def run(cmd):
    stdin,stdout,stderr=ssh.exec_command(cmd, timeout=60)
    return stdout.read().decode('utf-8','ignore')+stderr.read().decode('utf-8','ignore')
M="/www/wwwroot/yisu/frontend/dist/museum"
print("=== 各文件含 华夏衣冠志 计数 ===")
print(run(f"grep -c '华夏衣冠志' {M}/assets/*.js 2>/dev/null"))
print("=== 旧馆名残留检查 ===")
print(run(f"grep -c '衣溯 · 华夏服饰数字博物馆' {M}/assets/*.js 2>/dev/null || echo NONE"))
print(run(f"grep -c '衣溯 · 服装面料馆\\|衣溯 · 纹样馆' {M}/assets/*.js 2>/dev/null || echo NONE"))
print("=== 馆名新文案确认 ===")
print(run(f"grep -o -E '华夏衣冠志 · 数字博物馆（通史常设展）' {M}/assets/exhibits-*.js 2>/dev/null | head -3"))
print(run(f"grep -o -E '华夏衣冠志 · 数字博物馆' {M}/assets/index-*.js 2>/dev/null | head -3"))
ssh.close()
