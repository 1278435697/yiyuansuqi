import paramiko
host="47.93.14.11"; user="root"; pw="Han050607@"
ssh=paramiko.SSHClient(); ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(host, username=user, password=pw, timeout=30)
def run(cmd):
    stdin,stdout,stderr=ssh.exec_command(cmd, timeout=60)
    return stdout.read().decode('utf-8','ignore')+stderr.read().decode('utf-8','ignore')
M="/www/wwwroot/yisu/frontend/dist/museum"
print(run(f"cp -r {M} {M}_bak_20261018_brandfix && echo BACKUP_OK"))
# 1) 馆名/牌匾（无 AI）
print(run(f"sed -i 's/衣溯 · 华夏服饰数字博物馆/华夏衣冠志 · 数字博物馆/g' {M}/assets/*.js && echo SED1_OK"))
print(run(f"sed -i 's/衣溯 · 服装面料馆/华夏衣冠志 · 服装面料馆/g' {M}/assets/*.js && echo SED2_OK"))
print(run(f"sed -i 's/衣溯 · 纹样馆/华夏衣冠志 · 纹样馆/g' {M}/assets/*.js && echo SED3_OK"))
# 2) 衣溯AI -> 衣溯 · 华夏衣冠志（含「衣溯AI · 数字博物馆」「衣溯AI · 纹样资料库」「衣溯AI 主站文物影像库」）
print(run(f"sed -i 's/衣溯AI/衣溯 · 华夏衣冠志/g' {M}/assets/*.js && echo SED4_OK"))
# 3) 「返回衣溯 · 华夏衣冠志主站」读感不佳 -> 「返回主站」
print(run(f"sed -i 's/返回衣溯 · 华夏衣冠志主站/返回主站/g' {M}/assets/*.js && echo SED5_OK"))
# 4) index.html title + meta description
print(run(f"sed -i 's/衣溯AI · 华夏服饰溯源与复原平台｜博物馆展厅/衣溯 · 华夏衣冠志 · 数字博物馆展厅/g' {M}/index.html && echo SED6_OK"))
# 5) 校验残留
print("=== 残留衣溯AI ===")
print(run(f"grep -c '衣溯AI' {M}/assets/*.js {M}/index.html 2>/dev/null || true"))
print("=== 替换后抽样 ===")
print(run(f"grep -o -E '.{10}华夏衣冠志.{22}' {M}/assets/index-*.js 2>/dev/null | head -8"))
print(run(f"head -c 400 {M}/index.html"))
ssh.close()
